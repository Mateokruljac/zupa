"""Pretvorba liturgijskog ORM-a ↔ camelCase dict za JS."""
from __future__ import annotations

import copy
import uuid
from datetime import timedelta

from core.utils import _decimal_amount, _iso_or_empty, _parse_iso_date
from liturgija.models import (
    BulletinIssue,
    MassException,
    MassIntention,
    MassScheduleSlot,
)


def parse_optional_uuid(value):
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


def mass_schedule_slot_as_legacy_record(slot: MassScheduleSlot) -> dict:
    """Red tablice rasporeda → dict koji čita JS (`id` = PK)."""
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
    """Red tablice nakane → dict za JS (`id` = PK)."""
    return {
        'id': str(intention.id),
        'date': _iso_or_empty(intention.intention_date),
        'massTime': intention.mass_time or '',
        'intentionFor': intention.intention_for or '',
        'stipend': float(intention.stipend or 0),
        'paid': bool(intention.is_paid),
        'notes': intention.notes or '',
    }


def mass_exception_as_legacy_record(exception: MassException) -> dict:
    """Iznimka (otkaz) → dict za JS (`id` = PK)."""
    return {
        'id': str(exception.id),
        'date': _iso_or_empty(exception.exception_date),
        'cancelAll': bool(exception.cancel_all),
        'cancelTimes': list(exception.cancel_times or []),
        'note': exception.note or '',
    }


def bulletin_issue_as_legacy_record(issue: BulletinIssue) -> dict:
    """Red tablice listića → dict koji čita JS i povijest izdanja."""
    layout = issue.layout if isinstance(issue.layout, dict) else {}
    return {
        'id': str(issue.id),
        'weekStart': _iso_or_empty(issue.week_start),
        'weekEnd': _iso_or_empty(issue.week_end),
        'title': issue.title or '',
        'status': issue.status or BulletinIssue.Status.PUBLISHED,
        'layoutSnapshot': copy.deepcopy(layout),
        'renderedHtml': issue.rendered_html or '',
        'createdAt': issue.created_at.isoformat() if issue.created_at else '',
        'updatedAt': issue.updated_at.isoformat() if issue.updated_at else '',
    }


def schedule_collections() -> dict:
    """Raspored i iznimke u obliku koji čita ``get_masses_for_date``."""
    return {
        'massSchedule': [
            mass_schedule_slot_as_legacy_record(slot)
            for slot in MassScheduleSlot.objects.all()
        ],
        'massExceptions': [
            mass_exception_as_legacy_record(row)
            for row in MassException.objects.all()
        ],
    }


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


def mass_schedule_slot_field_defaults_from_legacy(record: dict) -> dict:
    """JS dict → kwargs za ``MassScheduleSlot``."""
    return {
        'day_label': str(record.get('day') or ''),
        'mass_time': str(record.get('time') or ''),
        'weekdays': _weekdays_list(record.get('weekdays')),
        'location': str(record.get('location') or ''),
        'notes': str(record.get('notes') or ''),
        'valid_from': _parse_iso_date(record.get('validFrom')),
        'valid_until': _parse_iso_date(record.get('validUntil')),
        'no_mass': bool(record.get('noMass')),
    }


def mass_intention_field_defaults_from_legacy(record: dict) -> dict:
    """JS dict → kwargs za ``MassIntention``."""
    return {
        'intention_date': _parse_iso_date(record.get('date')),
        'mass_time': str(record.get('massTime') or ''),
        'intention_for': str(record.get('intentionFor') or ''),
        'stipend': _decimal_amount(record.get('stipend')),
        'is_paid': bool(record.get('paid')),
        'notes': str(record.get('notes') or ''),
    }


def mass_exception_field_defaults_from_legacy(record: dict) -> dict:
    """JS dict → kwargs za iznimku mise."""
    cancel_times = record.get('cancelTimes')
    return {
        'exception_date': _parse_iso_date(record.get('date')),
        'cancel_all': bool(record.get('cancelAll')),
        'cancel_times': list(cancel_times) if isinstance(cancel_times, list) else [],
        'note': str(record.get('note') or ''),
    }


def bulletin_issue_field_defaults_from_legacy(record: dict) -> dict:
    """JS dict → kwargs za ``BulletinIssue`` (bez PK)."""
    layout = record.get('layoutSnapshot')
    if not isinstance(layout, dict):
        layout = {}
    status = str(record.get('status') or BulletinIssue.Status.PUBLISHED)
    if status not in BulletinIssue.Status.values:
        status = BulletinIssue.Status.PUBLISHED
    week_start = _parse_iso_date(record.get('weekStart'))
    week_end = _parse_iso_date(record.get('weekEnd'))
    if week_start is not None and week_end is None:
        week_end = week_start + timedelta(days=6)
    return {
        'week_start': week_start,
        'week_end': week_end,
        'title': str(record.get('title') or '')[:255],
        'status': status,
        'layout': copy.deepcopy(layout),
        'rendered_html': str(record.get('renderedHtml') or ''),
    }
