"""Ulazni računi — kontekst stranice (bivši invoices-engine.js)."""
from __future__ import annotations

from datetime import date


STATUS_LABELS = {
    'nacrt': 'Nacrt',
    'primljen': 'Primljen',
    'djelomicno': 'Djelomično plaćen',
    'placen': 'Plaćen',
    'storno': 'Storno',
}

CATEGORY_LABELS = {
    'režije': 'Režije',
    'dobavljaci': 'Dobavljači',
    'dz': 'Biskupija / DŽ',
    'ostalo': 'Ostalo',
}


def incoming_invoices(data: dict) -> list[dict]:
    return [i for i in data.get('invoices', []) if i.get('direction') != 'outgoing']


def summarize_invoices(data: dict, year_filter: str) -> dict:
    rows = incoming_invoices(data)
    if year_filter and year_filter != 'all':
        rows = [i for i in rows if str(i.get('issueDate') or '').startswith(str(year_filter))]
    open_rows = [i for i in rows if i.get('status') not in ('placen', 'storno')]
    unpaid = sum(
        max(0, float(i.get('total') or 0) - float(i.get('paidAmount') or 0))
        for i in open_rows
    )
    paid = sum(float(i.get('total') or 0) for i in rows if i.get('status') == 'placen')
    return {'count': len(rows), 'open': len(open_rows), 'unpaid_sum': unpaid, 'paid_sum': paid}


def invoices_page_context(data: dict, request) -> dict:
    year = request.GET.get('year') or 'all'
    status = request.GET.get('status') or 'all'

    rows = incoming_invoices(data)
    if year != 'all':
        rows = [i for i in rows if str(i.get('issueDate') or '').startswith(str(year))]
    if status != 'all':
        rows = [i for i in rows if i.get('status') == status]
    rows.sort(key=lambda i: i.get('dueDate') or i.get('issueDate') or '', reverse=True)

    years = sorted(
        {(i.get('issueDate') or '')[:4] for i in incoming_invoices(data) if i.get('issueDate')},
        reverse=True,
    )
    if not years:
        years = [str(date.today().year)]

    return {
        'invoice_rows': rows,
        'invoice_filters': {'year': year, 'status': status},
        'invoice_years': years,
        'invoice_summary': summarize_invoices(data, year),
        'invoice_status_labels': STATUS_LABELS,
        'invoice_category_labels': CATEGORY_LABELS,
    }
