"""Pretvorba uredskih ORM redova ↔ legacy API dict."""
from __future__ import annotations

import copy
from datetime import date

from ured.models import (
    Announcement,
    OfficeTask,
    ParishCalendarEvent,
    PublicSubmission,
    StaffMessage,
)


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


def office_task_as_legacy_record(task: OfficeTask) -> dict:
    return {
        'id': task.public_identifier,
        'title': task.title or '',
        'due': _iso_or_empty(task.due_date),
        'priority': task.priority or 'srednja',
        'done': bool(task.is_done),
        'category': task.category or '',
    }


def office_task_field_defaults_from_legacy(record: dict) -> dict:
    return {
        'title': str(record.get('title') or ''),
        'due_date': _parse_iso_date(record.get('due')),
        'priority': str(record.get('priority') or 'srednja'),
        'is_done': bool(record.get('done')),
        'category': str(record.get('category') or ''),
        'payload': {},
    }


def calendar_event_as_legacy_record(event: ParishCalendarEvent) -> dict:
    return {
        'id': event.public_identifier,
        'title': event.title or '',
        'date': _iso_or_empty(event.event_date),
        'place': event.place or '',
        'type': event.event_type or '',
    }


def calendar_event_field_defaults_from_legacy(record: dict) -> dict:
    return {
        'title': str(record.get('title') or ''),
        'event_date': _parse_iso_date(record.get('date')),
        'place': str(record.get('place') or ''),
        'event_type': str(record.get('type') or ''),
        'payload': {},
    }


def announcement_as_legacy_record(announcement: Announcement) -> dict:
    return {
        'id': announcement.public_identifier,
        'title': announcement.title or '',
        'body': announcement.body or '',
        'at': announcement.announced_at or '',
    }


def announcement_field_defaults_from_legacy(record: dict) -> dict:
    return {
        'title': str(record.get('title') or ''),
        'body': str(record.get('body') or ''),
        'announced_at': str(record.get('at') or ''),
        'payload': {},
    }


def staff_message_as_legacy_record(message: StaffMessage) -> dict:
    return {
        'id': message.public_identifier,
        'from': message.from_name or '',
        'fromRole': message.from_role or '',
        'to': message.to_name or '',
        'toRole': message.to_role or '',
        'subject': message.subject or '',
        'body': message.body or '',
        'at': message.sent_at or '',
        'read': bool(message.is_read),
    }


def staff_message_field_defaults_from_legacy(record: dict) -> dict:
    return {
        'from_name': str(record.get('from') or ''),
        'from_role': str(record.get('fromRole') or ''),
        'to_name': str(record.get('to') or ''),
        'to_role': str(record.get('toRole') or ''),
        'subject': str(record.get('subject') or ''),
        'body': str(record.get('body') or ''),
        'sent_at': str(record.get('at') or ''),
        'is_read': bool(record.get('read')),
        'payload': {},
    }


def public_submission_as_legacy_record(submission: PublicSubmission) -> dict:
    record = copy.deepcopy(submission.extra or {})
    record.update({
        'id': submission.public_identifier,
        'type': submission.form_type or record.get('type') or '',
        'formType': submission.form_type or record.get('formType') or '',
        'status': submission.status or '',
        'name': submission.person_name or '',
        'phone': submission.phone or '',
        'email': submission.email or '',
        'address': submission.address or '',
        'at': submission.submitted_at or record.get('at') or '',
        'data': copy.deepcopy(submission.form_data or {}),
    })
    return record


def public_submission_field_defaults_from_legacy(record: dict) -> dict:
    form_type = str(
        record.get('formType') or record.get('type') or ''
    )
    known_keys = {
        'id', 'type', 'formType', 'status', 'name', 'phone', 'email',
        'address', 'at', 'data',
    }
    extra = {
        key: copy.deepcopy(value)
        for key, value in record.items()
        if key not in known_keys
    }
    return {
        'form_type': form_type,
        'status': str(record.get('status') or ''),
        'person_name': str(record.get('name') or ''),
        'phone': str(record.get('phone') or ''),
        'email': str(record.get('email') or ''),
        'address': str(record.get('address') or ''),
        'submitted_at': str(record.get('at') or ''),
        'form_data': copy.deepcopy(record.get('data') or {})
        if isinstance(record.get('data'), dict)
        else {},
        'extra': extra,
        'payload': {},
    }
