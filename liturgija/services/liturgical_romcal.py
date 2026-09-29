"""Lokalni Romcal kalendar za Hrvatsku — samo uvoz u tablicu.

Romcal daje datum, rang, latinski naziv i boje. Hrvatski naziv i mapiranje
boje rade se pri uvozu u `liturgical_imports`.
"""
from __future__ import annotations

from functools import lru_cache


RANK_HR = {
    'solemnity': 'Svetkovina',
    'sunday': 'Nedjelja',
    'feast': 'Blagdan',
    'memorial': 'Spomen',
    'optional_memorial': 'Izborni spomen',
    'weekday': 'Svagdan',
}

RANK_PRIORITY = {
    'weekday': 0,
    'optional_memorial': 1,
    'memorial': 2,
    'feast': 4,
    'sunday': 5,
    'solemnity': 6,
}


@lru_cache(maxsize=1)
def _romcal_engine():
    """Jedan Romcal motor po procesu (učitavanje definicija je skupo)."""
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


def _value(value) -> str:
    """Romcal enum/objekt → običan string."""
    raw = getattr(value, 'root', getattr(value, 'value', value))
    return str(raw or '')


def romcal_calendar_events_for_year(year: int) -> list[dict]:
    """Sva Romcal slavlja godine, uključujući svagdan i usporednog sveca."""
    calendar_events = []
    for iso_date, day_events in _romcal_engine().liturgical_calendar(year).items():
        for event in day_events:
            rank = _value(event.rank)
            calendar_events.append({
                'date': iso_date,
                'title': event.fullname,
                'grade': RANK_PRIORITY.get(rank, 0),
                'grade_lcl': RANK_HR.get(rank, event.rank_name),
                'color': [_value(color.key) for color in (event.colors or [])],
            })
    return calendar_events
