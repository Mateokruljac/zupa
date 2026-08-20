"""Raspored misa — rezolucija termina po danu (logika iz mise-engine.js)."""
from __future__ import annotations

import copy
from datetime import date

from pastoral.services.dates import today_iso

DOW_LABEL = {
    0: 'Nedjelja', 1: 'Ponedjeljak', 2: 'Utorak', 3: 'Srijeda',
    4: 'Četvrtak', 5: 'Petak', 6: 'Subota',
}


def weekdays_from_entry(entry: dict) -> list[int]:
    if entry.get('weekdays'):
        return list(entry['weekdays'])
    day = entry.get('day') or ''
    if day == 'Nedjelja':
        return [0]
    if day == 'Subota':
        return [6]
    if day in ('Pon–Pet', 'Pon-Pet'):
        return [1, 2, 3, 4, 5]
    if day.startswith('Pon'):
        return [1]
    if day.startswith('Uto'):
        return [2]
    if day.startswith('Sri'):
        return [3]
    if day.startswith('Čet') or day.startswith('Cet'):
        return [4]
    if day.startswith('Pet'):
        return [5]
    return []


def day_label_from_weekdays(weekdays: list[int]) -> str:
    w = sorted(set(weekdays))
    if w == [1, 2, 3, 4, 5]:
        return 'Pon–Pet'
    if w == [0]:
        return 'Nedjelja'
    if w == [6]:
        return 'Subota'
    return ', '.join(DOW_LABEL.get(d, '?')[:3] for d in w)


def normalize_schedule_entry(entry: dict) -> dict:
    weekdays = weekdays_from_entry(entry)
    out = copy.deepcopy(entry)
    out['weekdays'] = weekdays
    out['day'] = entry.get('day') or day_label_from_weekdays(weekdays)
    out.setdefault('celebrant', '')
    out.setdefault('location', '')
    out.setdefault('notes', '')
    out.setdefault('validFrom', '')
    out.setdefault('validUntil', '')
    return out


def schedule_entry_applies_on_date(entry: dict, iso_date: str) -> bool:
    valid_from = entry.get('validFrom') or ''
    valid_until = entry.get('validUntil') or ''
    if valid_from and iso_date < valid_from:
        return False
    if valid_until and iso_date > valid_until:
        return False
    return True


def migrate_mass_schedule(data: dict) -> None:
    if not isinstance(data.get('massSchedule'), list):
        data['massSchedule'] = []
    data['massSchedule'] = [normalize_schedule_entry(e) for e in data['massSchedule']]
    if not isinstance(data.get('massExceptions'), list):
        data['massExceptions'] = []
    if not isinstance(data.get('massScheduleLog'), list):
        data['massScheduleLog'] = []


def get_masses_for_date(data: dict, iso: str) -> list[dict]:
    exc = next((e for e in data.get('massExceptions') or [] if e.get('date') == iso), None)
    dow = date.fromisoformat(iso).weekday()
    # Python weekday: Mon=0 .. Sun=6; JS getDay: Sun=0 .. Sat=6
    js_dow = (dow + 1) % 7
    slots: list[dict] = []

    if not exc or not exc.get('cancelAll'):
        for raw in data.get('massSchedule') or []:
            entry = normalize_schedule_entry(raw)
            if not schedule_entry_applies_on_date(entry, iso):
                continue
            if js_dow not in weekdays_from_entry(entry):
                continue
            if exc and entry.get('time') in (exc.get('cancelTimes') or []):
                continue
            slots.append({
                'time': entry.get('time'),
                'celebrant': entry.get('celebrant', ''),
                'location': entry.get('location', ''),
                'notes': entry.get('notes', ''),
                'scheduleId': entry.get('id'),
                'kind': 'regular',
            })

    for add in (exc or {}).get('addSlots') or []:
        slots.append({
            'time': add.get('time'),
            'celebrant': add.get('celebrant', ''),
            'location': add.get('location', ''),
            'notes': add.get('note') or (exc or {}).get('note', ''),
            'kind': 'exception',
        })

    slots.sort(key=lambda s: str(s.get('time') or ''))
    return slots


def format_mass_schedule_html(data: dict) -> str:
    from html import escape
    rows = data.get('massSchedule') or []
    if not rows:
        return '<p>Raspored misa nije unesen.</p>'
    items = []
    for raw in rows:
        e = normalize_schedule_entry(raw)
        extra = ' · '.join(x for x in (e.get('celebrant'), e.get('notes')) if x)
        line = f'<li><strong>{escape(e.get("day") or "")}</strong> — {escape(e.get("time") or "")}'
        valid_from = e.get('validFrom') or ''
        valid_until = e.get('validUntil') or ''
        if valid_from or valid_until:
            validity = f'{valid_from or "…"} – {valid_until or "trajno"}'
            extra = ' · '.join(value for value in (extra, validity) if value)
        if extra:
            line += f' <span class="card-sub">({escape(extra)})</span>'
        line += '</li>'
        items.append(line)
    return f'<ul class="listic-ul">{"".join(items)}</ul>'


def week_intentions(data: dict, start_iso: str | None = None) -> list[dict]:
    from pastoral.services.dates import week_end_from, week_start_from
    start = week_start_from(start_iso)
    end = week_end_from(start)
    rows = [
        n for n in data.get('intentions') or []
        if start <= (n.get('date') or '') <= end
    ]
    rows.sort(key=lambda n: (n.get('date') or '', n.get('massTime') or ''))
    return rows
