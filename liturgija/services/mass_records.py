"""Pretvorba mise/nakane ORM ↔ legacy API dict."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from liturgija.models import MassIntention, MassScheduleSlot


def _parse_iso_date(value) -> date | None:
    raw = str(value or '').strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _iso_or_empty(value: date | None) -> str:
    return value.isoformat() if value else ''


def _decimal_amount(value) -> Decimal:
    try:
        return Decimal(str(value if value is not None else 0))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


def _weekdays_list(value) -> list[int]:
    if not isinstance(value, list):
        return []
    weekdays = []
    for item in value:
        try:
            weekdays.append(int(item))
        except (TypeError, ValueError):
            continue
    return weekdays


def mass_schedule_slot_as_legacy_record(slot: MassScheduleSlot) -> dict:
    record = {
        'id': slot.public_identifier,
        'day': slot.day_label or '',
        'time': slot.mass_time or '',
        'weekdays': list(slot.weekdays or []),
        'celebrant': slot.celebrant or '',
        'location': slot.location or '',
        'notes': slot.notes or '',
        'validFrom': _iso_or_empty(slot.valid_from),
        'validUntil': _iso_or_empty(slot.valid_until),
    }
    if slot.no_mass:
        record['noMass'] = True
    return record


def mass_schedule_slot_field_defaults_from_legacy(record: dict) -> dict:
    return {
        'day_label': str(record.get('day') or ''),
        'mass_time': str(record.get('time') or ''),
        'weekdays': _weekdays_list(record.get('weekdays')),
        'celebrant': str(record.get('celebrant') or ''),
        'location': str(record.get('location') or ''),
        'notes': str(record.get('notes') or ''),
        'valid_from': _parse_iso_date(record.get('validFrom')),
        'valid_until': _parse_iso_date(record.get('validUntil')),
        'no_mass': bool(record.get('noMass')),
        'payload': {},
    }


def mass_intention_as_legacy_record(intention: MassIntention) -> dict:
    return {
        'id': intention.public_identifier,
        'date': _iso_or_empty(intention.intention_date),
        'massTime': intention.mass_time or '',
        'requestedBy': intention.requested_by or '',
        'intentionFor': intention.intention_for or '',
        'stipend': float(intention.stipend or 0),
        'paid': bool(intention.is_paid),
        'notes': intention.notes or '',
    }


def mass_intention_field_defaults_from_legacy(record: dict) -> dict:
    return {
        'intention_date': _parse_iso_date(record.get('date')),
        'mass_time': str(record.get('massTime') or ''),
        'requested_by': str(record.get('requestedBy') or ''),
        'intention_for': str(record.get('intentionFor') or ''),
        'stipend': _decimal_amount(record.get('stipend')),
        'is_paid': bool(record.get('paid')),
        'notes': str(record.get('notes') or ''),
        'payload': {},
    }


def mass_exception_as_legacy_record(exception) -> dict:
    return {
        'id': exception.public_identifier,
        'date': _iso_or_empty(exception.exception_date),
        'cancelAll': bool(exception.cancel_all),
        'cancelTimes': list(exception.cancel_times or []),
        'addSlots': list(exception.add_slots or []),
        'note': exception.note or '',
    }


def mass_exception_field_defaults_from_legacy(record: dict) -> dict:
    return {
        'exception_date': _parse_iso_date(record.get('date')),
        'cancel_all': bool(record.get('cancelAll')),
        'cancel_times': list(record.get('cancelTimes') or [])
        if isinstance(record.get('cancelTimes'), list)
        else [],
        'add_slots': list(record.get('addSlots') or [])
        if isinstance(record.get('addSlots'), list)
        else [],
        'note': str(record.get('note') or ''),
        'payload': {},
    }


def mass_schedule_log_as_legacy_record(entry) -> dict:
    return {
        'id': entry.public_identifier,
        'at': entry.logged_at or '',
        'message': entry.message or '',
    }


def mass_schedule_log_field_defaults_from_legacy(record: dict) -> dict:
    return {
        'logged_at': str(record.get('at') or ''),
        'message': str(record.get('message') or ''),
        'payload': {},
    }
