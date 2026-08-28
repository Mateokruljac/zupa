"""Kontekst stranice podsjetnika."""
from __future__ import annotations

from ured.services.reminders import collect_reminders


def reminders_page_context(parish_data: dict, request) -> dict:
    all_reminders = collect_reminders(parish_data)
    selected_priority = request.GET.get('priority', 'all')
    selected_category = request.GET.get('category', 'all')
    search_term = request.GET.get('search', '').strip().casefold()

    visible_reminders = [
        reminder
        for reminder in all_reminders
        if (
            selected_priority == 'all'
            or reminder.get('priority') == selected_priority
        )
        and (
            selected_category == 'all'
            or reminder.get('category') == selected_category
        )
        and (
            not search_term
            or search_term in ' '.join((
                str(reminder.get('title') or ''),
                str(reminder.get('sub') or ''),
                str(reminder.get('category') or ''),
            )).casefold()
        )
    ]
    return {
        'reminders': visible_reminders,
        'reminder_count': len(all_reminders),
        'high_priority_reminder_count': sum(
            reminder.get('priority') == 'visoka'
            for reminder in all_reminders
        ),
        'reminder_categories': sorted({
            reminder.get('category')
            for reminder in all_reminders
            if reminder.get('category')
        }),
        'selected_reminder_priority': selected_priority,
        'selected_reminder_category': selected_category,
        'reminder_search_term': request.GET.get('search', '').strip(),
    }
