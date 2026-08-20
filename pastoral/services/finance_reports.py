"""MVP financijski pregled temeljen isključivo na evidentiranim podacima."""
from __future__ import annotations

from datetime import date

from pastoral.services.cashbook import summarize_year
from pastoral.services.debts import collect_payables, collect_receivables
from pastoral.services.invoices_page import summarize_invoices


def quarter_summary(data: dict, year: int, quarter: int) -> dict:
    start_month = (quarter - 1) * 3 + 1
    end_month = quarter * 3
    rows = [
        entry for entry in data.get('cashbook', [])
        if (entry.get('ledger') or 'plavi') == 'plavi'
        and _month_in_range(
            entry.get('date'),
            year,
            start_month,
            end_month,
        )
    ]
    income_sum = sum(
        float(entry.get('amount') or 0)
        for entry in rows
        if entry.get('type') == 'ulaz'
    )
    expense_sum = sum(
        float(entry.get('amount') or 0)
        for entry in rows
        if entry.get('type') != 'ulaz'
    )
    return {
        'in_sum': income_sum,
        'out_sum': expense_sum,
        'balance': income_sum - expense_sum,
        'count': len(rows),
    }


def _month_in_range(
    iso_date: str | None,
    year: int,
    start_month: int,
    end_month: int,
) -> bool:
    if not iso_date or len(iso_date) < 7:
        return False
    try:
        entry_year = int(iso_date[:4])
        entry_month = int(iso_date[5:7])
    except ValueError:
        return False
    return (
        entry_year == year
        and start_month <= entry_month <= end_month
    )


def finance_reports_context(data: dict, request) -> dict:
    today = date.today()
    try:
        year = int(request.GET.get('year') or today.year)
    except ValueError:
        year = today.year
    year_summary = summarize_year(data, year)
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
    }
