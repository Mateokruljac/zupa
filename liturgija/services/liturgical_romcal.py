"""Lokalni Romcal kalendar za Hrvatsku — samo uvoz u tablicu.

Romcal daje datum, rang i latinski naziv. Hrvatski naziv i boja dolaze
iz kataloga liturgijskih dana.
"""
from __future__ import annotations

from functools import lru_cache

from liturgija.services.liturgical_day_catalog import localize_celebration


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
    raw = getattr(value, 'root', getattr(value, 'value', value))
    return str(raw or '')


def _display_name(event) -> str:
    display_name, _, _ = localize_celebration(event.fullname)
    return display_name


def _romcal_resolved_color(event, display_name: str) -> str:
    from liturgija.services.liturgical_imports import _normalized_liturgical_color

    rank = _value(event.rank)
    source_colors = [_value(color.key) for color in (event.colors or [])]
    return _normalized_liturgical_color({
        'color': source_colors or ['green'],
        'event_key': event.id,
        'name': display_name,
        'title': event.fullname,
        'grade': RANK_PRIORITY.get(rank, 0),
        'grade_lcl': RANK_HR.get(rank, event.rank_name),
    })


def romcal_calendar_events_for_year(year: int) -> list[dict]:
    """Sva Romcal slavlja godine, uključujući svagdan i usporednog sveca."""
    calendar_events = []
    for iso_date, day_events in _romcal_engine().liturgical_calendar(year).items():
        for event in day_events:
            title = _display_name(event)
            rank = _value(event.rank)
            calendar_events.append({
                'date': iso_date,
                'name': title,
                'title': event.fullname,
                'event_key': event.id,
                'grade': RANK_PRIORITY.get(rank, 0),
                'grade_lcl': RANK_HR.get(rank, event.rank_name),
                'color': _romcal_resolved_color(event, title),
            })
    return calendar_events
