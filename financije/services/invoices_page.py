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
    return [
        invoice for invoice in data.get('invoices', [])
        if invoice.get('direction') != 'outgoing'
    ]


def summarize_invoices(data: dict, year_filter: str) -> dict:
    rows = incoming_invoices(data)
    if year_filter and year_filter != 'all':
        rows = [
            invoice for invoice in rows
            if str(invoice.get('issueDate') or '').startswith(str(year_filter))
        ]
    open_rows = [
        invoice for invoice in rows
        if invoice.get('status') not in ('placen', 'storno')
    ]
    unpaid = sum(
        max(
            0,
            float(invoice.get('total') or 0)
            - float(invoice.get('paidAmount') or 0),
        )
        for invoice in open_rows
    )
    paid = sum(
        float(invoice.get('total') or 0)
        for invoice in rows
        if invoice.get('status') == 'placen'
    )
    today_iso = date.today().isoformat()
    overdue_rows = [
        invoice for invoice in open_rows
        if invoice.get('dueDate') and invoice['dueDate'] < today_iso
    ]
    overdue_sum = sum(
        max(
            0,
            float(invoice.get('total') or 0)
            - float(invoice.get('paidAmount') or 0),
        )
        for invoice in overdue_rows
    )
    return {
        'count': len(rows),
        'open': len(open_rows),
        'unpaid_sum': unpaid,
        'paid_sum': paid,
        'overdue': len(overdue_rows),
        'overdue_sum': overdue_sum,
    }


def invoices_page_context(data: dict, request) -> dict:
    year = request.GET.get('year') or 'all'
    status = request.GET.get('status') or 'all'

    rows = [dict(invoice) for invoice in incoming_invoices(data)]
    if year != 'all':
        rows = [
            invoice for invoice in rows
            if str(invoice.get('issueDate') or '').startswith(str(year))
        ]
    if status != 'all':
        rows = [invoice for invoice in rows if invoice.get('status') == status]
    today_iso = date.today().isoformat()
    for invoice in rows:
        invoice['is_overdue'] = bool(
            invoice.get('status') not in ('placen', 'storno')
            and invoice.get('dueDate')
            and invoice['dueDate'] < today_iso
        )
    rows.sort(
        key=lambda invoice: (
            invoice.get('dueDate') or invoice.get('issueDate') or ''
        ),
        reverse=True,
    )

    years = sorted(
        {
            (invoice.get('issueDate') or '')[:4]
            for invoice in incoming_invoices(data)
            if invoice.get('issueDate')
        },
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
