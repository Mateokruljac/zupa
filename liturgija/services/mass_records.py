"""Pretvorba mise/nakane ORM ↔ legacy API dict (camelCase za JS)."""
from core.utils import _iso_or_empty
from liturgija.models import MassIntention, MassScheduleSlot


def mass_schedule_slot_as_legacy_record(slot: MassScheduleSlot) -> dict:
    """Red tablice rasporeda → dict koji čita JS (`id` = record_id / PK)."""
    record = {
        'id': str(slot.id),
        'day': slot.day_label or '',
        'time': slot.mass_time or '',
        'weekdays': list(slot.weekdays or []),
        'location': slot.location or '',
        'notes': slot.notes or '',
        'validFrom': _iso_or_empty(slot.valid_from),
        'validUntil': _iso_or_empty(slot.valid_until),
    }
    if slot.no_mass:
        record['noMass'] = True
    return record


def mass_intention_as_legacy_record(intention: MassIntention) -> dict:
    """Red tablice nakane → dict za JS (`id` = record_id / PK)."""
    return {
        'id': str(intention.id),
        'date': _iso_or_empty(intention.intention_date),
        'massTime': intention.mass_time or '',
        'intentionFor': intention.intention_for or '',
        'stipend': float(intention.stipend or 0),
        'paid': bool(intention.is_paid),
        'notes': intention.notes or '',
    }


def mass_exception_as_legacy_record(exception) -> dict:
    """Iznimka (otkaz) → dict za JS (`id` = record_id / PK)."""
    return {
        'id': str(exception.id),
        'date': _iso_or_empty(exception.exception_date),
        'cancelAll': bool(exception.cancel_all),
        'cancelTimes': list(exception.cancel_times or []),
        'note': exception.note or '',
    }