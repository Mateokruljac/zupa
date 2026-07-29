"""Javne prijave — pregled i uvoz u evidenciju."""
from __future__ import annotations

from datetime import date

FORM_LABELS = {
    'prijava-krizma': 'Krizma',
    'prijava-krsenje': 'Krštenje',
    'prijava-pricest': 'Prva pričest',
    'prijava-ukop': 'Ukop / pogreb',
}


def public_submissions_context(data: dict, request) -> dict:
    status = request.GET.get('status') or 'all'
    rows = list(data.get('publicSubmissions', []))
    if status == 'nova':
        rows = [r for r in rows if r.get('status') == 'nova']
    elif status == 'preuzeto':
        rows = [r for r in rows if r.get('status') == 'preuzeto']
    rows.sort(key=lambda r: r.get('submittedAt') or '', reverse=True)

    nova_count = sum(1 for r in data.get('publicSubmissions', []) if r.get('status') == 'nova')

    return {
        'submission_rows': rows,
        'submission_filters': {'status': status},
        'submission_nova_count': nova_count,
        'form_labels': FORM_LABELS,
        'import_year': int(request.GET.get('year') or date.today().year),
    }
