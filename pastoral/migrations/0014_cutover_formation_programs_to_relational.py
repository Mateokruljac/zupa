from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import migrations


FORMATION_COLLECTIONS = (
    ('firstCommunion', 'first_communion'),
    ('confirmations', 'confirmation'),
)


def parse_optional_date(raw_value, *, parish_slug, field_name):
    if not raw_value:
        return None
    try:
        return date.fromisoformat(str(raw_value))
    except (TypeError, ValueError) as error:
        raise RuntimeError(
            f'Župa {parish_slug}: neispravan datum u polju {field_name}: {raw_value!r}.'
        ) from error


def parse_amount(raw_value, *, parish_slug):
    try:
        return Decimal(str(raw_value or 0))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise RuntimeError(
            f'Župa {parish_slug}: neispravan iznos priprave: {raw_value!r}.'
        ) from error


def candidate_names(candidate):
    given_names = str(candidate.get('firstName') or '').strip()
    surname = str(candidate.get('lastName') or '').strip()
    historical_name = str(candidate.get('name') or '').strip()
    if not historical_name:
        historical_name = f'{given_names} {surname}'.strip()
    return historical_name, given_names, surname


def validate_source_identifiers(parish, collection_name, program_groups):
    group_identifiers = [
        str(program_group.get('id') or '').strip()
        for program_group in program_groups
    ]
    if any(not identifier for identifier in group_identifiers):
        raise RuntimeError(
            f'Župa {parish.slug}: {collection_name} sadrži godinu bez stabilnog identifikatora.'
        )
    if len(group_identifiers) != len(set(group_identifiers)):
        raise RuntimeError(
            f'Župa {parish.slug}: {collection_name} sadrži ponovljene identifikatore godina.'
        )

    seen_years = set()
    for program_group in program_groups:
        program_year = int(program_group.get('year'))
        if program_year in seen_years:
            raise RuntimeError(
                f'Župa {parish.slug}: {collection_name} sadrži godinu {program_year} više puta.'
            )
        seen_years.add(program_year)

        candidates = list(program_group.get('candidates') or [])
        candidate_identifiers = [
            str(candidate.get('id') or '').strip()
            for candidate in candidates
        ]
        if any(not identifier for identifier in candidate_identifiers):
            raise RuntimeError(
                f'Župa {parish.slug}: godina {program_year} sadrži kandidata bez stabilnog identifikatora.'
            )
        if len(candidate_identifiers) != len(set(candidate_identifiers)):
            raise RuntimeError(
                f'Župa {parish.slug}: godina {program_year} sadrži ponovljene identifikatore kandidata.'
            )


def create_candidate(FormationCandidate, program_year, candidate, parish_slug):
    if str(candidate.get('oib') or '').strip():
        raise RuntimeError(
            f'Župa {parish_slug}: kandidat {candidate.get("id")} sadrži OIB. '
            'Migracija je zaustavljena kako se OIB ne bi prenio u nezaštićeno polje.'
        )

    historical_name, given_names, surname = candidate_names(candidate)
    if not historical_name:
        raise RuntimeError(
            f'Župa {parish_slug}: kandidat {candidate.get("id")} nema ime i prezime.'
        )

    FormationCandidate.objects.create(
        public_identifier=str(candidate['id']).strip(),
        program_year=program_year,
        historical_name=historical_name,
        given_names=given_names,
        surname=surname,
        birth_date=parse_optional_date(
            candidate.get('birthDate'),
            parish_slug=parish_slug,
            field_name='birthDate',
        ),
        school_name=str(candidate.get('school') or '').strip(),
        school_class=str(candidate.get('class') or '').strip(),
        group_name=str(candidate.get('group') or '').strip(),
        parents_name=str(candidate.get('parents') or '').strip(),
        sponsor_name=str(candidate.get('sponsor') or '').strip(),
        baptism_date=parse_optional_date(
            candidate.get('baptized'),
            parish_slug=parish_slug,
            field_name='baptized',
        ),
        operational_status=str(candidate.get('status') or 'upis').strip(),
        contribution_paid=bool(candidate.get('paid', False)),
    )


def cutover_formation_programs(apps, schema_editor):
    Parish = apps.get_model('pastoral', 'Parish')
    FormationProgramYear = apps.get_model('pastoral', 'FormationProgramYear')
    FormationCandidate = apps.get_model('pastoral', 'FormationCandidate')

    for parish in Parish.objects.all():
        parish_data = dict(parish.data or {})

        for collection_name, program_type in FORMATION_COLLECTIONS:
            program_groups = list(parish_data.get(collection_name) or [])
            validate_source_identifiers(parish, collection_name, program_groups)

            expected_candidate_count = 0
            for program_group in program_groups:
                candidates = list(program_group.get('candidates') or [])
                expected_candidate_count += len(candidates)
                program_year = FormationProgramYear.objects.create(
                    parish=parish,
                    program_type=program_type,
                    public_identifier=str(program_group['id']).strip(),
                    year=int(program_group['year']),
                    group_name=str(program_group.get('groupName') or '').strip(),
                    ceremony_date=parse_optional_date(
                        program_group.get('ceremonyDate'),
                        parish_slug=parish.slug,
                        field_name='ceremonyDate',
                    ),
                    celebrant_name=str(
                        program_group.get('celebrant')
                        or program_group.get('bishop')
                        or ''
                    ).strip(),
                    contribution_amount=parse_amount(
                        program_group.get('groupFee'),
                        parish_slug=parish.slug,
                    ),
                    contribution_paid=bool(program_group.get('groupFeePaid', False)),
                    contribution_paid_at=parse_optional_date(
                        program_group.get('groupFeePaidAt'),
                        parish_slug=parish.slug,
                        field_name='groupFeePaidAt',
                    ),
                )
                for candidate in candidates:
                    create_candidate(
                        FormationCandidate,
                        program_year,
                        candidate,
                        parish.slug,
                    )

            migrated_groups = FormationProgramYear.objects.filter(
                parish=parish,
                program_type=program_type,
            )
            migrated_candidate_count = FormationCandidate.objects.filter(
                program_year__in=migrated_groups,
            ).count()
            if migrated_groups.count() != len(program_groups):
                raise RuntimeError(
                    f'Župa {parish.slug}: broj migriranih godina za {collection_name} nije jednak izvornom broju.'
                )
            if migrated_candidate_count != expected_candidate_count:
                raise RuntimeError(
                    f'Župa {parish.slug}: broj migriranih kandidata za {collection_name} nije jednak izvornom broju.'
                )

            parish_data.pop(collection_name, None)

        parish.data = parish_data
        parish.save(update_fields=('data',))


class Migration(migrations.Migration):

    dependencies = [
        ('pastoral', '0013_formationcandidate_given_names_and_more'),
    ]

    operations = [
        migrations.RunPython(
            cutover_formation_programs,
            migrations.RunPython.noop,
        ),
    ]
