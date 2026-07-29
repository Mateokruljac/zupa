"""Stranica pastoralnih posjeta."""
from __future__ import annotations

from datetime import date


def visits_page_context(data: dict, request) -> dict:
    today = date.today().isoformat()
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
        enriched.append(row)

    return {
        'visits': enriched,
        'visit_stats': {
            'total': len(visits),
            'open': sum(1 for v in visits if not v.get('done')),
            'due': sum(1 for v in visits if not v.get('done') and (v.get('scheduled') or '') <= today),
        },
        'filter_status': filter_status,
        'families': data.get('families', []),
        'today': today,
    }
