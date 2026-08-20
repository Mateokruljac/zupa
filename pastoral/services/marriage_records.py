"""Relational persistence and stable UI projection for marriages."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from pastoral.models import (
    EventParticipant,
    MarriageDetails,
    Parish,
    SacramentalEvent,
)


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


def relational_weddings_as_dictionaries(parish: Parish) -> list[dict]:
    wedding_events = (
        SacramentalEvent.objects.filter(
            parish=parish,
            event_type=SacramentalEvent.EventType.MARRIAGE,
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
        groom_witness_name, bride_witness_name = _witness_names(marriage_details)
        wedding_records.append({
            'id': wedding_event.public_identifier,
            'groomName': groom_name,
            'brideName': bride_name,
            'couple': marriage_details.couple_display_name,
            'weddingDate': _date_as_text(wedding_event.event_date),
            'church': wedding_event.place_name,
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
    if parish.church_sui_iuris_id:
        wedding_event.canonical_tradition = (
            parish.church_sui_iuris.canonical_tradition
        )
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
    MarriageDetails.objects.update_or_create(
        event=wedding_event,
        defaults={
            'couple_display_name': couple_name,
            'contact': str(wedding_record.get('contact') or '').strip(),
            'preparatory_sessions': int(
                wedding_record.get('preparatorySessions') or 0
            ),
            'documents_complete': bool(wedding_record.get('documentsOk', False)),
            'witnesses_name': witnesses_name,
            'groom_witness_name': groom_witness_name,
            'bride_witness_name': bride_witness_name,
            'operational_status': str(
                wedding_record.get('status') or 'planirano'
            ).strip(),
            'stipend': _parse_amount(wedding_record.get('stipend')),
            'stipend_paid': bool(wedding_record.get('stipendPaid', False)),
        },
    )
    return wedding_event


@transaction.atomic
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
