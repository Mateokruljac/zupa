"""Relational persistence and stable UI projection for marriages."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from sakramenti.models import (
    EventParticipant,
    MarriageDetails,
    SacramentalEvent,
)
from django_multitenant.schema import with_tenant_schema
from sakramenti.services.family_card_sacraments import exclude_family_card_events
from pastoral.models import Parish


def _date_as_text(calendar_date: date | None) -> str:
    return calendar_date.isoformat() if calendar_date else ''


def _parse_optional_date(raw_value) -> date | None:
    if not raw_value:
        return None
    if isinstance(raw_value, date):
        return raw_value
    try:
        return date.fromisoformat(str(raw_value))
    except (TypeError, ValueError) as error:
        raise ValidationError({'weddingDate': 'Unesite ispravan datum.'}) from error


def _parse_amount(raw_value) -> Decimal:
    try:
        return Decimal(str(raw_value or 0))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValidationError({'stipend': 'Unesite ispravan iznos.'}) from error


def _names_from_record(wedding_record: dict) -> tuple[str, str]:
    groom_name = str(wedding_record.get('groomName') or '').strip()
    bride_name = str(wedding_record.get('brideName') or '').strip()
    if groom_name or bride_name:
        return groom_name, bride_name
    couple_name = str(wedding_record.get('couple') or '').strip()
    separated_names = couple_name.split(' & ', 1)
    if len(separated_names) == 2:
        return separated_names[0].strip(), separated_names[1].strip()
    return '', ''


def _split_name(value) -> tuple[str, str]:
    parts = str(value or '').strip().split()
    if len(parts) > 1:
        return ' '.join(parts[:-1]), parts[-1]
    return (parts[0], '') if parts else ('', '')


def _witness_names(marriage_details: MarriageDetails) -> tuple[str, str]:
    groom_witness_name = marriage_details.groom_witness_name
    bride_witness_name = marriage_details.bride_witness_name
    if groom_witness_name or bride_witness_name:
        return groom_witness_name, bride_witness_name
    separated_names = marriage_details.witnesses_name.split(',', 1)
    return (
        separated_names[0].strip() if separated_names else '',
        separated_names[1].strip() if len(separated_names) == 2 else '',
    )


@with_tenant_schema
def relational_weddings_as_dictionaries(parish: Parish) -> list[dict]:
    wedding_events = exclude_family_card_events(
        SacramentalEvent.objects.filter(
            parish=parish,
            event_type=SacramentalEvent.EventType.MARRIAGE,
            marriage_details__isnull=False,
        )
        .exclude(status=SacramentalEvent.Status.CANCELLED)
        .select_related('marriage_details', 'register_entry')
        .prefetch_related('participants')
    )
    wedding_records = []
    for wedding_event in wedding_events:
        marriage_details = wedding_event.marriage_details
        register_entry = getattr(wedding_event, 'register_entry', None)
        spouses = [
            participant.historical_name
            for participant in wedding_event.participants.all()
            if participant.role == EventParticipant.Role.SPOUSE
        ]
        groom_name = spouses[0] if spouses else ''
        bride_name = spouses[1] if len(spouses) > 1 else ''
        if marriage_details.groom_first_name or marriage_details.groom_last_name:
            groom_name = ' '.join(filter(None, (marriage_details.groom_first_name, marriage_details.groom_last_name)))
        if marriage_details.bride_first_name or marriage_details.bride_last_name:
            bride_name = ' '.join(filter(None, (marriage_details.bride_first_name, marriage_details.bride_last_name)))
        groom_witness_name, bride_witness_name = _witness_names(marriage_details)
        wedding_records.append({
            'id': wedding_event.public_identifier,
            'entryNumber': register_entry.entry_number if register_entry else marriage_details.entry_number,
            'physicalPage': marriage_details.physical_page or '',
            'groomName': groom_name,
            'brideName': bride_name,
            'groomFirstName': marriage_details.groom_first_name,
            'groomLastName': marriage_details.groom_last_name,
            'groomBirthPlace': marriage_details.groom_birth_place,
            'groomBirthDate': _date_as_text(marriage_details.groom_birth_date),
            'groomOib': marriage_details.groom_oib or '',
            'groomReligion': marriage_details.groom_religion,
            'groomBaptismDate': _date_as_text(marriage_details.groom_baptism_date),
            'groomBaptismParish': marriage_details.groom_baptism_parish,
            'groomBaptismParishAddress': marriage_details.groom_baptism_parish_address,
            'groomResidenceAddress': marriage_details.groom_residence_address,
            'brideFirstName': marriage_details.bride_first_name,
            'brideLastName': marriage_details.bride_last_name,
            'brideBirthPlace': marriage_details.bride_birth_place,
            'brideBirthDate': _date_as_text(marriage_details.bride_birth_date),
            'brideOib': marriage_details.bride_oib or '',
            'brideReligion': marriage_details.bride_religion,
            'brideBaptismDate': _date_as_text(marriage_details.bride_baptism_date),
            'brideBaptismParish': marriage_details.bride_baptism_parish,
            'brideBaptismParishAddress': marriage_details.bride_baptism_parish_address,
            'brideResidenceAddress': marriage_details.bride_residence_address,
            'groomFatherFirstName': marriage_details.groom_father_first_name,
            'groomFatherLastName': marriage_details.groom_father_last_name,
            'groomMotherFirstName': marriage_details.groom_mother_first_name,
            'groomMotherMaidenName': marriage_details.groom_mother_maiden_name,
            'brideFatherFirstName': marriage_details.bride_father_first_name,
            'brideFatherLastName': marriage_details.bride_father_last_name,
            'brideMotherFirstName': marriage_details.bride_mother_first_name,
            'brideMotherMaidenName': marriage_details.bride_mother_maiden_name,
            'groomWitnessFirstName': marriage_details.groom_witness_first_name,
            'groomWitnessLastName': marriage_details.groom_witness_last_name,
            'brideWitnessFirstName': marriage_details.bride_witness_first_name,
            'brideWitnessLastName': marriage_details.bride_witness_last_name,
            'officiantFirstName': marriage_details.officiant_first_name,
            'officiantLastName': marriage_details.officiant_last_name,
            'officiantRole': marriage_details.officiant_role,
            'notes': marriage_details.notes or '',
            'couple': marriage_details.couple_display_name,
            'weddingDate': _date_as_text(marriage_details.marriage_date or wedding_event.event_date),
            'marriagePlace': marriage_details.marriage_place or wedding_event.place_name,
            'church': marriage_details.marriage_place or wedding_event.place_name,
            'preparatorySessions': marriage_details.preparatory_sessions,
            'documentsOk': marriage_details.documents_complete,
            'celebrant': wedding_event.minister_name,
            'groomSponsor': groom_witness_name,
            'brideSponsor': bride_witness_name,
            'witnesses': marriage_details.witnesses_name,
            'contact': marriage_details.contact,
            'status': marriage_details.operational_status,
            'stipend': float(marriage_details.stipend),
            'stipendPaid': marriage_details.stipend_paid,
            'registryNo': register_entry.entry_reference if register_entry else '',
        })
    return wedding_records


@with_tenant_schema
def _synchronize_spouses(
    parish: Parish,
    wedding_event: SacramentalEvent,
    wedding_record: dict,
) -> None:
    groom_name, bride_name = _names_from_record(wedding_record)
    existing_spouses = list(
        wedding_event.participants.filter(
            role=EventParticipant.Role.SPOUSE
        ).order_by('display_order', 'id')
    )
    retained_participant_ids = []
    for display_order, spouse_name in enumerate((groom_name, bride_name)):
        if not spouse_name:
            continue
        if display_order < len(existing_spouses):
            spouse = existing_spouses[display_order]
            spouse.historical_name = spouse_name
            spouse.display_order = display_order
            spouse.save(update_fields=('historical_name', 'display_order'))
        else:
            spouse = EventParticipant.objects.create(
                parish=parish,
                event=wedding_event,
                role=EventParticipant.Role.SPOUSE,
                historical_name=spouse_name,
                display_order=display_order,
            )
        retained_participant_ids.append(spouse.id)
    wedding_event.participants.filter(
        role=EventParticipant.Role.SPOUSE
    ).exclude(id__in=retained_participant_ids).delete()


@with_tenant_schema
def _synchronize_wedding(parish: Parish, wedding_record: dict) -> SacramentalEvent:
    public_identifier = str(wedding_record.get('id') or '').strip()
    couple_name = str(wedding_record.get('couple') or '').strip()
    if not public_identifier:
        raise ValidationError('Vjenčanje nema stabilni identifikator.')
    if not couple_name:
        raise ValidationError('Upišite mladence.')

    wedding_event, _ = SacramentalEvent.objects.get_or_create(
        parish=parish,
        event_type=SacramentalEvent.EventType.MARRIAGE,
        public_identifier=public_identifier,
        defaults={
            'celebrating_parish': parish,
            'source': SacramentalEvent.Source.MANUAL,
        },
    )
    wedding_event.event_date = _parse_optional_date(
        wedding_record.get('weddingDate')
    )
    wedding_event.place_name = str(wedding_record.get('church') or '').strip()
    wedding_event.minister_name = str(
        wedding_record.get('celebrant') or ''
    ).strip()
    wedding_event.liturgical_tradition = parish.default_liturgical_tradition
    wedding_event.canonical_tradition = parish.canonical_tradition_for_events()
    if wedding_event.status == SacramentalEvent.Status.CANCELLED:
        wedding_event.status = SacramentalEvent.Status.DRAFT
    wedding_event.save()

    _synchronize_spouses(parish, wedding_event, wedding_record)
    witnesses_name = str(wedding_record.get('witnesses') or '').strip()
    groom_witness_name = str(
        wedding_record.get('groomSponsor') or ''
    ).strip()
    bride_witness_name = str(
        wedding_record.get('brideSponsor') or ''
    ).strip()
    if not witnesses_name:
        witnesses_name = ', '.join(
            name for name in (groom_witness_name, bride_witness_name) if name
        )
    details = MarriageDetails.objects.filter(event=wedding_event).first()
    if details is None:
        details = MarriageDetails(event=wedding_event)
    groom_name, bride_name = _names_from_record(wedding_record)
    groom_parts = _split_name(groom_name)
    bride_parts = _split_name(bride_name)
    groom_witness_parts = _split_name(groom_witness_name)
    bride_witness_parts = _split_name(bride_witness_name)
    officiant_parts = _split_name(wedding_record.get('celebrant'))
    entry_number = wedding_record.get('entryNumber')
    values = {
        'entry_number': int(entry_number) if str(entry_number or '').isdigit() else None,
        'physical_page': str(wedding_record.get('physicalPage') or '').strip() or None,
        'marriage_date': _parse_optional_date(wedding_record.get('weddingDate')),
        'marriage_place': str(wedding_record.get('marriagePlace') or wedding_record.get('church') or '').strip(),
        'groom_first_name': str(wedding_record.get('groomFirstName') or groom_parts[0]).strip(),
        'groom_last_name': str(wedding_record.get('groomLastName') or groom_parts[1]).strip(),
        'groom_birth_place': str(wedding_record.get('groomBirthPlace') or '').strip(),
        'groom_birth_date': _parse_optional_date(wedding_record.get('groomBirthDate')),
        'groom_oib': str(wedding_record.get('groomOib') or '').strip() or None,
        'groom_religion': str(wedding_record.get('groomReligion') or '').strip(),
        'groom_baptism_date': _parse_optional_date(wedding_record.get('groomBaptismDate')),
        'groom_baptism_parish': str(wedding_record.get('groomBaptismParish') or '').strip(),
        'groom_baptism_parish_address': str(wedding_record.get('groomBaptismParishAddress') or '').strip(),
        'groom_residence_address': str(wedding_record.get('groomResidenceAddress') or '').strip(),
        'bride_first_name': str(wedding_record.get('brideFirstName') or bride_parts[0]).strip(),
        'bride_last_name': str(wedding_record.get('brideLastName') or bride_parts[1]).strip(),
        'bride_birth_place': str(wedding_record.get('brideBirthPlace') or '').strip(),
        'bride_birth_date': _parse_optional_date(wedding_record.get('brideBirthDate')),
        'bride_oib': str(wedding_record.get('brideOib') or '').strip() or None,
        'bride_religion': str(wedding_record.get('brideReligion') or '').strip(),
        'bride_baptism_date': _parse_optional_date(wedding_record.get('brideBaptismDate')),
        'bride_baptism_parish': str(wedding_record.get('brideBaptismParish') or '').strip(),
        'bride_baptism_parish_address': str(wedding_record.get('brideBaptismParishAddress') or '').strip(),
        'bride_residence_address': str(wedding_record.get('brideResidenceAddress') or '').strip(),
        'groom_father_first_name': str(wedding_record.get('groomFatherFirstName') or '').strip(),
        'groom_father_last_name': str(wedding_record.get('groomFatherLastName') or '').strip(),
        'groom_mother_first_name': str(wedding_record.get('groomMotherFirstName') or '').strip(),
        'groom_mother_maiden_name': str(wedding_record.get('groomMotherMaidenName') or '').strip(),
        'bride_father_first_name': str(wedding_record.get('brideFatherFirstName') or '').strip(),
        'bride_father_last_name': str(wedding_record.get('brideFatherLastName') or '').strip(),
        'bride_mother_first_name': str(wedding_record.get('brideMotherFirstName') or '').strip(),
        'bride_mother_maiden_name': str(wedding_record.get('brideMotherMaidenName') or '').strip(),
        'groom_witness_first_name': str(wedding_record.get('groomWitnessFirstName') or groom_witness_parts[0]).strip(),
        'groom_witness_last_name': str(wedding_record.get('groomWitnessLastName') or groom_witness_parts[1]).strip(),
        'bride_witness_first_name': str(wedding_record.get('brideWitnessFirstName') or bride_witness_parts[0]).strip(),
        'bride_witness_last_name': str(wedding_record.get('brideWitnessLastName') or bride_witness_parts[1]).strip(),
        'officiant_first_name': str(wedding_record.get('officiantFirstName') or officiant_parts[0]).strip(),
        'officiant_last_name': str(wedding_record.get('officiantLastName') or officiant_parts[1]).strip(),
        'officiant_role': str(wedding_record.get('officiantRole') or '').strip(),
        'notes': str(wedding_record.get('notes') or '').strip() or None,
        'couple_display_name': couple_name, 'contact': str(wedding_record.get('contact') or '').strip(),
        'preparatory_sessions': int(wedding_record.get('preparatorySessions') or 0),
        'documents_complete': bool(wedding_record.get('documentsOk', False)),
        'witnesses_name': witnesses_name, 'groom_witness_name': groom_witness_name,
        'bride_witness_name': bride_witness_name,
        'operational_status': str(wedding_record.get('status') or 'planirano').strip(),
        'stipend': _parse_amount(wedding_record.get('stipend')),
        'stipend_paid': bool(wedding_record.get('stipendPaid', False)),
    }
    for name, value in values.items():
        setattr(details, name, value)
    details.save(update_fields=(tuple(values) if details.pk else None))
    return wedding_event


@transaction.atomic
@with_tenant_schema
def reconcile_wedding_records(parish: Parish, wedding_records: list[dict]) -> None:
    retained_event_ids = []
    seen_identifiers = set()
    for wedding_record in wedding_records:
        public_identifier = str(wedding_record.get('id') or '').strip()
        if public_identifier in seen_identifiers:
            raise ValidationError('Identifikator vjenčanja se ponavlja.')
        seen_identifiers.add(public_identifier)
        wedding_event = _synchronize_wedding(parish, wedding_record)
        retained_event_ids.append(wedding_event.id)

    removed_events = SacramentalEvent.objects.filter(
        parish=parish,
        event_type=SacramentalEvent.EventType.MARRIAGE,
    ).exclude(id__in=retained_event_ids)
    removed_events.update(status=SacramentalEvent.Status.CANCELLED)
