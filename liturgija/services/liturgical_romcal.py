"""Lokalni liturgijski kalendar temeljen na Romcalu.

Adapter namjerno ne poziva mrežu. Romcal daje strukturu i vlastiti kalendar
za Hrvatsku, a ovaj modul rezultat prevodi u postojeći API format projekta.
"""
from __future__ import annotations

import calendar
import re
from functools import lru_cache

from django.core.cache import cache

from liturgija.services.liturgical_hilp import hilp_url
from liturgija.services.liturgical_translate import translate_liturgical_name


SEASON_HR = {
    'advent': 'Došašće',
    'christmas_time': 'Božićno vrijeme',
    'lent': 'Korizma',
    'paschal_triduum': 'Vazmeno trodnevlje',
    'easter_time': 'Vazmeno vrijeme',
    'ordinary_time': 'Vrijeme kroz godinu',
}

RANK_HR = {
    'solemnity': 'Svetkovina',
    'sunday': 'Nedjelja',
    'feast': 'Blagdan',
    'memorial': 'Spomen',
    'optional_memorial': 'Izborni spomen',
    'weekday': 'Svagdan',
}

COLOR_HR = {
    'white': 'Bijela',
    'red': 'Crvena',
    'green': 'Zelena',
    'violet': 'Ljubičasta',
    'rose': 'Ružičasta',
    'black': 'Crna',
}

WEEKDAY_HR = {
    1: 'ponedjeljak',
    2: 'utorak',
    3: 'srijeda',
    4: 'četvrtak',
    5: 'petak',
    6: 'subota',
    7: 'nedjelja',
}

SEASON_GENITIVE_HR = {
    'advent': 'došašća',
    'christmas_time': 'božićnog vremena',
    'lent': 'korizme',
    'paschal_triduum': 'Vazmenog trodnevlja',
    'easter_time': 'vazmenog vremena',
    'ordinary_time': 'vremena kroz godinu',
}

TITLE_HR = {
    'mary_mother_of_god': 'Sveta Marija Bogorodica',
    'epiphany_of_the_lord': 'Bogojavljenje',
    'ash_wednesday': 'Pepelnica',
    'palm_sunday': 'Cvjetnica — Nedjelja Muke Gospodnje',
    'holy_thursday': 'Veliki četvrtak',
    'good_friday': 'Veliki petak',
    'holy_saturday': 'Velika subota',
    'easter_sunday': 'Uskrsna nedjelja',
    'ascension_of_the_lord': 'Uzašašće Gospodinovo',
    'pentecost_sunday': 'Duhovi — Pedesetnica',
    'most_holy_trinity': 'Presveto Trojstvo',
    'most_holy_body_and_blood_of_christ': 'Presveto Tijelo i Krv Kristova',
    'sacred_heart_of_jesus': 'Presveto Srce Isusovo',
    'nativity_of_saint_john_the_baptist': 'Rođenje svetoga Ivana Krstitelja',
    'saints_peter_and_paul_apostles': 'Sveti Petar i Pavao, apostoli',
    'assumption_of_the_blessed_virgin_mary': 'Uznesenje Blažene Djevice Marije',
    'christ_the_king': 'Krist Kralj svega stvorenja',
    'immaculate_conception_of_the_blessed_virgin_mary': 'Bezgrešno začeće Blažene Djevice Marije',
    'nativity_of_the_lord': 'Božić — Rođenje Gospodinovo',
    'annunciation_of_the_lord': 'Navještenje Gospodinovo',
    'augustine_kazotic_bishop': 'Blaženi Augustin Kažotić, biskup i mučenik',
}


@lru_cache(maxsize=1)
def _romcal_engine():
    from romcal import Romcal, get_bundled_calendar_definitions, get_bundled_resources

    return Romcal(
        calendar='croatia',
        locale='la',
        calendar_definitions=get_bundled_calendar_definitions(),
        resources=get_bundled_resources(),
        epiphany_on_sunday=False,
        ascension_on_sunday=False,
        corpus_christi_on_sunday=False,
    )


def romcal_version() -> str:
    from romcal import get_version

    return str(get_version())


def _value(value) -> str:
    """Vrijednost Romcal/Pydantic enuma bez oslanjanja na njegov __str__."""
    raw = getattr(value, 'root', getattr(value, 'value', value))
    return str(raw or '')


def _precedence_number(event) -> int:
    match = re.search(r'_(\d+)$', _value(event.precedence))
    return int(match.group(1)) if match else 999


def _pick_primary(events):
    return min(events, key=_precedence_number) if events else None


def _structured_title(event) -> tuple[str, bool]:
    if event.id in TITLE_HR:
        return TITLE_HR[event.id], True

    # Dani vlastitog vremena mogu se pouzdano prevesti iz Romcalovih polja.
    if event.from_calendar_id == 'proper_of_time' and event.week_of_season:
        weekday_number = _value(event.day_of_week)
        weekday = WEEKDAY_HR.get(int(weekday_number), '') if weekday_number.isdigit() else ''
        season = SEASON_GENITIVE_HR.get(_value(event.season), '')
        if weekday and season:
            return f'{weekday.capitalize()} {event.week_of_season}. tjedna {season}', True

    # Za svetačka imena bez točnog rječničkog zapisa koristimo samo brzi,
    # deterministični offline prijevod. Web zahtjev nikada ne čeka prevoditeljski API.
    return translate_liturgical_name(
        event.fullname,
        allow_remote_translation=False,
    )


def _cycle_value(value) -> str:
    if value is None:
        return ''
    raw = _value(value)
    return str(raw).replace('year_', '').upper()


def map_romcal_day(iso: str, events) -> dict | None:
    primary = _pick_primary(events)
    if primary is None:
        return None

    title, translated = _structured_title(primary)
    color = _value(primary.colors[0].key) if primary.colors else 'green'
    celebrations = []
    observances = []
    for event in sorted(events, key=_precedence_number):
        event_title, event_translated = _structured_title(event)
        event_color = _value(event.colors[0].key) if event.colors else 'green'
        observances.append({
            'eventId': event.id,
            'title': event_title,
            'titleOriginal': event.fullname,
            'rank': _value(event.rank),
            'rankLabel': RANK_HR.get(_value(event.rank), event.rank_name),
            'color': event_color,
            'colorLabel': COLOR_HR.get(event_color, event_color),
            'primary': event is primary,
            'translated': event_translated,
        })
        if event is not primary:
            celebrations.append(event_title)

    psalter = _value(primary.psalter_week)
    psalter_number = str(psalter).replace('week_', '')
    return {
        'source': 'romcal',
        'providerVersion': romcal_version(),
        'calendar': 'croatia',
        'calendarScope': primary.from_calendar_id,
        'date': iso,
        'eventId': primary.id,
        'precedence': _value(primary.precedence),
        'title': title,
        'titleOriginal': primary.fullname,
        'subtitle': SEASON_HR.get(_value(primary.season), primary.season_name),
        'seasonWeek': f'{primary.week_of_season}. tjedan' if primary.week_of_season else '',
        'psalterWeekHr': f'{psalter_number}. tjedan psaltira' if psalter_number else '',
        'liturgicalYear': _cycle_value(primary.sunday_cycle),
        'sundayCycle': _cycle_value(primary.sunday_cycle),
        'weekdayCycle': _cycle_value(primary.weekday_cycle),
        'color': color,
        'colorLabel': COLOR_HR.get(color, color),
        'rank': _value(primary.rank),
        'rankLabel': RANK_HR.get(_value(primary.rank), primary.rank_name),
        'holyDayOfObligation': primary.is_holy_day_of_obligation,
        'observances': observances,
        'celebrations': celebrations,
        'readings': [],
        'hilpUrl': hilp_url(iso),
        'translated': translated,
    }


class RomcalLiturgicalService:
    """Determinističan lokalni izvor; nema HTTP poziva ni scrapinga."""

    def get_year_days(self, year: int) -> dict[str, dict]:
        cache_key = f'romcal_croatia_v1_{romcal_version()}_{year}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        raw = _romcal_engine().liturgical_calendar(year)
        days = {
            iso: mapped
            for iso, events in raw.items()
            if (mapped := map_romcal_day(iso, events)) is not None
        }
        cache.set(cache_key, days, 60 * 60 * 24 * 30)
        return days

    def get_month_days(self, year: int, month: int) -> dict[str, dict]:
        _, last = calendar.monthrange(year, month)
        year_days = self.get_year_days(year)
        return {
            iso: year_days[iso]
            for day in range(1, last + 1)
            if (iso := f'{year}-{month:02d}-{day:02d}') in year_days
        }

    def get_day(self, iso: str) -> dict:
        year = int(iso[:4])
        return self.get_year_days(year).get(iso, {
            'source': 'romcal',
            'calendar': 'croatia',
            'date': iso,
            'title': 'Liturgijski podaci nisu pronađeni',
            'readings': [],
            'hilpUrl': hilp_url(iso),
            'translated': False,
        })


COMPARE_FIELDS = (
    'title', 'subtitle', 'color', 'rankLabel', 'liturgicalYear', 'seasonWeek',
)


def compare_liturgical_days(litcal_day: dict, romcal_day: dict) -> dict:
    differences = {
        field: {'litcal': litcal_day.get(field), 'romcal': romcal_day.get(field)}
        for field in COMPARE_FIELDS
        if litcal_day.get(field) != romcal_day.get(field)
    }
    return {
        'date': romcal_day.get('date') or litcal_day.get('date'),
        'matches': not differences,
        'differences': differences,
        'litcal': litcal_day,
        'romcal': romcal_day,
    }
