"""Uređivanje i uklanjanje događaja i zadataka župnog kalendara."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages

from pastoral.forms import EventForm, TaskForm

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


def _find_record(records: list[dict], record_id: str) -> dict | None:
    return next(
        (
            record
            for record in records
            if record.get('id') == record_id
        ),
        None,
    )


def _event_conflicts(
    parish_events: list[dict],
    event_id: str,
    event_date: str,
    event_time: str,
    event_place: str,
) -> bool:
    if not event_time or not event_place:
        return False
    return any(
        parish_event.get('id') != event_id
        and parish_event.get('date') == event_date
        and parish_event.get('time') == event_time
        and (parish_event.get('place') or '').casefold()
        == event_place.casefold()
        for parish_event in parish_events
    )


def _update_calendar_event(
    request,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> None:
    event_form = EventForm(request.POST)
    event_id = request.POST.get('event_id', '')
    parish_events = parish_data.get('events', [])
    selected_event = _find_record(parish_events, event_id)
    if not selected_event:
        messages.error(request, 'Događaj nije pronađen.')
        return
    if not event_form.is_valid():
        messages.error(request, 'Provjerite podatke događaja.')
        return

    cleaned_data = event_form.cleaned_data
    event_date = cleaned_data['event_date'].isoformat()
    event_time = (
        cleaned_data['event_time'].strftime('%H:%M')
        if cleaned_data.get('event_time')
        else ''
    )
    event_place = cleaned_data.get('place') or ''
    if _event_conflicts(
        parish_events,
        event_id,
        event_date,
        event_time,
        event_place,
    ):
        messages.error(
            request,
            'U istom prostoru već postoji događaj u odabranom terminu.',
        )
        return

    selected_event.update({
        'title': cleaned_data['title'],
        'date': event_date,
        'time': event_time,
        'place': event_place,
        'type': cleaned_data['event_type'],
        'owner': cleaned_data['owner'],
        'notes': cleaned_data.get('notes') or '',
    })
    parish_data_service.save(parish_data)
    messages.success(request, 'Događaj je spremljen.')


def _update_calendar_task(
    request,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> None:
    task_form = TaskForm(request.POST)
    selected_task = _find_record(
        parish_data.get('tasks', []),
        request.POST.get('task_id', ''),
    )
    if not selected_task:
        messages.error(request, 'Zadatak nije pronađen.')
        return
    if not task_form.is_valid():
        messages.error(request, 'Provjerite podatke zadatka.')
        return

    cleaned_data = task_form.cleaned_data
    selected_task.update({
        'title': cleaned_data['title'],
        'owner': cleaned_data['owner'],
        'due': (
            cleaned_data['due'].isoformat()
            if cleaned_data.get('due')
            else ''
        ),
        'priority': cleaned_data['priority'],
        'category': cleaned_data.get('category') or 'ured',
    })
    parish_data_service.save(parish_data)
    messages.success(request, 'Zadatak je spremljen.')


def handle_calendar_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
    if page_slug != 'kalendar':
        return False

    if action_name == 'update_event':
        _update_calendar_event(request, parish_data, parish_data_service)
        return True

    if action_name == 'delete_event':
        event_id = request.POST.get('event_id', '')
        parish_data['events'] = [
            parish_event
            for parish_event in parish_data.get('events', [])
            if parish_event.get('id') != event_id
        ]
        parish_data_service.save(parish_data)
        messages.success(request, 'Događaj je obrisan.')
        return True

    if action_name == 'update_task':
        _update_calendar_task(request, parish_data, parish_data_service)
        return True

    if action_name == 'delete_task':
        task_id = request.POST.get('task_id', '')
        parish_data['tasks'] = [
            parish_task
            for parish_task in parish_data.get('tasks', [])
            if parish_task.get('id') != task_id
        ]
        parish_data_service.save(parish_data)
        messages.success(request, 'Zadatak je obrisan.')
        return True

    return False
