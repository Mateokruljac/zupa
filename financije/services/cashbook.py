"""Blagajna župe — agregacija po službenim knjigama računa."""
from __future__ import annotations

from datetime import date

from financije.ledgers import (
    LEDGER_CRKVENI,
    LEDGERS,
    PARISH_BALANCE_LEDGER,
    entry_ledger,
    normalize_ledger,
)


def _year_entries(data: dict, year: int) -> list[dict]:
    prefix = str(year)
    return [
        entry
        for entry in data.get('cashbook', [])
        if (entry.get('date') or '').startswith(prefix)
    ]


def summarize_entries(rows: list[dict]) -> dict:
    in_sum = sum(float(entry.get('amount') or 0) for entry in rows if entry.get('type') == 'ulaz')
    out_sum = sum(float(entry.get('amount') or 0) for entry in rows if entry.get('type') != 'ulaz')
    by_category: dict[str, dict] = {}
    for entry in rows:
        category = entry.get('category') or 'ostalo'
        if category not in by_category:
            by_category[category] = {'in': 0.0, 'out': 0.0}
        amount = float(entry.get('amount') or 0)
        if entry.get('type') == 'ulaz':
            by_category[category]['in'] += amount
        else:
            by_category[category]['out'] += amount
    return {
        'in_sum': in_sum,
        'out_sum': out_sum,
        'balance': in_sum - out_sum,
        'by_category': by_category,
        'count': len(rows),
    }


def filter_ledger(rows: list[dict], ledger: str) -> list[dict]:
    wanted = normalize_ledger(ledger)
    return [entry for entry in rows if entry_ledger(entry) == wanted]


def summarize_year(
    data: dict,
    year: int,
    ledger: str = PARISH_BALANCE_LEDGER,
) -> dict:
    return summarize_entries(filter_ledger(_year_entries(data, year), ledger))


def cashbook_page_context(data: dict, request) -> dict:
    today = date.today()
    try:
        year = int(request.GET.get('year') or today.year)
    except ValueError:
        year = today.year
    ledger = normalize_ledger(request.GET.get('ledger') or LEDGER_CRKVENI)

    year_rows = _year_entries(data, year)
    year_rows.sort(key=lambda entry: entry.get('date') or '', reverse=True)
    rows = filter_ledger(year_rows, ledger)

    years = sorted(
        {
            (entry.get('date') or '')[:4]
            for entry in data.get('cashbook', [])
            if entry.get('date')
        },
        reverse=True,
    )
    if str(year) not in years:
        years = [str(year)] + years

    current_book = next(book for book in LEDGERS if book['id'] == ledger)
    return {
        'cashbook_year': year,
        'cashbook_ledger': ledger,
        'cashbook_book': current_book,
        'cashbook_books': LEDGERS,
        'cashbook_rows': rows,
        'cashbook_summary': summarize_entries(rows),
        'cashbook_years': [int(year_value) for year_value in years[:6] if year_value.isdigit()],
        'open_donation_dialog': request.GET.get('donate') == '1',
    }
