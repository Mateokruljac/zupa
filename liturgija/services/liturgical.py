"""Liturgijski kalendar iz uvezenih redaka, uz opcionalna HILP čitanja."""
from __future__ import annotations

import calendar
from datetime import date

from liturgija.services.liturgical_hilp import fetch_hilp_day
from liturgija.services.liturgical_imports import (
    stored_calendar_day,
    stored_calendar_days,
)

COLOR_HR = {
    'purple': 'Ljubičasta',
    'violet': 'Ljubičasta',
    'white': 'Bijela',
    'red': 'Crvena',
    'green': 'Zelena',
    'rose': 'Ružičasta',
    'black': 'Crna',
}


def color_label(colors) -> str:
    token = colors[0] if isinstance(colors, list) and colors else colors
    if not token:
        return ''
    return COLOR_HR.get(str(token).lower()) or str(token)


def _enrich_with_hilp(day: dict) -> dict:
    if not day or day.get('empty'):
        return day

    hilp = fetch_hilp_day(day['date'])
    if not hilp:
        return day

    out = dict(day)
    if hilp.get('readings') and not out.get('readings'):
        out['readings'] = hilp['readings']
        out['readingsSource'] = 'hilp'
    if hilp.get('gospelThought'):
        out['gospelThought'] = hilp['gospelThought']
    if hilp.get('readingRefs'):
        out['readingRefs'] = hilp['readingRefs']
    if hilp.get('liturgicalWeekHr') and not out.get('seasonWeek'):
        out['seasonWeek'] = hilp['liturgicalWeekHr']
    if hilp.get('psalterWeekHr'):
        out['psalterWeekHr'] = hilp['psalterWeekHr']
    if hilp.get('colorHr') and not out.get('colorLabel'):
        out['colorLabel'] = color_label(hilp['colorHr'])
    out['hilpUrl'] = hilp.get('hilpUrl') or out.get('hilpUrl')
    return out


class LiturgicalService:
    def get_year_days(self, year: int, *, with_hilp: bool = False) -> dict[str, dict]:
        days = stored_calendar_days(date(year, 1, 1), date(year, 12, 31))
        if with_hilp:
            return {iso: _enrich_with_hilp(day) for iso, day in days.items()}
        return days

    def get_month_days(self, year: int, month: int) -> dict[str, dict]:
        _, last_day = calendar.monthrange(year, month)
        return stored_calendar_days(
            date(year, month, 1),
            date(year, month, last_day),
        )

    def get_day(self, iso: str, *, with_hilp: bool = True) -> dict:
        iso_date = iso.isoformat() if hasattr(iso, 'isoformat') else str(iso)[:10]
        mapped = stored_calendar_day(iso_date)
        if mapped.get('empty') or not with_hilp:
            return mapped
        return _enrich_with_hilp(mapped)
