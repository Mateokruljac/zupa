"""Čitanje liturgijskog kalendara iz baze, uz opcionalnu HILP dopunu.

Put: uvoz (Romcal + kratice čitanja) → `LiturgicalCalendarEntry` → ovdje.
Čitanja dolaze iz tablice; HILP u runtimeu dopunjuje misao / tjedan.
"""
from __future__ import annotations

import calendar
from datetime import date

from liturgija.services.liturgical_hilp import fetch_hilp_day
from liturgija.services.liturgical_imports import (
    stored_calendar_day,
    stored_calendar_days,
)


def _enrich_with_hilp(day: dict) -> dict:
    """Nadopuni dan misli / tjednom s hilp.hr (čitanja ostaju iz baze)."""
    hilp = fetch_hilp_day(day['date'])
    if not hilp:
        return day

    out = dict(day)
    if hilp.get('gospelThought'):
        out['gospelThought'] = hilp['gospelThought']
    if hilp.get('readingRefs') and not out.get('readings'):
        out['readingRefs'] = hilp['readingRefs']
    if hilp.get('liturgicalWeekHr') and not out.get('seasonWeek'):
        out['seasonWeek'] = hilp['liturgicalWeekHr']
    if hilp.get('psalterWeekHr'):
        out['psalterWeekHr'] = hilp['psalterWeekHr']
    out['hilpUrl'] = hilp.get('hilpUrl') or out.get('hilpUrl')
    return out


def get_year_days(year: int) -> dict[str, dict]:
    """Svi uvezeni dani godine, ključ ISO datum. Bez HILP-a."""
    return stored_calendar_days(date(year, 1, 1), date(year, 12, 31))


def get_month_days(year: int, month: int) -> dict[str, dict]:
    """Uvezeni dani jednog mjeseca (bez HILP-a)."""
    _, last_day = calendar.monthrange(year, month)
    return stored_calendar_days(date(year, month, 1), date(year, month, last_day))


def get_day(iso: str | date) -> dict:
    """Jedan dan; HILP može dopuniti misao / tjedan, ne čitanja."""
    iso_date = iso.isoformat() if hasattr(iso, 'isoformat') else str(iso)[:10]
    mapped = stored_calendar_day(iso_date)
    if mapped.get('empty'):
        return mapped
    return _enrich_with_hilp(mapped)
