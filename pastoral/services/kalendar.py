"""Kalendar stranica — liturgija + župni događaji."""
from __future__ import annotations

import calendar
from datetime import date

from pastoral.services.liturgical import LiturgicalService


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    _, last = calendar.monthrange(year, month)
    return date(year, month, 1), date(year, month, last)


def kalendar_page_context(data: dict, request) -> dict:
    today = date.today()
    try:
        year = int(request.GET.get('year') or today.year)
    except ValueError:
        year = today.year
    try:
        month = int(request.GET.get('month') or today.month)
    except ValueError:
        month = today.month
    month = max(1, min(12, month))

    selected = (request.GET.get('date') or '').strip()
    if selected == 'today' or not selected:
        selected = today.isoformat()

    lit = LiturgicalService()
    month_days = lit.get_month_days(year, month)

    first_weekday, days_in_month = calendar.monthrange(year, month)
    cells: list[str | None] = [None] * first_weekday
    for d in range(1, days_in_month + 1):
        cells.append(f'{year}-{month:02d}-{d:02d}')
    while len(cells) % 7:
        cells.append(None)

    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    events_by_date: dict[str, list] = {}
    for ev in data.get('events', []):
        d = (ev.get('date') or '')[:10]
        if d:
            events_by_date.setdefault(d, []).append(ev)

    return {
        'rows': data.get('tasks', []),
        'parish_events': data.get('events', []),
        'cal_year': year,
        'cal_month': month,
        'cal_prev': {'year': prev_year, 'month': prev_month},
        'cal_next': {'year': next_year, 'month': next_month},
        'cal_cells': cells,
        'filter_date': selected,
        'lit_month_days': month_days,
        'lit_day': lit.get_day(selected),
        'day_events': events_by_date.get(selected, []),
        'tasks': data.get('tasks', []),
    }
