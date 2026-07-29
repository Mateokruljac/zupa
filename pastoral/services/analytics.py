"""Analitika nadzorne ploče — statistika (iz analytics-engine.js)."""
from __future__ import annotations

from datetime import date

from pastoral.services.dates import month_key
from pastoral.services.debts import collect_debts, cat_meta


def compute_cashbook_months(data: dict, months: int = 6) -> list[dict]:
    today = date.today()
    rows = []
    for i in range(months - 1, -1, -1):
        m = today.month - i
        y = today.year
        while m < 1:
            m += 12
            y -= 1
        mk = f'{y}-{m:02d}'
        entries = [e for e in data.get('cashbook') or [] if (e.get('date') or '').startswith(mk)]
        label = date(y, m, 1).strftime('%b')
        rows.append({
            'label': label,
            'in': sum(float(e.get('amount') or 0) for e in entries if e.get('type') == 'ulaz'),
            'out': sum(float(e.get('amount') or 0) for e in entries if e.get('type') == 'izlaz'),
        })
    return rows


def compute_debt_categories(data: dict) -> list[dict]:
    rows = collect_debts(data, only_unpaid=True)
    counts: dict[str, int] = {}
    for r in rows:
        cat = r.get('category') or 'ostalo'
        counts[cat] = counts.get(cat, 0) + 1
    return [
        {'id': cid, 'label': cat_meta(cid, 'receivable').get('label', cid), 'count': n}
        for cid, n in counts.items()
    ]


def compute_stats(data: dict) -> dict:
    today = date.today()
    mk = month_key(today)
    intentions = data.get('intentions') or []
    intentions_month = [n for n in intentions if (n.get('date') or '').startswith(mk)]
    paid_month = sum(1 for n in intentions_month if n.get('paid'))
    stipend_sum = sum(float(n.get('stipend') or 0) for n in intentions_month)
    year = today.year
    conf = next((c for c in data.get('confirmations') or [] if c.get('year') == year), None)
    if not conf and data.get('confirmations'):
        conf = data['confirmations'][0]

    last6 = []
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        while m < 1:
            m += 12
            y -= 1
        key = f'{y}-{m:02d}'
        last6.append({
            'label': date(y, m, 1).strftime('%b'),
            'count': sum(1 for n in intentions if (n.get('date') or '').startswith(key)),
        })

    lukno_paid = lukno_unpaid = 0
    donation_year = 0.0
    for fam in data.get('families') or []:
        row = next((c for c in fam.get('contributions') or [] if c.get('year') == year), None)
        if row:
            if row.get('luknoPaid'):
                lukno_paid += 1
            else:
                lukno_unpaid += 1
            donation_year += float(row.get('churchDonation') or 0)

    return {
        'intentionsMonth': len(intentions_month),
        'paidPct': round(paid_month / len(intentions_month) * 100) if intentions_month else 0,
        'stipendSum': stipend_sum,
        'sacramentCounts': {
            'krštenja': len(data.get('baptisms') or []),
            'vjenčanja': len(data.get('weddings') or []),
            'pogrebi': len(data.get('funerals') or []),
            'krizmanici': len((conf or {}).get('candidates') or []),
        },
        'last6': last6,
        'luknoPaid': lukno_paid,
        'luknoUnpaid': lukno_unpaid,
        'donationYear': donation_year,
        'cashbookMonths': compute_cashbook_months(data),
        'debtCategories': compute_debt_categories(data),
    }
