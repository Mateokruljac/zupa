"""Relational persistence and stable UI projection for funerals."""
from __future__ import annotations

from datetime import date, time
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from sakramenti.models import (
    EventParticipant,
    FuneralDetails,
    SacramentalEvent,
)
from pastoral.models import Parish


def _date_as_text(calendar_date: date | None) -> str:
    return calendar_date.isoformat() if calendar_date else ''


def _time_as_text(clock_time: time | None) -> str:
    return clock_time.strftime('%H:%M') if clock_time else ''


def _parse_optional_date(raw_value, field_name: str) -> date | None:
    if not raw_value:
        return None
    if isinstance(raw_value, date):
        return raw_value
    try:
        return date.fromisoformat(str(raw_value))
    except (TypeError, ValueError) as error:
        raise ValidationError({field_name: 'Unesite ispravan datum.'}) from error


def _parse_optional_time(raw_value) -> time | None:
    if not raw_value:
        return None
    if isinstance(raw_value, time):
        return raw_value
    try:
        return time.fromisoformat(str(raw_value))
    except (TypeError, ValueError) as error:
        raise ValidationError({'massTime': 'Unesite ispravno vrijeme.'}) from error


def _parse_amount(raw_value) -> Decimal:
    try:
        return Decimal(str(raw_value or 0))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValidationError({'stipend': 'Unesite ispravan iznos.'}) from error


def relational_funerals_as_dictionaries(parish: Parish) -> list[dict]:
    funeral_events = (
        SacramentalEvent.objects.filter(
            parish=parish,
            event_type=SacramentalEvent.EventType.FUNERAL,
        )
        .exclude(status=SacramentalEvent.Status.CANCELLED)
        .select_related('funeral_details', 'register_entry')
        .prefetch_related('participants')
    )
    funeral_records = []
    for funeral_event in funeral_events:
        funeral_details = funeral_event.funeral_details
        register_entry = getattr(funeral_event, 'register_entry', None)
        recipient = next(
            (
                participant
                for participant in funeral_event.participants.all()
                if participant.role == EventParticipant.Role.RECIPIENT
            ),
            None,
        )
        funeral_records.append({
            'id': funeral_event.public_identifier,
            'deceased': recipient.historical_name if recipient else '',
            'deathDate': _date_as_text(funeral_details.death_date),
            'funeralDate': _date_as_text(funeral_event.event_date),
            'celebrant': funeral_event.minister_name,
            'massPlanned': funeral_details.mass_planned,
            'massDate': _date_as_text(funeral_details.mass_date),
            'massTime': _time_as_text(funeral_details.mass_time),
            'cemetery': funeral_event.place_name,
            'cemeteryLocation': funeral_details.cemetery_location,
            'familyContact': funeral_details.family_contact,
            'status': funeral_details.operational_status,
            'stipend': float(funeral_details.stipend),
            'stipendPaid': funeral_details.stipend_paid,
            'registryNo': register_entry.entry_reference if register_entry else '',
        })
    return funeral_records


def _synchronize_recipient(
    parish: Parish,
    funeral_event: SacramentalEvent,
    deceased_name: str,
) -> None:
    recipient = funeral_event.participants.filter(
        role=EventParticipant.Role.RECIPIENT
    ).order_by('display_order', 'id').first()
    if recipient is None:
        recipient = EventParticipant.objects.create(
            parish=parish,
            event=funeral_event,
            role=EventParticipant.Role.RECIPIENT,
            historical_name=deceased_name,
            display_order=0,
        )
    else:
        recipient.historical_name = deceased_name
        recipient.display_order = 0
        recipient.save(update_fields=('historical_name', 'display_order'))
    funeral_event.participants.filter(
        role=EventParticipant.Role.RECIPIENT
    ).exclude(pk=recipient.pk).delete()


def _synchronize_funeral(parish: Parish, funeral_record: dict) -> SacramentalEvent:
    public_identifier = str(funeral_record.get('id') or '').strip()
    deceased_name = str(funeral_record.get('deceased') or '').strip()
    if not public_identifier:
        raise ValidationError('Pogreb nema stabilni identifikator.')
    if not deceased_name:
        raise ValidationError('Upišite pokojnika.')

    funeral_event, _ = SacramentalEvent.objects.get_or_create(
        parish=parish,
        event_type=SacramentalEvent.EventType.FUNERAL,
        public_identifier=public_identifier,
        defaults={
            'celebrating_parish': parish,
            'source': SacramentalEvent.Source.MANUAL,
        },
    )
    funeral_event.event_date = _parse_optional_date(
        funeral_record.get('funeralDate'), 'funeralDate'
    )
    funeral_event.place_name = str(
        funeral_record.get('cemetery') or ''
    ).strip()
    funeral_event.minister_name = str(
        funeral_record.get('celebrant') or ''
    ).strip()
    funeral_event.liturgical_tradition = parish.default_liturgical_tradition
    if parish.church_sui_iuris_id:
        funeral_event.canonical_tradition = (
            parish.church_sui_iuris.canonical_tradition
        )
    if funeral_event.status == SacramentalEvent.Status.CANCELLED:
        funeral_event.status = SacramentalEvent.Status.DRAFT
    funeral_event.save()

    _synchronize_recipient(parish, funeral_event, deceased_name)
    FuneralDetails.objects.update_or_create(
        event=funeral_event,
        defaults={
            'death_date': _parse_optional_date(
                funeral_record.get('deathDate'), 'deathDate'
            ),
            'cemetery_location': str(
                funeral_record.get('cemeteryLocation') or ''
            ).strip(),
            'family_contact': str(
                funeral_record.get('familyContact') or ''
            ).strip(),
            'mass_planned': bool(funeral_record.get('massPlanned', False)),
            'mass_date': _parse_optional_date(
                funeral_record.get('massDate'), 'massDate'
            ),
            'mass_time': _parse_optional_time(funeral_record.get('massTime')),
            'operational_status': str(
                funeral_record.get('status') or 'planirano'
            ).strip(),
            'stipend': _parse_amount(funeral_record.get('stipend')),
            'stipend_paid': bool(funeral_record.get('stipendPaid', False)),
        },
    )
    return funeral_event


@transaction.atomic
def reconcile_funeral_records(parish: Parish, funeral_records: list[dict]) -> None:
    retained_event_ids = []
    seen_identifiers = set()
    for funeral_record in funeral_records:
        public_identifier = str(funeral_record.get('id') or '').strip()
        if public_identifier in seen_identifiers:
            raise ValidationError('Identifikator pogreba se ponavlja.')
        seen_identifiers.add(public_identifier)
        funeral_event = _synchronize_funeral(parish, funeral_record)
        retained_event_ids.append(funeral_event.id)

    SacramentalEvent.objects.filter(
        parish=parish,
        event_type=SacramentalEvent.EventType.FUNERAL,
    ).exclude(id__in=retained_event_ids).update(
        status=SacramentalEvent.Status.CANCELLED
    )
