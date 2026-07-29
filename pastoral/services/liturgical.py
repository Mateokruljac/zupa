"""Liturgijski kalendar — LitCal (nacija VA) + prijevod na hrvatski."""
from __future__ import annotations

import calendar
import json
import logging
import urllib.error
import urllib.request
from pathlib import Path

from django.conf import settings
from django.core.cache import cache

from pastoral.services.liturgical_hilp import fetch_hilp_day, hilp_url
from pastoral.services.liturgical_deep import translate_reading_ref, translate_to_hr
from pastoral.services.liturgical_translate import (
    translate_liturgical_name,
    translate_season_lcl,
)

logger = logging.getLogger(__name__)

LITCAL_BASE = 'https://litcal.johnromanodorazio.com/api/v5/calendar'
LITCAL_NATION = 'VA'

SEASON_HR = {
    'ADVENT': 'Advent',
    'CHRISTMASTIDE': 'Božićno razdoblje',
    'CHRISTMAS TIME': 'Božićno razdoblje',
    'LENT': 'Korizma',
    'EASTER TRIDUUM': 'Veliki tjedan / Triduum',
    'EASTERTIDE': 'Uskrsno razdoblje',
    'ORDINARY TIME': 'Obično vrijeme',
    'ORDINARY_TIME': 'Obično vrijeme',
}

COLOR_HR = {
    'purple': 'Ljubičasta',
    'violet': 'Ljubičasta',
    'purpura': 'Ljubičasta',
    'white': 'Bijela',
    'red': 'Crvena',
    'green': 'Zelena',
    'rose': 'Ružičasta',
    'black': 'Crna',
    'zelena': 'Zelena',
    'bijela': 'Bijela',
    'crvena': 'Crvena',
    'ljubičasta': 'Ljubičasta',
    'ružičasta': 'Ružičasta',
}

GRADE_HR = {
    0: 'Radni dan',
    1: 'Izborni spomen',
    2: 'Spomen',
    3: 'Spomen',
    4: 'Blagdan',
    5: 'Blagdan',
    6: 'Svetkovina',
    7: 'Svetkovina',
}

GRADE_TEXT_HR = {
    'SOLEMNITY': 'Svetkovina',
    'FEAST': 'Blagdan',
    'MEMORIAL': 'Spomen',
    'OPTIONAL MEMORIAL': 'Izborni spomen',
    'FERIAL': 'Radni dan',
    'WEEKDAY': 'Radni dan',
}


def _litcal_fixture_dir() -> Path:
    base = Path(getattr(settings, 'BASE_DIR', Path(__file__).resolve().parents[2]))
    candidates = [
        base / 'static' / 'data' / 'litcal',
        Path(__file__).resolve().parents[2] / 'static' / 'data' / 'litcal',
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def _hilp_url(iso: str) -> str:
    return hilp_url(iso)


def season_label(raw: str) -> str:
    if not raw:
        return ''
    key = str(raw).upper().replace(' ', ' ')
    return SEASON_HR.get(key) or SEASON_HR.get(key.replace(' ', '_')) or translate_season_lcl(raw)


def color_label(colors) -> str:
    if isinstance(colors, list):
        c = colors[0] if colors else ''
    else:
        c = colors or ''
    if not c:
        return ''
    low = str(c).lower()
    return COLOR_HR.get(low) or str(c)


def format_rank_hr(rank) -> str:
    if rank is None or rank == '':
        return ''
    if isinstance(rank, int) or (isinstance(rank, str) and str(rank).isdigit()):
        n = int(rank)
        if n in GRADE_HR:
            return GRADE_HR[n]
    raw = str(rank).strip().upper()
    if raw in GRADE_TEXT_HR:
        return GRADE_TEXT_HR[raw]
    return str(rank)


def _pick_primary(events: list) -> dict | None:
    if not events:
        return None
    candidates = [e for e in events if not e.get('is_vigil_mass')]
    if not candidates:
        return events[0]
    return max(candidates, key=lambda e: e.get('grade') or 0)


def _event_color(ev: dict) -> str:
    c = ev.get('color')
    if isinstance(c, list) and c:
        return str(c[0]).lower()
    if isinstance(c, str) and c:
        return c.lower()
    return 'green'


def _litcal_api_url(year: int) -> str:
    return f'{LITCAL_BASE}/nation/{LITCAL_NATION}?year={year}&return_type=JSON'


def _load_events(year: int) -> list:
    cache_key = f'litcal_va_raw_{year}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    url = _litcal_api_url(year)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Pastoral/1.0 (+zupa)'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        events = data.get('litcal') or data.get('Litcal') or []
        if events:
            cache.set(cache_key, events, 60 * 60 * 24)
            return events
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        logger.warning('LitCal API %s %s: %s', LITCAL_NATION, year, exc)

    fixture_dir = _litcal_fixture_dir()
    for fixture in (fixture_dir / 'va' / f'{year}.json', fixture_dir / f'{year}.json'):
        if not fixture.exists():
            continue
        try:
            with fixture.open(encoding='utf-8') as f:
                data = json.load(f)
            events = data.get('litcal') or data.get('Litcal') or []
            if events:
                logger.info('LitCal %s iz fixture %s', LITCAL_NATION, fixture.name)
                cache.set(cache_key, events, 60 * 60 * 24)
                return events
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning('LitCal fixture %s: %s', fixture, exc)

    return []


def _build_index(events: list) -> dict[str, list]:
    by_day: dict[str, list] = {}
    for ev in events:
        d = (ev.get('date') or '')[:10]
        if not d:
            continue
        by_day.setdefault(d, []).append(ev)
    for day_events in by_day.values():
        day_events.sort(key=lambda e: e.get('grade') or 0, reverse=True)
    return by_day


def _readings_from_litcal(primary: dict) -> list[dict]:
    readings_raw = primary.get('readings') or {}
    readings = []
    if isinstance(readings_raw, dict):
        labels = {
            'first_reading': 'Prvo čitanje',
            'responsorial_psalm': 'Otpjevni psalam',
            'second_reading': 'Drugo čitanje',
            'gospel_acclamation': 'Aleluja',
            'gospel': 'Evanđelje',
        }
        for key, label in labels.items():
            txt = readings_raw.get(key)
            if txt:
                readings.append({
                    'label': label,
                    'text': translate_reading_ref(str(txt)),
                    'reference': str(txt),
                })
    return readings


def map_litcal_day(iso: str, events: list) -> dict | None:
    primary = _pick_primary(events)
    if not primary:
        return None

    others = []
    for e in events:
        if e is primary or not e.get('name') or e.get('is_vigil_mass'):
            continue
        hr, _ = translate_liturgical_name(e.get('name', ''))
        others.append(hr)
        if len(others) >= 4:
            break

    rank = primary.get('grade') if primary.get('grade') is not None else primary.get('grade_lcl')
    season_raw = primary.get('liturgical_season_lcl') or primary.get('liturgical_season')
    title, translated = translate_liturgical_name(primary.get('name', ''))
    subtitle = season_label(season_raw or '')
    if season_raw and subtitle == season_raw:
        subtitle = translate_to_hr(season_raw)

    return {
        'source': 'litcal-va',
        'calendar': LITCAL_NATION,
        'date': iso,
        'title': title,
        'titleOriginal': primary.get('name', ''),
        'subtitle': subtitle,
        'seasonWeek': (
            f'Tjedan psaltira {primary["psalter_week"]}'
            if primary.get('psalter_week') else ''
        ),
        'liturgicalYear': primary.get('liturgical_year') or '',
        'color': _event_color(primary),
        'colorLabel': color_label(primary.get('color_lcl') or primary.get('color')),
        'rank': rank,
        'rankLabel': format_rank_hr(rank),
        'celebrations': others,
        'readings': _readings_from_litcal(primary),
        'hilpUrl': _hilp_url(iso),
        'translated': translated,
    }


def _enrich_with_hilp(day: dict) -> dict:
    if not day or day.get('source') == 'offline':
        return day

    has_readings = bool(day.get('readings'))
    hilp = fetch_hilp_day(day['date'])
    if not hilp:
        return day

    out = dict(day)
    if hilp.get('readings'):
        if not has_readings:
            out['readings'] = hilp['readings']
            out['readingsSource'] = 'hilp'
        else:
            out['readingsSource'] = 'litcal-va'
            out['readingsHilp'] = hilp['readings']
    if hilp.get('gospelThought'):
        out['gospelThought'] = hilp['gospelThought']
    if hilp.get('readingRefs'):
        out['readingRefs'] = translate_to_hr(hilp['readingRefs'])
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
        cache_key = f'litcal_va_hr_v4_days_{year}_hilp_{int(with_hilp)}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        merged: dict[str, list] = {}
        for y in (year - 1, year, year + 1):
            by_day = _build_index(_load_events(y))
            for iso, evs in by_day.items():
                merged.setdefault(iso, []).extend(evs)
        for iso in merged:
            merged[iso].sort(key=lambda e: e.get('grade') or 0, reverse=True)

        days: dict[str, dict] = {}
        for iso, events in merged.items():
            mapped = map_litcal_day(iso, events)
            if mapped:
                if with_hilp:
                    mapped = _enrich_with_hilp(mapped)
                days[iso] = mapped

        cache.set(cache_key, days, 60 * 60 * 12)
        return days

    def _events_for_date(self, iso: str) -> list:
        year = int(iso[:4])
        merged: list = []
        for y in (year - 1, year, year + 1):
            by_day = _build_index(_load_events(y))
            merged.extend(by_day.get(iso, []))
        merged.sort(key=lambda e: e.get('grade') or 0, reverse=True)
        return merged

    def _get_day_litcal(self, iso: str) -> dict:
        cache_key = f'litcal_va_hr_v4_day_{iso}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        events = self._events_for_date(iso)
        if events:
            mapped = map_litcal_day(iso, events)
            if mapped:
                cache.set(cache_key, mapped, 60 * 60 * 12)
                return mapped

        return {
            'source': 'offline',
            'date': iso,
            'title': 'Liturgijski podaci nisu učitani',
            'subtitle': 'Provjerite mrežu ili pokušajte kasnije.',
            'readings': [],
            'hilpUrl': _hilp_url(iso),
            'translated': False,
        }

    def get_month_days(self, year: int, month: int) -> dict[str, dict]:
        """Liturgijski sažetak za mjesec (bez HILP-a radi brzine)."""
        cache_key = f'litcal_va_hr_v4_month_{year}_{month:02d}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        days: dict[str, dict] = {}
        _, last = calendar.monthrange(year, month)
        for day in range(1, last + 1):
            iso = f'{year}-{month:02d}-{day:02d}'
            mapped = self._get_day_litcal(iso)
            if mapped.get('source') != 'offline':
                days[iso] = mapped

        cache.set(cache_key, days, 60 * 60 * 12)
        return days

    def get_day(self, iso: str, *, with_hilp: bool = True) -> dict:
        mapped = self._get_day_litcal(iso)
        if with_hilp and mapped.get('source') != 'offline':
            mapped = _enrich_with_hilp(mapped)
        elif mapped.get('source') == 'offline':
            hilp = fetch_hilp_day(iso)
            if hilp and hilp.get('readings'):
                mapped = {
                    'source': 'hilp',
                    'date': iso,
                    'title': hilp.get('liturgicalWeekHr') or 'Liturgijski dan',
                    'subtitle': hilp.get('psalterWeekHr') or '',
                    'seasonWeek': hilp.get('liturgicalWeekHr') or '',
                    'psalterWeekHr': hilp.get('psalterWeekHr') or '',
                    'color': 'green',
                    'colorLabel': color_label(hilp.get('colorHr') or 'zelena'),
                    'rankLabel': 'Svagdan',
                    'celebrations': [],
                    'readings': hilp.get('readings', []),
                    'gospelThought': hilp.get('gospelThought', ''),
                    'readingRefs': hilp.get('readingRefs', ''),
                    'readingsSource': 'hilp',
                    'hilpUrl': hilp.get('hilpUrl') or _hilp_url(iso),
                    'translated': True,
                }
        return mapped
