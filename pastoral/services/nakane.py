"""Misne nakane — filtriranje i statistika (server-side)."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from pastoral.forms import IntentionForm
from pastoral.services.mass_schedule import get_masses_for_date


def today_iso() -> str:
    return date.today().isoformat()


def intentions_for_date(intentions: list, iso: str) -> list:
    return sorted(
        [n for n in intentions if n.get('date') == iso],
        key=lambda n: n.get('massTime') or '',
    )


def nakane_stats(intentions: list) -> dict:
    today = today_iso()
    unpaid = [n for n in intentions if not n.get('paid') and float(n.get('stipend') or 0) > 0]
    today_list = intentions_for_date(intentions, today)
    return {
        'total': len(intentions),
        'today_count': len(today_list),
        'today_unpaid': sum(1 for n in today_list if not n.get('paid')),
        'unpaid_total': len(unpaid),
        'unpaid_amount': sum(float(n.get('stipend') or 0) for n in unpaid),
    }


def filter_intentions(intentions: list, request) -> tuple[list, dict]:
    q = (request.GET.get('q') or '').strip().lower()
    status = request.GET.get('status', '')
    filter_date = request.GET.get('date', '')
    if filter_date == 'today':
        filter_date = today_iso()

    rows = list(intentions)
    if filter_date:
        rows = [n for n in rows if n.get('date') == filter_date]
    if status == 'unpaid':
        rows = [n for n in rows if not n.get('paid')]
    elif status == 'paid':
        rows = [n for n in rows if n.get('paid')]
    if q:
        rows = [
            n for n in rows
            if q in (n.get('intentionFor') or '').lower()
            or q in (n.get('requestedBy') or '').lower()
            or q in (n.get('massTime') or '').lower()
        ]
    rows.sort(key=lambda n: (n.get('date') or '9999', n.get('massTime') or ''))
    filters = {'q': request.GET.get('q', ''), 'status': status, 'date': filter_date}
    return rows, filters


def month_calendar(year: int, month: int) -> list[str | None]:
    """Grid of ISO dates for calendar (Mon-first), None = empty cell."""
    first = date(year, month, 1)
    start_offset = (first.weekday())  # Mon=0
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    cells: list[str | None] = [None] * start_offset
    d = first
    while d <= last_day:
        cells.append(d.isoformat())
        d += timedelta(days=1)
    while len(cells) % 7:
        cells.append(None)
    return cells


def intentions_by_date(intentions: list) -> dict[str, list]:
    out: dict[str, list] = {}
    for n in intentions:
        iso = n.get('date')
        if not iso:
            continue
        out.setdefault(iso, []).append(n)
    for iso in out:
        out[iso].sort(key=lambda x: x.get('massTime') or '')
    return out


def _time_to_mins(t: str) -> int:
    parts = str(t or '0:0').split(':')
    return int(parts[0]) * 60 + int(parts[1] if len(parts) > 1 else 0)


def next_mass_hint(data: dict, iso: str, day_intentions: list) -> str:
    today = today_iso()
    if iso != today:
        return ''
    masses = get_masses_for_date(data, iso)
    times = [m['time'] for m in masses if m.get('time')]
    if not times:
        times = ['07:30', '09:00', '11:00', '18:00', '18:30']
    now_mins = datetime.now().hour * 60 + datetime.now().minute
    upcoming = sorted(
        [t for t in times if _time_to_mins(t) >= now_mins - 30],
        key=_time_to_mins,
    )
    if not upcoming:
        return 'Sve mise za danas su prošle.'
    mass_time = upcoming[0]
    count = sum(1 for n in day_intentions if n.get('massTime') == mass_time)
    return f'Sljedeća misa: {mass_time} — {count} nakana'


def evidence_stats(intentions: list) -> dict:
    total = len(intentions)
    paid = sum(1 for n in intentions if n.get('paid'))
    unpaid = total - paid
    paid_pct = round(paid / total * 100) if total else 0
    stipend_total = sum(float(n.get('stipend') or 0) for n in intentions)
    stipend_unpaid = sum(float(n.get('stipend') or 0) for n in intentions if not n.get('paid'))
    today = date.today()
    last6 = []
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        while m < 1:
            m += 12
            y -= 1
        mk = f'{y}-{m:02d}'
        months_hr = ['sij', 'velj', 'ožu', 'tra', 'svi', 'lip', 'srp', 'kol', 'ruj', 'lis', 'stu', 'pro']
        last6.append({
            'label': months_hr[m - 1],
            'count': sum(1 for n in intentions if (n.get('date') or '').startswith(mk)),
        })
    return {
        'total': total,
        'paid': paid,
        'unpaid': unpaid,
        'paid_pct': paid_pct,
        'stipend_total': stipend_total,
        'stipend_unpaid': stipend_unpaid,
        'last6': last6,
    }


def nakane_page_context(data: dict, request) -> dict:
    intentions = data.get('intentions', [])
    filter_date = request.GET.get('date', today_iso())
    if filter_date == 'today':
        filter_date = today_iso()
    try:
        cal_year = int(request.GET.get('year', filter_date[:4]))
        cal_month = int(request.GET.get('month', filter_date[5:7]))
    except (ValueError, IndexError):
        cal_year = date.today().year
        cal_month = date.today().month
    cal_month = max(1, min(12, cal_month))

    filtered, filters = filter_intentions(intentions, request)
    if not filters.get('date'):
        filters['date'] = filter_date

    prev_month = cal_month - 1
    prev_year = cal_year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1
    next_month = cal_month + 1
    next_year = cal_year
    if next_month > 12:
        next_month = 1
        next_year += 1

    day_list = intentions_for_date(intentions, filter_date)
    try:
        initial_date = date.fromisoformat(filter_date)
    except ValueError:
        initial_date = date.today()

    return {
        'intentions': intentions,
        'filtered_intentions': filtered,
        'nakane_filters': filters,
        'nakane_stats': nakane_stats(intentions),
        'nakane_evidence': evidence_stats(intentions),
        'filter_date': filter_date,
        'day_intentions': day_list,
        'next_mass_hint': next_mass_hint(data, filter_date, day_list),
        'mass_schedule': data.get('massSchedule', []),
        'cal_year': cal_year,
        'cal_month': cal_month,
        'cal_cells': month_calendar(cal_year, cal_month),
        'intentions_by_date': intentions_by_date(intentions),
        'cal_prev': {'year': prev_year, 'month': prev_month},
        'cal_next': {'year': next_year, 'month': next_month},
        'intention_form': IntentionForm(initial={'date': initial_date}),
        'nakane_bootstrap': {
            'intentions': intentions,
            'massSchedule': data.get('massSchedule', []),
            'filterDate': filter_date,
        },
    }
