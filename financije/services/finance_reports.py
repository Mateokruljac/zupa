"""MVP financijski pregled — župni saldo iz knjige crkvenih računa."""
from __future__ import annotations

from datetime import date

from financije.ledgers import LEDGERS, PARISH_BALANCE_LEDGER
from financije.services.cashbook import summarize_year
from financije.services.debts import collect_payables, collect_receivables
from financije.services.invoices_page import summarize_invoices


def finance_reports_context(data: dict, request) -> dict:
    today = date.today()
    try:
        year = int(request.GET.get('year') or today.year)
    except ValueError:
        year = today.year
    year_summary = summarize_year(data, year, PARISH_BALANCE_LEDGER)
    category_rows = [
        {'label': category, 'in': values['in'], 'out': values['out']}
        for category, values in year_summary.get('by_category', {}).items()
    ]
    category_rows.sort(
        key=lambda category: category['in'] + category['out'],
        reverse=True,
    )
    receivable_rows = collect_receivables(data, only_unpaid=True)
    payable_rows = collect_payables(data, only_unpaid=True)
    years = sorted({
        (entry.get('date') or '')[:4]
        for entry in data.get('cashbook', [])
        if (entry.get('date') or '')[:4].isdigit()
    }, reverse=True)
    if str(year) not in years:
        years.insert(0, str(year))

    other_books = []
    for book in LEDGERS:
        if book['id'] == PARISH_BALANCE_LEDGER:
            continue
        summary = summarize_year(data, year, book['id'])
        other_books.append({
            **book,
            'balance': summary['balance'],
            'count': summary['count'],
        })

    return {
        'report_year': year,
        'report_years': [int(year_value) for year_value in years[:6]],
        'year_summary': year_summary,
        'invoice_summary': summarize_invoices(data, str(year)),
        'finance_obligations': {
            'receivable_count': len(receivable_rows),
            'receivable_sum': sum(
                float(receivable.get('amount') or 0)
                for receivable in receivable_rows
            ),
            'payable_count': len(payable_rows),
            'payable_sum': sum(
                float(payable.get('amount') or 0)
                for payable in payable_rows
            ),
        },
        'finance_categories': category_rows,
        'other_account_books': other_books,
    }
