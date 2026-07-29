"""Blagajna župe — agregacija (bivši cashbook-engine.js)."""
from __future__ import annotations

from datetime import date


def summarize_year(data: dict, year: int) -> dict:
    y = str(year)
    rows = [e for e in data.get('cashbook', []) if (e.get('date') or '').startswith(y)]
    in_sum = sum(float(e.get('amount') or 0) for e in rows if e.get('type') == 'ulaz')
    out_sum = sum(float(e.get('amount') or 0) for e in rows if e.get('type') != 'ulaz')
    by_category: dict[str, dict] = {}
    for e in rows:
        cat = e.get('category') or 'ostalo'
        if cat not in by_category:
            by_category[cat] = {'in': 0.0, 'out': 0.0}
        amt = float(e.get('amount') or 0)
        if e.get('type') == 'ulaz':
            by_category[cat]['in'] += amt
        else:
            by_category[cat]['out'] += amt
    inv_paid = sum(
        float(i.get('paidAmount') or i.get('total') or 0)
        for i in data.get('invoices', [])
        if i.get('direction') != 'outgoing'
        and (i.get('paidAt') or i.get('issueDate') or '').startswith(y)
        and i.get('status') == 'placen'
    )
    return {
        'in_sum': in_sum,
        'out_sum': out_sum,
        'balance': in_sum - out_sum,
        'by_category': by_category,
        'inv_paid': inv_paid,
        'count': len(rows),
    }


def cashbook_page_context(data: dict, request) -> dict:
    today = date.today()
    try:
        year = int(request.GET.get('year') or today.year)
    except ValueError:
        year = today.year
    ledger = request.GET.get('ledger') or 'sve'

    rows = [
        e for e in data.get('cashbook', [])
        if (e.get('date') or '').startswith(str(year))
    ]
    rows.sort(key=lambda e: e.get('date') or '', reverse=True)
    if ledger != 'sve':
        rows = [e for e in rows if (e.get('ledger') or 'plavi') == ledger]

    summary = summarize_year(data, year)
    years = sorted({(e.get('date') or '')[:4] for e in data.get('cashbook', []) if e.get('date')}, reverse=True)
    if str(year) not in years:
        years = [str(year)] + years

    return {
        'cashbook_year': year,
        'cashbook_ledger': ledger,
        'cashbook_rows': rows,
        'cashbook_summary': summary,
        'cashbook_years': [int(y) for y in years[:6] if y.isdigit()],
    }
