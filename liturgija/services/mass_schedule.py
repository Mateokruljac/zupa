"""Raspored misa — koji termini vrijede na danom datumu.

Ista pravila kao `mise-engine.js`: tjedni raspored, raspon valjanosti,
razdoblje bez mise, iznimke (otkaz svih / pojedinih sati).
"""
from __future__ import annotations

from datetime import date
from html import escape

_DAY_WEEKDAYS = {
    'Nedjelja': [0],
    'Subota': [6],
    'Pon–Pet': [1, 2, 3, 4, 5],
    'Pon-Pet': [1, 2, 3, 4, 5],
}


def _weekdays(entry: dict) -> list[int]:
    """Koji dani u tjednu ovaj red pokriva (JS ``getDay`` indeksi)."""
    raw = entry.get('weekdays')
    if raw:
        try:
            return [int(day) for day in raw]
        except (TypeError, ValueError):
            return []
    day = entry.get('day') or ''
    if day in _DAY_WEEKDAYS:
        return list(_DAY_WEEKDAYS[day])
    for prefix, weekday in (
        ('Pon', 1), ('Uto', 2), ('Sri', 3),
        ('Čet', 4), ('Cet', 4), ('Pet', 5),
    ):
        if day.startswith(prefix):
            return [weekday]
    return []


def _applies_on_date(entry: dict, iso_date: str) -> bool:
    """Je li red unutar ``validFrom``–``validUntil`` (prazno = bez granice)."""
    valid_from = entry.get('validFrom') or ''
    valid_until = entry.get('validUntil') or ''
    if valid_from and iso_date < valid_from:
        return False
    if valid_until and iso_date > valid_until:
        return False
    return True


def get_masses_for_date(data: dict, iso: str) -> list[dict]:
    """Termini mise tog datuma, sortirani po satu.

    Ako vrijedi „nema mise” ili otkaz svih → prazno; inače tjedni raspored
    minus otkazani sati.
    """
    js_dow = (date.fromisoformat(iso).weekday() + 1) % 7
    schedule = data.get('massSchedule') or []
    if any(
        entry.get('noMass')
        and _applies_on_date(entry, iso)
        and js_dow in _weekdays(entry)
        for entry in schedule
    ):
        return []

    exception = next(
        (row for row in (data.get('massExceptions') or []) if row.get('date') == iso),
        None,
    )
    if exception and exception.get('cancelAll'):
        return []
    cancelled_times = set(exception.get('cancelTimes') or []) if exception else set()

    slots = []
    for entry in schedule:
        if entry.get('noMass'):
            continue
        if not _applies_on_date(entry, iso) or js_dow not in _weekdays(entry):
            continue
        time = entry.get('time') or ''
        if time in cancelled_times:
            continue
        slots.append({
            'time': time,
            'location': entry.get('location') or '',
            'notes': entry.get('notes') or '',
            'scheduleId': entry.get('id'),
            'kind': 'regular',
        })
    slots.sort(key=lambda slot: slot['time'])
    return slots


def format_mass_schedule_html(data: dict) -> str:
    """HTML popis stalnog rasporeda za župni listić."""
    rows = data.get('massSchedule') or []
    if not rows:
        return '<p>Raspored misa nije unesen.</p>'
    items = []
    for entry in rows:
        slot_label = 'nema mise' if entry.get('noMass') else (entry.get('time') or '')
        extras = [entry.get('notes') or '']
        valid_from = entry.get('validFrom') or ''
        valid_until = entry.get('validUntil') or ''
        if valid_from or valid_until:
            extras.append(f'{valid_from or "…"} – {valid_until or "trajno"}')
        extra = ' · '.join(part for part in extras if part)
        line = (
            f'<li><strong>{escape(entry.get("day") or "")}</strong>'
            f' — {escape(slot_label)}'
        )
        if extra:
            line += f' <span class="card-sub">({escape(extra)})</span>'
        line += '</li>'
        items.append(line)
    return f'<ul class="listic-ul">{"".join(items)}</ul>'
