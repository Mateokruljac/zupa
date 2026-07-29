"""Financijska izvješća — kvartalni/godišnji pregled (bivši finance-advanced-engine.js)."""
from __future__ import annotations

from datetime import date

from pastoral.services.analytics import compute_stats
from pastoral.services.cashbook import summarize_year


def quarter_summary(data: dict, year: int, quarter: int) -> dict:
    start_m = (quarter - 1) * 3 + 1
    end_m = quarter * 3
    rows = [
        e for e in data.get('cashbook', [])
        if (e.get('ledger') or 'plavi') == 'plavi'
        and _month_in_range(e.get('date'), year, start_m, end_m)
    ]
    in_sum = sum(float(e.get('amount') or 0) for e in rows if e.get('type') == 'ulaz')
    out_sum = sum(float(e.get('amount') or 0) for e in rows if e.get('type') != 'ulaz')
    return {'in_sum': in_sum, 'out_sum': out_sum, 'balance': in_sum - out_sum, 'count': len(rows)}


def _month_in_range(iso: str | None, year: int, start_m: int, end_m: int) -> bool:
    if not iso or len(iso) < 7:
        return False
    try:
        y = int(iso[:4])
        m = int(iso[5:7])
    except ValueError:
        return False
    return y == year and start_m <= m <= end_m


def finance_reports_context(data: dict, request) -> dict:
    today = date.today()
    try:
        year = int(request.GET.get('year') or today.year)
    except ValueError:
        year = today.year
    try:
        quarter = int(request.GET.get('q') or ((today.month - 1) // 3 + 1))
    except ValueError:
        quarter = 1
    quarter = max(1, min(4, quarter))

    return {
        'report_year': year,
        'report_quarter': quarter,
        'year_summary': summarize_year(data, year),
        'quarter_summary': quarter_summary(data, year, quarter),
        'stats': compute_stats(data),
    }
