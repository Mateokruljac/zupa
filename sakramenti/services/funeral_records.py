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
from django_multitenant.schema import with_tenant_schema
from sakramenti.services.family_card_sacraments import exclude_family_card_events
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


def _split_name(value) -> tuple[str, str]:
    parts = str(value or '').strip().split()
    if len(parts) > 1:
        return ' '.join(parts[:-1]), parts[-1]
    return (parts[0], '') if parts else ('', '')


@with_tenant_schema
def relational_funerals_as_dictionaries(parish: Parish) -> list[dict]:
    funeral_events = exclude_family_card_events(
        SacramentalEvent.objects.filter(
            parish=parish,
            event_type=SacramentalEvent.EventType.FUNERAL,
            funeral_details__isnull=False,
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
            'entryNumber': register_entry.entry_number if register_entry else funeral_details.entry_number,
            'physicalPage': funeral_details.physical_page or '',
            'deceased': ' '.join(filter(None, (funeral_details.first_name, funeral_details.last_name))) or (recipient.historical_name if recipient else ''),
            'firstName': funeral_details.first_name,
            'lastName': funeral_details.last_name,
            'deathDate': _date_as_text(funeral_details.death_date),
            'deathPlace': funeral_details.death_place,
            'sex': funeral_details.sex,
            'birthPlace': funeral_details.birth_place,
            'birthDate': _date_as_text(funeral_details.birth_date),
            'identifierType': funeral_details.identifier_type or '',
            'identifierValue': funeral_details.identifier_value or '',
            'spouseFirstName': funeral_details.spouse_first_name or '',
            'spouseLastName': funeral_details.spouse_last_name or '',
            'fatherFirstName': funeral_details.father_first_name,
            'fatherLastName': funeral_details.father_last_name,
            'motherFirstName': funeral_details.mother_first_name,
            'motherLastName': funeral_details.mother_last_name,
            'residenceAddress': funeral_details.residence_address,
            'receivedConfession': funeral_details.received_confession,
            'receivedAnointing': funeral_details.received_anointing,
            'receivedCommunion': funeral_details.received_communion,
            'burialPlace': funeral_details.burial_place or funeral_event.place_name,
            'burialDate': _date_as_text(funeral_details.burial_date or funeral_event.event_date),
            'funeralDate': _date_as_text(funeral_details.burial_date or funeral_event.event_date),
            'ministerFirstName': funeral_details.minister_first_name,
            'ministerLastName': funeral_details.minister_last_name,
            'celebrant': ' '.join(filter(None, (funeral_details.minister_first_name, funeral_details.minister_last_name))) or funeral_event.minister_name,
            'causeOfDeath': funeral_details.cause_of_death or '',
            'notes': funeral_details.notes or '',
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


@with_tenant_schema
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


@with_tenant_schema
def _synchronize_funeral(parish: Parish, funeral_record: dict) -> SacramentalEvent:
    public_identifier = str(funeral_record.get('id') or '').strip()
    legacy_deceased_name = str(funeral_record.get('deceased') or '').strip()
    legacy_first_name, legacy_last_name = _split_name(legacy_deceased_name)
    first_name = str(funeral_record.get('firstName') or legacy_first_name).strip()
    last_name = str(funeral_record.get('lastName') or legacy_last_name).strip()
    deceased_name = ' '.join(filter(None, (first_name, last_name)))
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
    burial_date = _parse_optional_date(
        funeral_record.get('burialDate') or funeral_record.get('funeralDate'),
        'burialDate',
    )
    burial_place = str(
        funeral_record.get('burialPlace') or funeral_record.get('cemetery') or ''
    ).strip()
    legacy_minister = _split_name(funeral_record.get('celebrant'))
    minister_first_name = str(funeral_record.get('ministerFirstName') or legacy_minister[0]).strip()
    minister_last_name = str(funeral_record.get('ministerLastName') or legacy_minister[1]).strip()
    minister_name = ' '.join(filter(None, (minister_first_name, minister_last_name))) or str(
        funeral_record.get('celebrant') or ''
    ).strip()
    funeral_event.event_date = burial_date
    funeral_event.place_name = str(
        burial_place
    ).strip()
    funeral_event.minister_name = str(
        minister_name
    ).strip()
    funeral_event.liturgical_tradition = parish.default_liturgical_tradition
    funeral_event.canonical_tradition = parish.canonical_tradition_for_events()
    if funeral_event.status == SacramentalEvent.Status.CANCELLED:
        funeral_event.status = SacramentalEvent.Status.DRAFT
    funeral_event.save()

    _synchronize_recipient(parish, funeral_event, deceased_name)
    funeral_details = FuneralDetails.objects.filter(event=funeral_event).first()
    if funeral_details is None:
        funeral_details = FuneralDetails(event=funeral_event)
    entry_number = funeral_record.get('entryNumber')
    funeral_details.entry_number = int(entry_number) if str(entry_number or '').isdigit() else None
    funeral_details.physical_page = str(funeral_record.get('physicalPage') or '').strip() or None
    funeral_details.death_date = _parse_optional_date(funeral_record.get('deathDate'), 'deathDate')
    funeral_details.death_place = str(funeral_record.get('deathPlace') or '').strip()
    funeral_details.first_name = first_name or deceased_name
    funeral_details.last_name = last_name
    funeral_details.sex = str(funeral_record.get('sex') or '').strip() or None
    funeral_details.birth_place = str(funeral_record.get('birthPlace') or '').strip()
    funeral_details.birth_date = _parse_optional_date(funeral_record.get('birthDate'), 'birthDate')
    funeral_details.identifier_type = str(funeral_record.get('identifierType') or '').strip() or None
    funeral_details.identifier_value = str(funeral_record.get('identifierValue') or '').strip() or None
    funeral_details.spouse_first_name = str(funeral_record.get('spouseFirstName') or '').strip() or None
    funeral_details.spouse_last_name = str(funeral_record.get('spouseLastName') or '').strip() or None
    funeral_details.father_first_name = str(funeral_record.get('fatherFirstName') or '').strip()
    funeral_details.father_last_name = str(funeral_record.get('fatherLastName') or '').strip()
    funeral_details.mother_first_name = str(funeral_record.get('motherFirstName') or '').strip()
    funeral_details.mother_last_name = str(funeral_record.get('motherLastName') or '').strip()
    funeral_details.residence_address = str(funeral_record.get('residenceAddress') or '').strip()
    funeral_details.received_confession = bool(funeral_record.get('receivedConfession', False))
    funeral_details.received_anointing = bool(funeral_record.get('receivedAnointing', False))
    funeral_details.received_communion = bool(funeral_record.get('receivedCommunion', False))
    funeral_details.burial_place = burial_place
    funeral_details.burial_date = burial_date
    funeral_details.minister_first_name = minister_first_name
    funeral_details.minister_last_name = minister_last_name
    funeral_details.cause_of_death = str(funeral_record.get('causeOfDeath') or '').strip() or None
    funeral_details.notes = str(funeral_record.get('notes') or '').strip() or None
    funeral_details.cemetery_location = str(funeral_record.get('cemeteryLocation') or '').strip()
    funeral_details.family_contact = str(funeral_record.get('familyContact') or '').strip()
    funeral_details.mass_planned = bool(funeral_record.get('massPlanned', False))
    funeral_details.mass_date = _parse_optional_date(funeral_record.get('massDate'), 'massDate')
    funeral_details.mass_time = _parse_optional_time(funeral_record.get('massTime'))
    funeral_details.operational_status = str(funeral_record.get('status') or 'planirano').strip()
    funeral_details.stipend = _parse_amount(funeral_record.get('stipend'))
    funeral_details.stipend_paid = bool(funeral_record.get('stipendPaid', False))
    funeral_details.save()
    return funeral_event


@transaction.atomic
@with_tenant_schema
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
