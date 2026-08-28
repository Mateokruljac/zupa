"""Pretvorba Street ORM ↔ legacy API dict (camelCase)."""
from __future__ import annotations

from zupa_vjernici.models import Street


def street_as_legacy_record(street: Street) -> dict:
    return {
        'id': street.public_identifier,
        'name': street.name or '',
        'zone': street.zone or '',
        'sortOrder': int(street.sort_order or 0),
        'notes': street.notes or '',
    }


def street_field_defaults_from_legacy(record: dict) -> dict:
    """Polja za update_or_create — bez oslanjanja na payload."""
    return {
        'name': str(record.get('name') or ''),
        'zone': str(record.get('zone') or ''),
        'sort_order': int(record.get('sortOrder') or 0),
        'notes': str(record.get('notes') or ''),
        'payload': {},
    }
