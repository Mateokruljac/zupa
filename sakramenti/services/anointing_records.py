"""Relational persistence and stable UI projection for anointing visits."""
from __future__ import annotations

from datetime import date, time

from django.core.exceptions import ValidationError
from django.db import transaction

from sakramenti.models import (
    AnointingDetails,
    EventParticipant,
    SacramentalEvent,
)
from django_multitenant.schema import with_tenant_schema
from sakramenti.services.family_card_sacraments import exclude_family_card_events
from pastoral.models import Parish


def _date_as_text(calendar_date: date | None) -> str:
    return calendar_date.isoformat() if calendar_date else ''


def _time_as_text(clock_time: time | None) -> str:
    return clock_time.strftime('%H:%M') if clock_time else ''


def _parse_optional_date(raw_value) -> date | None:
    if not raw_value:
        return None
    if isinstance(raw_value, date):
        return raw_value
    try:
        return date.fromisoformat(str(raw_value))
    except (TypeError, ValueError) as error:
        raise ValidationError({'scheduled': 'Unesite ispravan datum.'}) from error


def _parse_optional_time(raw_value) -> time | None:
    if not raw_value:
        return None
    if isinstance(raw_value, time):
        return raw_value
    try:
        return time.fromisoformat(str(raw_value))
    except (TypeError, ValueError) as error:
        raise ValidationError({'scheduledTime': 'Unesite ispravno vrijeme.'}) from error


@with_tenant_schema
def relational_anointings_as_dictionaries(parish: Parish) -> list[dict]:
    anointing_events = exclude_family_card_events(
        SacramentalEvent.objects.filter(
            parish=parish,
            event_type=SacramentalEvent.EventType.ANOINTING,
            anointing_details__isnull=False,
        )
        .exclude(status=SacramentalEvent.Status.CANCELLED)
        .select_related('anointing_details')
        .prefetch_related('participants')
    )
    anointing_records = []
    for anointing_event in anointing_events:
        anointing_details = anointing_event.anointing_details
        recipient = next(
            (
                participant
                for participant in anointing_event.participants.all()
                if participant.role == EventParticipant.Role.RECIPIENT
            ),
            None,
        )
        anointing_records.append({
            'id': anointing_event.public_identifier,
            'person': recipient.historical_name if recipient else '',
            'address': anointing_details.address,
            'location': anointing_details.location,
            'scheduled': _date_as_text(anointing_event.event_date),
            'scheduledTime': _time_as_text(anointing_details.scheduled_time),
            'priest': anointing_event.minister_name,
            'contact': anointing_details.contact,
            'notes': anointing_details.notes,
            'status': anointing_details.operational_status,
            'done': anointing_details.completed,
        })
    return anointing_records


@with_tenant_schema
def _synchronize_recipient(
    parish: Parish,
    anointing_event: SacramentalEvent,
    recipient_name: str,
) -> None:
    recipient = anointing_event.participants.filter(
        role=EventParticipant.Role.RECIPIENT
    ).order_by('display_order', 'id').first()
    if recipient is None:
        recipient = EventParticipant.objects.create(
            parish=parish,
            event=anointing_event,
            role=EventParticipant.Role.RECIPIENT,
            historical_name=recipient_name,
            display_order=0,
        )
    else:
        recipient.historical_name = recipient_name
        recipient.display_order = 0
        recipient.save(update_fields=('historical_name', 'display_order'))
    anointing_event.participants.filter(
        role=EventParticipant.Role.RECIPIENT
    ).exclude(pk=recipient.pk).delete()


@with_tenant_schema
def _synchronize_anointing(
    parish: Parish,
    anointing_record: dict,
) -> SacramentalEvent:
    public_identifier = str(anointing_record.get('id') or '').strip()
    recipient_name = str(anointing_record.get('person') or '').strip()
    if not public_identifier:
        raise ValidationError('Pomazanje nema stabilni identifikator.')
    if not recipient_name:
        raise ValidationError('Upišite osobu.')

    anointing_event, _ = SacramentalEvent.objects.get_or_create(
        parish=parish,
        event_type=SacramentalEvent.EventType.ANOINTING,
        public_identifier=public_identifier,
        defaults={
            'celebrating_parish': parish,
            'source': SacramentalEvent.Source.MANUAL,
        },
    )
    address = str(anointing_record.get('address') or '').strip()
    anointing_event.event_date = _parse_optional_date(
        anointing_record.get('scheduled')
    )
    anointing_event.place_name = address
    anointing_event.minister_name = str(
        anointing_record.get('priest') or ''
    ).strip()
    anointing_event.liturgical_tradition = parish.default_liturgical_tradition
    anointing_event.canonical_tradition = parish.canonical_tradition_for_events()
    if anointing_event.status == SacramentalEvent.Status.CANCELLED:
        anointing_event.status = SacramentalEvent.Status.DRAFT
    anointing_event.save()

    _synchronize_recipient(parish, anointing_event, recipient_name)
    AnointingDetails.objects.update_or_create(
        event=anointing_event,
        defaults={
            'scheduled_time': _parse_optional_time(
                anointing_record.get('scheduledTime')
            ),
            'address': address,
            'location': str(anointing_record.get('location') or '').strip(),
            'contact': str(anointing_record.get('contact') or '').strip(),
            'notes': str(anointing_record.get('notes') or '').strip(),
            'operational_status': str(
                anointing_record.get('status') or 'planirano'
            ).strip(),
            'completed': bool(anointing_record.get('done', False)),
        },
    )
    return anointing_event


@transaction.atomic
@with_tenant_schema
def reconcile_anointing_records(parish: Parish, anointing_records: list[dict]) -> None:
    retained_event_ids = []
    seen_identifiers = set()
    for anointing_record in anointing_records:
        public_identifier = str(anointing_record.get('id') or '').strip()
        if public_identifier in seen_identifiers:
            raise ValidationError('Identifikator pomazanja se ponavlja.')
        seen_identifiers.add(public_identifier)
        anointing_event = _synchronize_anointing(parish, anointing_record)
        retained_event_ids.append(anointing_event.id)

    SacramentalEvent.objects.filter(
        parish=parish,
        event_type=SacramentalEvent.EventType.ANOINTING,
    ).exclude(id__in=retained_event_ids).update(
        status=SacramentalEvent.Status.CANCELLED
    )
