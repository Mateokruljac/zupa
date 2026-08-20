"""Kontekst kalendarske stranice: liturgija, događaji i zadaci."""
from __future__ import annotations

import calendar
from datetime import date

from pastoral.services.liturgical import LiturgicalService


def _integer_query_parameter(request, parameter_name: str, default_value: int) -> int:
    try:
        return int(request.GET.get(parameter_name) or default_value)
    except ValueError:
        return default_value


def _selected_calendar_period(request, today: date) -> tuple[int, int]:
    calendar_year = _integer_query_parameter(request, 'year', today.year)
    requested_month = _integer_query_parameter(request, 'month', today.month)
    calendar_month = max(1, min(12, requested_month))
    return calendar_year, calendar_month


def _selected_calendar_date(request, today: date) -> str:
    selected_date = (request.GET.get('date') or '').strip()
    if selected_date == 'today' or not selected_date:
        return today.isoformat()
    return selected_date


def _calendar_cells(calendar_year: int, calendar_month: int) -> list[str | None]:
    first_weekday, days_in_month = calendar.monthrange(
        calendar_year,
        calendar_month,
    )
    calendar_cells: list[str | None] = [None] * first_weekday
    calendar_cells.extend(
        f'{calendar_year}-{calendar_month:02d}-{day_number:02d}'
        for day_number in range(1, days_in_month + 1)
    )
    while len(calendar_cells) % 7:
        calendar_cells.append(None)
    return calendar_cells


def _adjacent_calendar_periods(
    calendar_year: int,
    calendar_month: int,
) -> tuple[dict, dict]:
    if calendar_month == 1:
        previous_period = {'year': calendar_year - 1, 'month': 12}
    else:
        previous_period = {'year': calendar_year, 'month': calendar_month - 1}

    if calendar_month == 12:
        next_period = {'year': calendar_year + 1, 'month': 1}
    else:
        next_period = {'year': calendar_year, 'month': calendar_month + 1}
    return previous_period, next_period


def _events_grouped_by_date(parish_events: list[dict]) -> dict[str, list[dict]]:
    events_by_date: dict[str, list[dict]] = {}
    for parish_event in parish_events:
        event_date = (parish_event.get('date') or '')[:10]
        if event_date:
            events_by_date.setdefault(event_date, []).append(parish_event)
    return events_by_date


def _open_tasks_grouped_by_date(parish_tasks: list[dict]) -> dict[str, list[dict]]:
    tasks_by_date: dict[str, list[dict]] = {}
    for parish_task in parish_tasks:
        due_date = (parish_task.get('due') or '')[:10]
        if due_date and not parish_task.get('done'):
            tasks_by_date.setdefault(due_date, []).append(parish_task)
    return tasks_by_date


def _calendar_conflicts(parish_events: list[dict]) -> list[dict]:
    conflicts = []
    events_by_time_and_place = {}
    for parish_event in parish_events:
        if not (
            parish_event.get('date')
            and parish_event.get('time')
            and parish_event.get('place')
        ):
            continue
        event_slot = (
            parish_event.get('date'),
            parish_event.get('time'),
            (parish_event.get('place') or '').casefold(),
        )
        existing_event = events_by_time_and_place.get(event_slot)
        if existing_event:
            conflicts.append({
                'first': existing_event,
                'second': parish_event,
            })
        else:
            events_by_time_and_place[event_slot] = parish_event
    return conflicts


def _sorted_tasks(parish_tasks: list[dict]) -> list[dict]:
    return sorted(
        parish_tasks,
        key=lambda parish_task: (
            parish_task.get('done', False),
            parish_task.get('due') or '9999-12-31',
            parish_task.get('priority') != 'visoka',
        ),
    )


def calendar_page_context(parish_data: dict, request) -> dict:
    today = date.today()
    calendar_year, calendar_month = _selected_calendar_period(request, today)
    selected_date = _selected_calendar_date(request, today)

    liturgical_service = LiturgicalService()
    liturgical_month_days = liturgical_service.get_month_days(
        calendar_year,
        calendar_month,
    )
    previous_period, next_period = _adjacent_calendar_periods(
        calendar_year,
        calendar_month,
    )

    parish_events = parish_data.get('events', [])
    parish_tasks = parish_data.get('tasks', [])
    events_by_date = _events_grouped_by_date(parish_events)
    tasks_by_date = _open_tasks_grouped_by_date(parish_tasks)
    sorted_tasks = _sorted_tasks(parish_tasks)
    task_status_filter = request.GET.get('tasks', 'open')
    if task_status_filter == 'done':
        visible_tasks = [
            parish_task
            for parish_task in sorted_tasks
            if parish_task.get('done')
        ]
    elif task_status_filter == 'all':
        visible_tasks = sorted_tasks
    else:
        task_status_filter = 'open'
        visible_tasks = [
            parish_task
            for parish_task in sorted_tasks
            if not parish_task.get('done')
        ]

    selected_event_id = request.GET.get('event', '')
    selected_task_id = request.GET.get('task', '')
    selected_event = next(
        (
            parish_event
            for parish_event in parish_events
            if parish_event.get('id') == selected_event_id
        ),
        None,
    )
    selected_task = next(
        (
            parish_task
            for parish_task in parish_tasks
            if parish_task.get('id') == selected_task_id
        ),
        None,
    )
    selected_day_events = events_by_date.get(selected_date, [])
    selected_day_tasks = tasks_by_date.get(selected_date, [])

    return {
        'rows': visible_tasks,
        'parish_events': parish_events,
        'cal_year': calendar_year,
        'cal_month': calendar_month,
        'cal_prev': previous_period,
        'cal_next': next_period,
        'cal_prev_date': (
            f"{previous_period['year']}-{previous_period['month']:02d}-01"
        ),
        'cal_next_date': (
            f"{next_period['year']}-{next_period['month']:02d}-01"
        ),
        'cal_cells': _calendar_cells(calendar_year, calendar_month),
        'filter_date': selected_date,
        'lit_month_days': liturgical_month_days,
        'lit_day': liturgical_service.get_day(selected_date),
        'day_events': selected_day_events,
        'day_tasks': selected_day_tasks,
        'day_item_count': len(selected_day_events) + len(selected_day_tasks),
        'calendar_counts': {
            calendar_date: {
                'events': len(events_by_date.get(calendar_date, [])),
                'tasks': len(tasks_by_date.get(calendar_date, [])),
            }
            for calendar_date in set(events_by_date) | set(tasks_by_date)
        },
        'calendar_conflicts': _calendar_conflicts(parish_events),
        'tasks': sorted_tasks,
        'task_status_filter': task_status_filter,
        'selected_event': selected_event,
        'selected_task': selected_task,
        'calendar_stats': {
            'open_tasks': sum(
                1 for parish_task in parish_tasks
                if not parish_task.get('done')
            ),
            'overdue_tasks': sum(
                1
                for parish_task in parish_tasks
                if not parish_task.get('done')
                and (parish_task.get('due') or '') < today.isoformat()
            ),
            'month_events': sum(
                1
                for parish_event in parish_events
                if (parish_event.get('date') or '').startswith(
                    f'{calendar_year}-{calendar_month:02d}'
                )
            ),
        },
    }
