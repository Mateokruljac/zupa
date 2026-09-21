"""Čitanje liturgijskog kalendara iz baze, uz opcionalna HILP čitanja.

Put: uvoz (Romcal) → `LiturgicalCalendarEntry` → ovaj servis → `/app/` i API.
Ne zove vanjski kalendarski API. HILP je samo dopuna čitanja.
"""
from __future__ import annotations

import calendar
from datetime import date

from django_multitenant.schema import with_tenant_schema
from liturgija.services.liturgical_hilp import fetch_hilp_day
from liturgija.services.liturgical_imports import (
    stored_calendar_day,
    stored_calendar_days,
)

# Token boje (EN ili sinonim) → natpis na hrvatskom za UI.
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
    """Vrati hrvatski naziv boje. Prima string ili listu (uzima prvi član)."""
    # HILP ponekad šalje listu; tablica šalje jedan token.
    token = colors[0] if isinstance(colors, list) and colors else colors
    if not token:
        return ''
    # Nepoznat token ostaje kako je došao (npr. "other").
    return COLOR_HR.get(str(token).lower()) or str(token)


def _enrich_with_hilp(day: dict) -> dict:
    """Nadopuni dan čitanjima s hilp.hr ako ih tablica nema.

    Ne dira prazan dan (`empty`) — nema smisla zvati mrežu za neuvezeni datum.
    """
    if not day or day.get('empty'):
        return day

    # Mrežni dohvat; cache je unutar fetch_hilp_day (24 h).
    hilp = fetch_hilp_day(day['date'])
    if not hilp:
        return day

    out = dict(day)
    # Čitanja iz tablice imaju prednost; HILP samo ako su prazna.
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
    """Jedina ulazna točka aplikacije za liturgijski dan/mjesec/godinu."""

    @with_tenant_schema
    def get_year_days(self, year: int, *, with_hilp: bool = False) -> dict[str, dict]:
        """Svi uvezeni dani godine, ključ ISO datum.

        HILP je isključen po defaultu — 365 HTTP poziva bi usporilo API godine.
        """
        days = stored_calendar_days(date(year, 1, 1), date(year, 12, 31))
        if with_hilp:
            return {iso: _enrich_with_hilp(day) for iso, day in days.items()}
        return days

    @with_tenant_schema
    def get_month_days(self, year: int, month: int) -> dict[str, dict]:
        """Uvezeni dani jednog mjeseca (bez HILP-a)."""
        # Zadnji dan mjeseca (28–31) da filter u SQL-u pokrije cijeli raspon.
        _, last_day = calendar.monthrange(year, month)
        return stored_calendar_days(
            date(year, month, 1),
            date(year, month, last_day),
        )

    @with_tenant_schema
    def get_day(self, iso: str, *, with_hilp: bool = True) -> dict:
        """Jedan dan. Default uključuje HILP čitanja (dashboard, API dana)."""
        # Prihvati i `date` objekt i string "YYYY-MM-DD...".
        iso_date = iso.isoformat() if hasattr(iso, 'isoformat') else str(iso)[:10]
        mapped = stored_calendar_day(iso_date)
        if mapped.get('empty') or not with_hilp:
            return mapped
        return _enrich_with_hilp(mapped)
