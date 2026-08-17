"""Javne prijave — pregled i uvoz u evidenciju."""
from __future__ import annotations

from datetime import date, datetime

FORM_LABELS = {
    'prijava-krizma': 'Krizma',
    'prijava-krsenje': 'Krštenje',
    'prijava-pricest': 'Prva pričest',
    'prijava-ukop': 'Ukop / pogreb',
}


def public_submissions_context(data: dict, request) -> dict:
    status = request.GET.get('status') or 'all'
    form_type = request.GET.get('type') or ''
    q = (request.GET.get('q') or '').strip().casefold()
    rows = list(data.get('publicSubmissions', []))
    if status == 'nova':
        rows = [r for r in rows if r.get('status') == 'nova']
    elif status == 'preuzeto':
        rows = [r for r in rows if r.get('status') == 'preuzeto']
    if form_type:
        rows = [r for r in rows if (r.get('formType') or r.get('type')) == form_type]
    if q:
        rows = [
            row for row in rows
            if any(q in str(row.get(key) or '').casefold() for key in ('name', 'phone', 'email', 'address'))
            or any(q in str(field.get('value') or '').casefold() for field in row.get('displayFields', []))
        ]

    today = date.today()
    street_names = [(street.get('name') or '').casefold() for street in data.get('streets', []) if street.get('name')]
    known_names = {
        str(value).strip().casefold()
        for collection, key in (
            ('baptisms', 'childName'), ('weddings', 'couple'), ('funerals', 'deceased'), ('anointing', 'person')
        )
        for row in data.get(collection, [])
        for value in [row.get(key)] if value
    }
    enriched = []
    for original in rows:
        row = dict(original)
        try:
            submitted = datetime.fromisoformat(str(row.get('submittedAt', '')).replace('Z', '+00:00')).date()
        except (TypeError, ValueError):
            submitted = None
        row['ageDays'] = max(0, (today - submitted).days) if submitted else None
        row['hasContact'] = bool(row.get('phone') or row.get('email'))
        address = (row.get('address') or (row.get('data') or {}).get('adresa') or '').casefold()
        row['jurisdictionKnown'] = bool(address and any(name in address for name in street_names))
        row['possibleDuplicate'] = bool((row.get('name') or '').strip().casefold() in known_names)
        row['triageReady'] = bool(row.get('consentGranted') and row['hasContact'] and row['jurisdictionKnown'] and not row['possibleDuplicate'])
        enriched.append(row)
    rows = sorted(enriched, key=lambda row: (row.get('status') != 'nova', row.get('submittedAt') or ''))

    nova_count = sum(1 for r in data.get('publicSubmissions', []) if r.get('status') == 'nova')

    return {
        'submission_rows': rows,
        'submission_filters': {'status': status, 'type': form_type, 'q': request.GET.get('q', '')},
        'submission_nova_count': nova_count,
        'form_labels': FORM_LABELS,
        'submission_form_types': sorted({r.get('formType') or r.get('type') for r in data.get('publicSubmissions', []) if r.get('formType') or r.get('type')}),
        'import_year': int(request.GET.get('year') or date.today().year),
    }
