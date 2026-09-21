"""Relational persistence and UI projections for sacramental preparation."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch

from sakramenti.models import FormationCandidate, FormationProgramYear
from pastoral.models import Parish
from django_multitenant.schema import with_tenant_schema


COLLECTION_BY_PROGRAM_TYPE = {
    FormationProgramYear.ProgramType.FIRST_COMMUNION: 'firstCommunion',
    FormationProgramYear.ProgramType.CONFIRMATION: 'confirmations',
}


def _date_as_text(calendar_date: date | None) -> str:
    return calendar_date.isoformat() if calendar_date else ''


def _parse_optional_date(raw_value, field_label: str) -> date | None:
    if not raw_value:
        return None
    if isinstance(raw_value, date):
        return raw_value
    try:
        return date.fromisoformat(str(raw_value))
    except (TypeError, ValueError) as error:
        raise ValidationError({field_label: 'Unesite ispravan datum.'}) from error


def _parse_amount(raw_value) -> Decimal:
    try:
        return Decimal(str(raw_value or 0))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValidationError({'groupFee': 'Unesite ispravan iznos.'}) from error


def _candidate_name_parts(candidate_record: dict) -> tuple[str, str, str]:
    given_names = str(candidate_record.get('firstName') or '').strip()
    surname = str(candidate_record.get('lastName') or '').strip()
    historical_name = str(candidate_record.get('name') or '').strip()
    if not historical_name:
        historical_name = f'{given_names} {surname}'.strip()
    if not given_names and not surname:
        name_parts = historical_name.split()
        if len(name_parts) > 1:
            given_names = ' '.join(name_parts[:-1])
            surname = name_parts[-1]
        else:
            given_names = historical_name
    return historical_name, given_names, surname


def _program_year_as_dictionary(program_year: FormationProgramYear) -> dict:
    projected_group = {
        'id': program_year.public_identifier,
        'year': program_year.year,
        'ceremonyDate': _date_as_text(program_year.ceremony_date),
        'groupFee': float(program_year.contribution_amount),
        'groupFeePaid': program_year.contribution_paid,
        'candidates': [],
    }
    if program_year.contribution_paid_at:
        projected_group['groupFeePaidAt'] = _date_as_text(
            program_year.contribution_paid_at
        )

    if program_year.program_type == FormationProgramYear.ProgramType.FIRST_COMMUNION:
        projected_group.update({
            'groupName': program_year.group_name,
            'celebrant': program_year.celebrant_name,
        })
    else:
        projected_group['bishop'] = program_year.celebrant_name

    for candidate in program_year.candidates.all():
        sacramental_event = candidate.sacramental_event
        register_entry = (
            getattr(sacramental_event, 'register_entry', None)
            if sacramental_event
            else None
        )
        if program_year.program_type == FormationProgramYear.ProgramType.FIRST_COMMUNION:
            projected_candidate = {
                'id': candidate.public_identifier,
                'firstName': candidate.given_names,
                'lastName': candidate.surname,
                'name': candidate.historical_name,
                'birthDate': _date_as_text(candidate.birth_date),
                'school': candidate.school_name,
                'class': candidate.school_class,
                'parents': candidate.parents_name,
                'baptized': _date_as_text(candidate.baptism_date),
                'status': candidate.operational_status,
                'paid': candidate.contribution_paid,
                'registryNo': (
                    register_entry.entry_reference if register_entry else ''
                ),
            }
        else:
            projected_candidate = {
                'id': candidate.public_identifier,
                'name': candidate.historical_name,
                'birthDate': _date_as_text(candidate.birth_date),
                'school': candidate.school_name,
                'class': candidate.school_class,
                'group': candidate.group_name,
                'baptized': _date_as_text(candidate.baptism_date),
                'sponsor': candidate.sponsor_name,
                'status': candidate.operational_status,
                'oib': '',
                'registryNo': (
                    register_entry.entry_reference if register_entry else ''
                ),
            }
        projected_group['candidates'].append(projected_candidate)
    return projected_group


@with_tenant_schema
def relational_formation_programs_as_dictionaries(parish: Parish) -> dict[str, list[dict]]:
    """Return the stable dictionary contract expected by existing screens."""
    projected_collections = {
        collection_name: []
        for collection_name in COLLECTION_BY_PROGRAM_TYPE.values()
    }
    candidate_queryset = FormationCandidate.objects.select_related(
        'sacramental_event__register_entry'
    )
    program_years = FormationProgramYear.objects.filter(parish=parish).prefetch_related(
        Prefetch('candidates', queryset=candidate_queryset)
    )
    for program_year in program_years:
        collection_name = COLLECTION_BY_PROGRAM_TYPE[program_year.program_type]
        projected_collections[collection_name].append(
            _program_year_as_dictionary(program_year)
        )
    return projected_collections


@with_tenant_schema
def _synchronize_candidate(
    program_year: FormationProgramYear,
    candidate_record: dict,
) -> FormationCandidate:
    public_identifier = str(candidate_record.get('id') or '').strip()
    if not public_identifier:
        raise ValidationError('Kandidat nema stabilni identifikator.')
    if str(candidate_record.get('oib') or '').strip():
        raise ValidationError(
            'OIB se ne sprema uz evidenciju priprave. Povežite kandidata s provjerenom osobom.'
        )

    historical_name, given_names, surname = _candidate_name_parts(candidate_record)
    if not historical_name:
        raise ValidationError('Kandidat mora imati ime i prezime.')

    candidate, _ = FormationCandidate.objects.update_or_create(
        program_year=program_year,
        public_identifier=public_identifier,
        defaults={
            'historical_name': historical_name,
            'given_names': given_names,
            'surname': surname,
            'birth_date': _parse_optional_date(
                candidate_record.get('birthDate'), 'birthDate'
            ),
            'school_name': str(candidate_record.get('school') or '').strip(),
            'school_class': str(candidate_record.get('class') or '').strip(),
            'group_name': str(candidate_record.get('group') or '').strip(),
            'parents_name': str(candidate_record.get('parents') or '').strip(),
            'sponsor_name': str(candidate_record.get('sponsor') or '').strip(),
            'baptism_date': _parse_optional_date(
                candidate_record.get('baptized'), 'baptized'
            ),
            'operational_status': str(
                candidate_record.get('status') or 'upis'
            ).strip(),
            'contribution_paid': bool(candidate_record.get('paid', False)),
        },
    )
    return candidate


@transaction.atomic
@with_tenant_schema
def reconcile_formation_programs(parish: Parish, parish_data: dict) -> None:
    """Make relational preparation records match the current UI representation."""
    retained_program_year_ids = []
    for program_type, collection_name in COLLECTION_BY_PROGRAM_TYPE.items():
        seen_years = set()
        for group_record in list(parish_data.get(collection_name) or []):
            program_year_number = int(group_record.get('year'))
            if program_year_number in seen_years:
                raise ValidationError(
                    f'Godina {program_year_number} unesena je više puta.'
                )
            seen_years.add(program_year_number)

            public_identifier = str(group_record.get('id') or '').strip()
            if not public_identifier:
                raise ValidationError('Godina priprave nema stabilni identifikator.')

            program_year, _ = FormationProgramYear.objects.update_or_create(
                parish=parish,
                program_type=program_type,
                year=program_year_number,
                defaults={
                    'public_identifier': public_identifier,
                    'group_name': str(group_record.get('groupName') or '').strip(),
                    'ceremony_date': _parse_optional_date(
                        group_record.get('ceremonyDate'), 'ceremonyDate'
                    ),
                    'celebrant_name': str(
                        group_record.get('celebrant')
                        or group_record.get('bishop')
                        or ''
                    ).strip(),
                    'contribution_amount': _parse_amount(
                        group_record.get('groupFee')
                    ),
                    'contribution_paid': bool(
                        group_record.get('groupFeePaid', False)
                    ),
                    'contribution_paid_at': _parse_optional_date(
                        group_record.get('groupFeePaidAt'), 'groupFeePaidAt'
                    ),
                },
            )
            retained_program_year_ids.append(program_year.id)

            retained_candidate_ids = []
            for candidate_record in list(group_record.get('candidates') or []):
                candidate = _synchronize_candidate(program_year, candidate_record)
                retained_candidate_ids.append(candidate.id)
            program_year.candidates.exclude(id__in=retained_candidate_ids).delete()

    removed_program_years = FormationProgramYear.objects.filter(parish=parish).exclude(
        id__in=retained_program_year_ids
    )
    FormationCandidate.objects.filter(program_year__in=removed_program_years).delete()
    removed_program_years.delete()
