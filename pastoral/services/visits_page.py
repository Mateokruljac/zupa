"""Stranica pastoralnih posjeta."""
from __future__ import annotations

from datetime import date

from pastoral.services.dates import parse_iso_date


def visits_page_context(data: dict, request) -> dict:
    today_date = date.today()
    today = today_date.isoformat()
    visits = sorted(
        data.get('visits', []),
        key=lambda v: (v.get('done'), v.get('scheduled') or '9999'),
    )
    filter_status = request.GET.get('status', 'open')
    if filter_status == 'done':
        visible = [v for v in visits if v.get('done')]
    elif filter_status == 'all':
        visible = visits
    else:
        visible = [v for v in visits if not v.get('done')]

    families = {f.get('id'): f for f in data.get('families', [])}
    enriched = []
    for v in visible:
        row = dict(v)
        fam = families.get(row.get('familyId'))
        if fam:
            row.setdefault('familySurname', fam.get('surname', ''))
            row.setdefault('address', fam.get('address', ''))
        scheduled = parse_iso_date(row.get('scheduled'))
        row['isOverdue'] = bool(not row.get('done') and scheduled and scheduled < today_date)
        row['daysOverdue'] = (today_date - scheduled).days if row['isOverdue'] else 0
        row['needsReport'] = bool(row.get('done') and not (row.get('report') or '').strip())
        enriched.append(row)

    open_visits = [v for v in visits if not v.get('done')]
    overdue = [
        visit for visit in open_visits
        if (scheduled := parse_iso_date(visit.get('scheduled'))) and scheduled < today_date
    ]
    reports_missing = [v for v in visits if v.get('done') and not (v.get('report') or '').strip()]

    return {
        'visits': enriched,
        'visit_stats': {
            'total': len(visits),
            'open': len(open_visits),
            'due': len(overdue),
            'reports_missing': len(reports_missing),
            'communion': sum(1 for v in open_visits if v.get('type') == 'kucna-pricest'),
        },
        'filter_status': filter_status,
        'families': data.get('families', []),
        'today': today,
    }
