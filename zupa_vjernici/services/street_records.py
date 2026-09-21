"""
Ulica (SCD2A) ↔ camelCase dict koji UI još očekuje.

Čitanje ide samo s otvorenog reda. Upis verzira materijalnu izmjenu
(naziv, zona). Kućanstva koja drže FK na stari `id` preusmjeravaju se
na novi otvoreni red — inače bi ostala na zatvorenoj verziji ulice.
"""
from __future__ import annotations

from zupa_vjernici.models import Street


def street_as_legacy_record(street: Street) -> dict:
    """Projekcija otvorene ulice u UI ugovor (`id`, `sortOrder`)."""
    return {
        'id': street.public_identifier,
        'name': street.name or '',
        'zone': street.zone or '',
        'sortOrder': int(street.sort_order or 0),
        'notes': street.notes or '',
    }


def street_field_defaults_from_legacy(record: dict) -> dict:
    """Stupci ORM-a iz UI dicta; `payload` se prazni namjerno."""
    return {
        'name': str(record.get('name') or ''),
        'zone': str(record.get('zone') or ''),
        'sort_order': int(record.get('sortOrder') or 0),
        'notes': str(record.get('notes') or ''),
        'payload': {},
    }


def upsert_current_street(parish, public_identifier: str, defaults: dict):
    """Spremi otvorenu ulicu i, ako je verzija, preusmjeri kućanstva.

    Returns:
        (Street, created) — created je True samo za prvi otvoreni red.
    """
    from core.models import upsert_current_scd2
    from zupa_vjernici.models import Household

    previous = Street.current.filter(
        parish=parish,
        public_identifier=public_identifier,
    ).first()
    previous_pk = previous.pk if previous else None
    street, created = upsert_current_scd2(
        Street,
        {'parish': parish, 'public_identifier': public_identifier},
        defaults,
    )
    if previous_pk and street.pk != previous_pk:
        Household.objects.filter(street_id=previous_pk).update(street=street)
    return street, created
