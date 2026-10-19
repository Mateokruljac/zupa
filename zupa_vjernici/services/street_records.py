"""
Ulica (SCD2A) ↔ camelCase dict koji UI još očekuje.

Čitanje ide samo s otvorenog reda. Upis verzira materijalnu izmjenu
(naziv, grad). Kućanstva koja drže FK na stari `id` preusmjeravaju se
na novi otvoreni red — inače bi ostala na zatvorenoj verziji ulice.
"""
from __future__ import annotations

from core.models import OPEN_ENDED_VALID_TO
from zupa_vjernici.models import Street
from django_multitenant.schema import with_tenant_schema


def street_as_legacy_record(street: Street) -> dict:
    """Projekcija otvorene ulice u UI ugovor (`id`, `sortOrder`)."""
    return {
        'id': street.public_identifier,
        'name': street.name or '',
        'city': street.city or '',
        'sortOrder': int(street.sort_order or 0),
        'notes': street.notes or '',
    }


@with_tenant_schema
def street_name_history(parish, public_identifier: str) -> list[dict]:
    """Povijest naziva/grada iz SCD2 verzija (najnovije prvo)."""
    if not public_identifier:
        return []
    rows = list(
        Street.objects.filter(
            parish=parish,
            public_identifier=public_identifier,
        ).order_by('-date_from', '-created_at')
    )
    history = []
    for row in rows:
        is_current = row.date_to == OPEN_ENDED_VALID_TO
        history.append({
            'name': row.name or '',
            'city': row.city or '',
            'valid_from': row.date_from.isoformat() if row.date_from else '',
            'valid_to': (
                ''
                if is_current or not row.date_to
                else row.date_to.isoformat()
            ),
            'is_current': is_current,
        })
    return history


def street_field_defaults_from_legacy(record: dict) -> dict:
    """Stupci ORM-a iz UI dicta; `payload` se prazni namjerno."""
    return {
        'name': str(record.get('name') or ''),
        'city': str(record.get('city') or ''),
        'sort_order': int(record.get('sortOrder') or 0),
        'notes': str(record.get('notes') or ''),
        'payload': {},
    }


@with_tenant_schema
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
