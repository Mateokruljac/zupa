"""Page context for the mass-intention workspace."""
from __future__ import annotations

from pastoral.services.dates import today_iso


def nakane_page_context(data: dict, request) -> dict:
    selected_date = request.GET.get('date') or today_iso()
    if selected_date == 'today':
        selected_date = today_iso()

    return {
        'nakane_bootstrap': {
            'intentions': data.get('intentions', []),
            'massSchedule': data.get('massSchedule', []),
            'massExceptions': data.get('massExceptions', []),
            'filterDate': selected_date,
        },
    }
