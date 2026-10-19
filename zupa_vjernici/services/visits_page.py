"""Stranica pastoralnih posjeta."""
from __future__ import annotations

from datetime import date
from urllib.parse import urlencode

from pastoral.services.dates import parse_iso_date

VISIT_PAGE_SIZE = 15

VISIT_TYPE_LABELS = {
    'obitelj': 'Pastoralni posjet',
    'kucna-pricest': 'Kućna pričest',
    'bolnica': 'Bolesnik',
    'ostalo': 'Ostalo',
}

VISIT_FILTERS = (
    ('open', 'Otvoreni'),
    ('overdue', 'Prošao termin'),
    ('needs_report', 'Bez napomene'),
    ('done', 'Obavljeni'),
    ('all', 'Svi'),
)


def _visit_query(**params) -> str:
    cleaned = {
        key: value
        for key, value in params.items()
        if value not in (None, '')
    }
    return urlencode(cleaned)


def _visible_pages(current_page: int, page_count: int) -> list[int | None]:
    if page_count <= 7:
        return list(range(1, page_count + 1))
    pages: list[int | None] = [1]
    window_start = max(2, current_page - 1)
    window_end = min(page_count - 1, current_page + 1)
    if window_start > 2:
        pages.append(None)
    pages.extend(range(window_start, window_end + 1))
    if window_end < page_count - 1:
        pages.append(None)
    pages.append(page_count)
    return pages


def paginate_visits(
    visits: list[dict],
    page_number: object,
    *,
    page_size: int = VISIT_PAGE_SIZE,
) -> dict:
    total = len(visits)
    page_count = max(1, (total + page_size - 1) // page_size) if total else 1
    try:
        current_page = int(page_number or 1)
    except (TypeError, ValueError):
        current_page = 1
    current_page = min(max(current_page, 1), page_count)
    start_index = (current_page - 1) * page_size
    end_index = start_index + page_size
    return {
        'items': visits[start_index:end_index],
        'page': current_page,
        'page_count': page_count,
        'page_size': page_size,
        'total': total,
        'start': start_index + 1 if total else 0,
        'end': min(end_index, total),
        'has_previous': current_page > 1,
        'has_next': current_page < page_count,
        'previous_page': current_page - 1,
        'next_page': current_page + 1,
        'pages': _visible_pages(current_page, page_count),
    }


def _visit_person_options(families: list) -> list[dict]:
    options = []
    for family in families:
        family_id = family.get('id') or ''
        if not family_id:
            continue
        surname = (family.get('surname') or '').strip()
        address = (family.get('address') or '').strip()
        if surname:
            options.append({
                'name': f'Obitelj {surname}',
                'address': address,
                'familyId': family_id,
                'detail': address,
            })
        for member in family.get('members') or []:
            name = (member.get('name') or '').strip()
            if not name:
                continue
            options.append({
                'name': name,
                'address': address,
                'familyId': family_id,
                'detail': ' · '.join(filter(None, (surname, address))),
            })
    options.sort(key=lambda item: (item.get('name') or '').casefold())
    return options


def _visit_type_label(visit_type: str | None) -> str:
    key = (visit_type or '').strip()
    return VISIT_TYPE_LABELS.get(key, key or '—')


def _enrich_visit(visit: dict, families_by_id: dict, today: date) -> dict:
    enriched = dict(visit)
    family = families_by_id.get(enriched.get('familyId'))
    if family:
        enriched.setdefault('familySurname', family.get('surname', ''))
        enriched.setdefault('address', family.get('address', ''))
        enriched['familyId'] = family.get('id') or enriched.get('familyId') or ''
    scheduled_date = parse_iso_date(enriched.get('scheduled'))
    enriched['isOverdue'] = bool(
        not enriched.get('done')
        and scheduled_date
        and scheduled_date < today
    )
    enriched['daysOverdue'] = (
        (today - scheduled_date).days if enriched['isOverdue'] else 0
    )
    enriched['needsReport'] = bool(
        enriched.get('done') and not (enriched.get('report') or '').strip()
    )
    enriched['typeLabel'] = _visit_type_label(enriched.get('type'))
    return enriched


def _matches_filter(visit: dict, filter_status: str) -> bool:
    if filter_status == 'done':
        return bool(visit.get('done'))
    if filter_status == 'all':
        return True
    if filter_status == 'overdue':
        return bool(visit.get('isOverdue'))
    if filter_status == 'needs_report':
        return bool(visit.get('needsReport'))
    return not visit.get('done')


def _matches_search(visit: dict, search_term: str) -> bool:
    if not search_term:
        return True
    haystack = ' '.join(
        filter(None, (visit.get('person'), visit.get('familySurname')))
    ).casefold()
    return search_term in haystack


def _sort_by_date(visits: list[dict], *, descending: bool = False) -> list[dict]:
    dated: list[tuple[date, dict]] = []
    undated: list[dict] = []
    for visit in visits:
        scheduled = parse_iso_date(visit.get('scheduled'))
        if scheduled is None:
            undated.append(visit)
        else:
            dated.append((scheduled, visit))
    dated.sort(key=lambda item: item[0], reverse=descending)
    return [visit for _scheduled, visit in dated] + undated


def visits_page_context(data: dict, request) -> dict:
    today_date = date.today()
    today = today_date.isoformat()
    filter_status = (request.GET.get('status') or 'open').strip().casefold()
    allowed = {item[0] for item in VISIT_FILTERS}
    if filter_status not in allowed:
        filter_status = 'open'
    search_term = (request.GET.get('q') or '').strip()
    normalized_search = search_term.casefold()
    sort_dir = (request.GET.get('dir') or 'asc').strip().casefold()
    if sort_dir not in {'asc', 'desc'}:
        sort_dir = 'asc'

    families_by_id = {
        family.get('id'): family
        for family in data.get('families', [])
        if family.get('id')
    }
    all_visits = [
        _enrich_visit(visit, families_by_id, today_date)
        for visit in data.get('visits', [])
    ]
    searchable_visits = [
        visit
        for visit in all_visits
        if _matches_search(visit, normalized_search)
    ]

    sorted_visits = _sort_by_date(
        searchable_visits,
        descending=sort_dir == 'desc',
    )
    filtered_visits = [
        visit
        for visit in sorted_visits
        if _matches_filter(visit, filter_status)
    ]
    visit_pagination = paginate_visits(
        filtered_visits,
        request.GET.get('page'),
    )
    visible_visits = visit_pagination['items']

    open_visits = [visit for visit in searchable_visits if not visit.get('done')]
    overdue = [visit for visit in searchable_visits if visit.get('isOverdue')]
    reports_missing = [
        visit for visit in searchable_visits if visit.get('needsReport')
    ]
    done_visits = [visit for visit in searchable_visits if visit.get('done')]

    filter_counts = {
        'open': len(open_visits),
        'overdue': len(overdue),
        'needs_report': len(reports_missing),
        'done': len(done_visits),
        'all': len(searchable_visits),
    }

    visit_filter_params = {}
    if filter_status != 'open':
        visit_filter_params['status'] = filter_status
    if search_term:
        visit_filter_params['q'] = search_term
    if sort_dir != 'asc':
        visit_filter_params['dir'] = sort_dir

    families = data.get('families', [])
    return {
        'visits': visible_visits,
        'visit_stats': {
            'total': len(all_visits),
            'open': len(open_visits),
            'due': len(overdue),
            'reports_missing': len(reports_missing),
            'done': len(done_visits),
            'communion': sum(
                1
                for visit in open_visits
                if visit.get('type') == 'kucna-pricest'
            ),
        },
        'visit_filters': [
            {
                'id': filter_id,
                'label': label,
                'href': f'?{_visit_query(status=filter_id, q=search_term, dir=sort_dir)}',
                'active': filter_status == filter_id,
                'count': filter_counts[filter_id],
            }
            for filter_id, label in VISIT_FILTERS
        ],
        'filter_status': filter_status,
        'visit_search': search_term,
        'visit_search_active': bool(search_term),
        'visit_sort_dir': sort_dir,
        'visit_sort_toggle_href': (
            f'?{_visit_query(status=filter_status, q=search_term, dir=("desc" if sort_dir == "asc" else "asc"))}'
        ),
        'visit_query': urlencode(visit_filter_params),
        'visit_pagination': visit_pagination,
        'families': families,
        'visit_person_options': _visit_person_options(families),
        'today': today,
    }
