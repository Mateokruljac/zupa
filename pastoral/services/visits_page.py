"""Stranica pastoralnih posjeta."""
from __future__ import annotations

from datetime import date

from pastoral.services.dates import parse_iso_date


def visits_page_context(data: dict, request) -> dict:
    today_date = date.today()
    today = today_date.isoformat()
    visits = sorted(
        data.get('visits', []),
        key=lambda visit: (
            visit.get('done'),
            visit.get('scheduled') or '9999',
        ),
    )
    filter_status = request.GET.get('status', 'open')
    if filter_status == 'done':
        visible_visits = [visit for visit in visits if visit.get('done')]
    elif filter_status == 'all':
        visible_visits = visits
    else:
        visible_visits = [visit for visit in visits if not visit.get('done')]

    families_by_id = {
        family.get('id'): family
        for family in data.get('families', [])
    }
    enriched_visits = []
    for visit in visible_visits:
        enriched_visit = dict(visit)
        family = families_by_id.get(enriched_visit.get('familyId'))
        if family:
            enriched_visit.setdefault('familySurname', family.get('surname', ''))
            enriched_visit.setdefault('address', family.get('address', ''))
        scheduled_date = parse_iso_date(enriched_visit.get('scheduled'))
        enriched_visit['isOverdue'] = bool(
            not enriched_visit.get('done')
            and scheduled_date
            and scheduled_date < today_date
        )
        enriched_visit['daysOverdue'] = (
            (today_date - scheduled_date).days
            if enriched_visit['isOverdue']
            else 0
        )
        enriched_visit['needsReport'] = bool(
            enriched_visit.get('done')
            and not (enriched_visit.get('report') or '').strip()
        )
        enriched_visits.append(enriched_visit)

    open_visits = [visit for visit in visits if not visit.get('done')]
    overdue = [
        visit for visit in open_visits
        if (scheduled := parse_iso_date(visit.get('scheduled'))) and scheduled < today_date
    ]
    reports_missing = [
        visit
        for visit in visits
        if visit.get('done') and not (visit.get('report') or '').strip()
    ]

    return {
        'visits': enriched_visits,
        'visit_stats': {
            'total': len(visits),
            'open': len(open_visits),
            'due': len(overdue),
            'reports_missing': len(reports_missing),
            'communion': sum(
                1
                for visit in open_visits
                if visit.get('type') == 'kucna-pricest'
            ),
        },
        'filter_status': filter_status,
        'families': data.get('families', []),
        'today': today,
    }
