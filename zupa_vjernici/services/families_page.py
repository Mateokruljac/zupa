"""Kontekst stranice Obitelji."""
from __future__ import annotations

from datetime import date
from urllib.parse import urlencode

from django.db import DatabaseError

from pastoral.services.dates import parse_iso_date
from pregled.services.dashboard import calculate_parish_population_statistics
from zupa_vjernici.services.contribution_categories import (
    contribution_totals,
    is_lukno_contribution,
    parish_contribution_totals,
)
from zupa_vjernici.services.membership_timeline import (
    membership_timeline_for_family,
)

REPORT_CHART_YEAR_SPAN = 8

FAMILY_PAGE_SIZE = 15
FAMILY_CARD_TABS = (
    ('osnovno', 'Osnovno'),
    ('clanovi', 'Članovi'),
    ('lukno', 'Lukno i darovi'),
    ('povijest', 'Povijest'),
    ('biljeske', 'Bilješke'),
)
_STATUS_FILTER_LABELS = {
    'aktivna': 'Aktivne',
    'neaktivna': 'Neaktivne',
    'all': 'Sve',
}
_LUKNO_FILTER_LABELS = {
    'paid': 'Plaćeno',
    'unpaid': 'Nije plaćeno',
}
_FOCUS_FILTER_LABELS = {
    'no_contact': 'Bez telefona',
    'new': 'Nove ove godine',
    'visit_due': 'Za posjetiti',
}


def _family_list_query(**params) -> str:
    return urlencode(
        {
            key: value
            for key, value in params.items()
            if value not in (None, '')
        }
    )


def _normalized_focus_filter(value: str | None) -> str:
    normalized = str(value or '').strip().casefold()
    if normalized in _FOCUS_FILTER_LABELS:
        return normalized
    return ''


def _family_has_phone(family: dict) -> bool:
    return bool(str(family.get('phone') or '').strip())


def _family_created_in_year(family: dict, year: int) -> bool:
    created_at = str(family.get('createdAt') or '').strip()
    return created_at.startswith(f'{year}-')


def _family_needs_visit(family: dict, today: date) -> bool:
    last_visit = parse_iso_date(family.get('lastVisit'))
    if not last_visit:
        return True
    if (today - last_visit).days > 365:
        return True
    return 'posjetiti' in (family.get('pastoralNotes') or '').casefold()


def _filters_are_active(
    *,
    search_term: str,
    street_filter: str,
    lukno_filter: str,
    lukno_year: int,
    previous_year: int,
    status_query_value: str,
    focus_filter: str,
) -> bool:
    return bool(
        search_term
        or street_filter
        or lukno_filter
        or focus_filter
        or status_query_value != 'aktivna'
        or lukno_year != previous_year
    )


def _active_family_filters(
    *,
    search_term: str,
    street_filter: str,
    street_name: str,
    lukno_filter: str,
    lukno_year: int,
    previous_year: int,
    status_query_value: str,
    focus_filter: str,
    page: int,
) -> list[dict]:
    """Samo chipovi koji odstupaju od zadanih filtera."""
    base = {
        'q': search_term,
        'street': street_filter,
        'lukno': lukno_filter,
        'year': str(lukno_year),
        'status': (
            status_query_value if status_query_value != 'aktivna' else ''
        ),
        'focus': focus_filter,
        'page': str(page) if page > 1 else '',
    }

    def clear_url(**overrides) -> str:
        merged = dict(base)
        merged.update(overrides)
        query = _family_list_query(**merged)
        return f'?{query}' if query else '?'

    chips: list[dict] = []
    if status_query_value != 'aktivna':
        chips.append(
            {
                'key': 'status',
                'label': 'Aktivnost',
                'value': _STATUS_FILTER_LABELS.get(
                    status_query_value,
                    status_query_value,
                ),
                'clear_url': clear_url(status='', page=''),
                'removable': True,
            }
        )
    if lukno_year != previous_year:
        chips.append(
            {
                'key': 'year',
                'label': 'Lukno',
                'value': f'{lukno_year}.',
                'clear_url': clear_url(year=str(previous_year), page=''),
                'removable': True,
            }
        )
    if lukno_filter:
        chips.append(
            {
                'key': 'lukno',
                'label': 'Status lukna',
                'value': _LUKNO_FILTER_LABELS.get(lukno_filter, lukno_filter),
                'clear_url': clear_url(lukno='', page=''),
                'removable': True,
            }
        )
    if focus_filter:
        chips.append(
            {
                'key': 'focus',
                'label': 'Brzi filter',
                'value': _FOCUS_FILTER_LABELS.get(focus_filter, focus_filter),
                'clear_url': clear_url(focus='', page=''),
                'removable': True,
            }
        )
    if street_filter:
        chips.append(
            {
                'key': 'street',
                'label': 'Ulica',
                'value': street_name or street_filter,
                'clear_url': clear_url(street='', page=''),
                'removable': True,
            }
        )
    if search_term:
        chips.append(
            {
                'key': 'q',
                'label': 'Pretraga',
                'value': search_term,
                'clear_url': clear_url(q='', page=''),
                'removable': True,
            }
        )
    return chips


def filter_families(
    families: list[dict],
    *,
    street_id: str = '',
    search_term: str = '',
    lukno: str = '',
    lukno_year: int | None = None,
    status: str = 'aktivna',
    focus: str = '',
    reference_date: date | None = None,
) -> list[dict]:
    """Vrati obitelji koje odgovaraju ulici, imenu člana, luknu i fokusu."""
    matching_families = list(families)
    today = reference_date or date.today()
    if street_id:
        matching_families = [
            family
            for family in matching_families
            if family.get('streetId') == street_id
        ]
    normalized_search = search_term.strip().casefold()
    if normalized_search:
        matching_families = [
            family
            for family in matching_families
            if _family_matches_search(family, normalized_search)
        ]
    lukno_filter = _normalized_lukno_filter(lukno)
    if lukno_filter and lukno_year is not None:
        matching_families = [
            family
            for family in matching_families
            if _family_matches_lukno_filter(family, lukno_year, lukno_filter)
        ]
    status_filter = _normalized_status_filter(status)
    if status_filter:
        matching_families = [
            family
            for family in matching_families
            if _family_status(family) == status_filter
        ]
    focus_filter = _normalized_focus_filter(focus)
    if focus_filter == 'no_contact':
        matching_families = [
            family
            for family in matching_families
            if not _family_has_phone(family)
        ]
    elif focus_filter == 'new':
        matching_families = [
            family
            for family in matching_families
            if _family_created_in_year(family, today.year)
        ]
    elif focus_filter == 'visit_due':
        matching_families = [
            family
            for family in matching_families
            if _family_needs_visit(family, today)
        ]
    matching_families.sort(key=lambda family: (family.get('surname') or '').casefold())
    return matching_families


def _family_status(family: dict) -> str:
    status = str(family.get('status') or 'aktivna').strip().casefold()
    return 'neaktivna' if status == 'neaktivna' else 'aktivna'


def _normalized_status_filter(value: str | None) -> str:
    """``aktivna`` / ``neaktivna`` / ``''`` (sve). Zadano: aktivne."""
    if value is None:
        return 'aktivna'
    normalized = str(value).strip().casefold()
    if normalized in ('', 'all', 'sve'):
        return ''
    if normalized in ('aktivna', 'neaktivna'):
        return normalized
    return 'aktivna'


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


def paginate_families(
    families: list[dict],
    page_number: object,
    *,
    page_size: int = FAMILY_PAGE_SIZE,
) -> dict:
    total = len(families)
    page_count = max(1, (total + page_size - 1) // page_size) if total else 1
    try:
        current_page = int(page_number or 1)
    except (TypeError, ValueError):
        current_page = 1
    current_page = min(max(current_page, 1), page_count)
    start_index = (current_page - 1) * page_size
    end_index = start_index + page_size
    return {
        'items': families[start_index:end_index],
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


def resolve_lukno_year(raw_value, current_year: int) -> int:
    """Vrati odabranu godinu lukna ili prethodnu godinu ako unos nije valjan."""
    previous_year = current_year - 1
    text = str(raw_value or '').strip()
    if not text:
        return previous_year
    try:
        requested_year = int(text)
    except ValueError:
        return previous_year
    if 1990 <= requested_year <= current_year:
        return requested_year
    return previous_year


def _normalized_lukno_filter(value: str) -> str:
    normalized = (value or '').strip().casefold()
    if normalized in {'paid', 'unpaid'}:
        return normalized
    return ''


def _family_lukno_is_paid(family: dict, year: int) -> bool:
    contribution = _contribution_for_year(family, year)
    return bool(contribution and contribution.get('luknoPaid'))


def _family_matches_lukno_filter(family: dict, year: int, lukno_filter: str) -> bool:
    is_paid = _family_lukno_is_paid(family, year)
    if lukno_filter == 'paid':
        return is_paid
    return not is_paid


def _contribution_for_year(family: dict, year: int) -> dict | None:
    return next(
        (
            contribution
            for contribution in family.get('contributions') or []
            if contribution.get('year') == year
            and is_lukno_contribution(contribution)
        ),
        None,
    )


def _previous_year_lukno_totals(families: list[dict], year: int) -> tuple[int, float]:
    unpaid_count = 0
    paid_income = 0.0
    for family in families:
        contribution = _contribution_for_year(family, year)
        if not contribution:
            continue
        if contribution.get('luknoPaid'):
            paid_income += float(contribution.get('luknoAmount') or 0)
        else:
            unpaid_count += 1
    return unpaid_count, paid_income


def _composition_row(label: str, detail: str, count: int, total: int) -> dict:
    return {
        'label': label,
        'detail': detail,
        'count': count,
        'share': round(count / total * 100) if total else 0,
    }


def _family_matches_search(family: dict, search_term: str) -> bool:
    return any(
        search_term in (family_member.get('name') or '').casefold()
        for family_member in family.get('members') or []
    )


def _lukno_payment_status(family: dict, year: int) -> str:
    contribution = _contribution_for_year(family, year)
    if not contribution:
        return 'none'
    if contribution.get('luknoPaid'):
        return 'paid'
    return 'unpaid'


def _enrich_family_row(family: dict, today: date) -> dict:
    enriched = dict(family)
    last_visit = parse_iso_date(enriched.get('lastVisit'))
    enriched['last_visit_days'] = (
        (today - last_visit).days if last_visit else None
    )
    enriched['needs_pastoral_followup'] = _family_needs_visit(enriched, today)
    enriched['has_phone'] = _family_has_phone(enriched)
    return enriched


def _selected_family_profile(
    data: dict,
    selected_family: dict,
    year: int,
    today: date,
) -> dict:
    visits = sorted(
        [
            visit
            for visit in data.get('visits', [])
            if visit.get('familyId') == selected_family.get('id')
        ],
        key=lambda visit: visit.get('scheduled') or '',
        reverse=True,
    )
    last_visit_date = parse_iso_date(selected_family.get('lastVisit'))
    data_gaps = []
    if not selected_family.get('phone'):
        data_gaps.append('telefon')
    if not selected_family.get('email'):
        data_gaps.append('e-mail')
    if not selected_family.get('streetId'):
        data_gaps.append('teritorijalna pripadnost')
    return {
        'visits': visits,
        'last_visit': visits[0] if visits else None,
        'last_visit_on': selected_family.get('lastVisit') or '',
        'last_visit_days': (
            (today - last_visit_date).days if last_visit_date else None
        ),
        'needs_pastoral_followup': _family_needs_visit(selected_family, today),
        'open_visits': sum(1 for visit in visits if not visit.get('done')),
        'current_contribution': _contribution_for_year(selected_family, year),
        'contribution_totals': contribution_totals(
            selected_family.get('contributions') or [],
        ),
        'data_gaps': data_gaps,
        'tags': selected_family.get('tags') or [],
        'notes': selected_family.get('pastoralNotes') or '',
        'membership_timeline': membership_timeline_for_family(
            selected_family.get('id') or '',
        ),
    }


def _payments_chart_rows(totals: dict) -> list[dict]:
    """Uplate po godinama (uzlazno) za bar grafikon."""
    return [
        {
            'label': f'{row.get("year")}.',
            'total': float(row.get('total') or 0),
        }
        for row in reversed(list(totals.get('byYear') or []))
        if row.get('year')
    ]


def _people_count_as_of(as_of: date) -> int | None:
    """Broj osoba u kućanstvima na datum (SCD2 članstva)."""
    try:
        from zupa_vjernici.models import HouseholdMembership

        return (
            HouseholdMembership.objects.filter(
                lives_in_household=True,
                date_from__lte=as_of,
                date_to__gt=as_of,
            )
            .values('public_identifier')
            .distinct()
            .count()
        )
    except DatabaseError:
        return None


def _people_chart_rows_from_families(
    families: list[dict],
    years: list[int],
    today: date,
) -> list[dict]:
    """Približan broj članova prema createdAt kućanstva (fallback)."""
    rows: list[dict] = []
    for year in years:
        as_of = min(date(year, 12, 31), today)
        as_of_iso = as_of.isoformat()
        total = 0
        for family in families:
            created_at = str(family.get('createdAt') or '').strip()
            if created_at and created_at[:10] > as_of_iso:
                continue
            total += len(family.get('members') or [])
        rows.append({'label': f'{year}.', 'count': total})
    return rows


def _people_chart_rows(families: list[dict], current_year: int) -> list[dict]:
    """Kretanje broja ljudi po godinama (linijski graf)."""
    today = date.today()
    start_year = current_year - REPORT_CHART_YEAR_SPAN + 1
    years = list(range(start_year, current_year + 1))
    rows: list[dict] = []
    used_db = False
    for year in years:
        as_of = min(date(year, 12, 31), today)
        count = _people_count_as_of(as_of)
        if count is None:
            break
        used_db = True
        rows.append({'label': f'{year}.', 'count': count})
    if used_db and len(rows) == len(years):
        if any(row['count'] for row in rows):
            return rows
    return _people_chart_rows_from_families(families, years, today)


def families_report_page_context(data: dict, request) -> dict:
    """Izvještajni pregled: KPI, sastav kućanstava, uplate."""
    year = date.today().year
    previous_year = year - 1
    all_families = list(data.get('families', []))
    total_members = sum(
        len(family.get('members') or [])
        for family in all_families
    )
    if all_families:
        members_average = total_members / len(all_families)
        members_average_display = (
            str(int(members_average))
            if members_average == int(members_average)
            else f'{members_average:.1f}'.replace('.', ',')
        )
    else:
        members_average_display = '—'
    previous_year_lukno_unpaid, previous_year_lukno_income = (
        _previous_year_lukno_totals(all_families, previous_year)
    )
    population_stats = calculate_parish_population_statistics(data)
    family_count = len(all_families)
    households_with_more_children = (
        population_stats['households_with_two_children']
        + population_stats['households_with_three_children']
        + population_stats['households_with_more_children']
    )
    parish_finance_totals = parish_contribution_totals(all_families)
    return {
        'family_stats': {
            'total': family_count,
            'members': total_members,
            'members_average': members_average_display,
            'streets_count': len(data.get('streets', [])),
            'previous_year': previous_year,
            'previous_year_lukno_unpaid': previous_year_lukno_unpaid,
            'previous_year_lukno_income': previous_year_lukno_income,
        },
        'family_composition': [
            _composition_row(
                'Samačka',
                'jedna osoba u kartonu',
                population_stats['single_person_households'],
                family_count,
            ),
            _composition_row(
                'Bez djece',
                'više članova, bez djece',
                population_stats['households_without_children'],
                family_count,
            ),
            _composition_row(
                'S jednim djetetom',
                'jedan sin, kći ili dijete',
                population_stats['households_with_one_child'],
                family_count,
            ),
            _composition_row(
                'S više djece',
                'dvoje ili više djece',
                households_with_more_children,
                family_count,
            ),
        ],
        'parish_finance_totals': parish_finance_totals,
        'family_payments_chart': _payments_chart_rows(parish_finance_totals),
        'family_people_chart': _people_chart_rows(all_families, year),
        'current_year': year,
    }


def families_page_context(data: dict, request) -> dict:
    streets = {
        street['id']: street
        for street in data.get('streets', [])
    }
    street_filter = request.GET.get('street', '')
    search_term = (request.GET.get('q') or '').strip()
    focus_filter = _normalized_focus_filter(request.GET.get('focus'))
    print_mode = str(request.GET.get('print') or '').strip() == '1'
    year = date.today().year
    previous_year = year - 1
    lukno_year = resolve_lukno_year(request.GET.get('year'), year)
    lukno_filter = _normalized_lukno_filter(request.GET.get('lukno', ''))
    status_filter = _normalized_status_filter(request.GET.get('status'))
    status_query_value = (
        'all' if status_filter == '' else status_filter
    )
    all_families = list(data.get('families', []))
    today = date.today()
    filtered_families = filter_families(
        all_families,
        street_id=street_filter,
        search_term=search_term,
        lukno=lukno_filter,
        lukno_year=lukno_year,
        status=status_query_value,
        focus=focus_filter,
        reference_date=today,
    )
    if print_mode:
        family_pagination = paginate_families(
            filtered_families,
            1,
            page_size=max(len(filtered_families), 1),
        )
    else:
        family_pagination = paginate_families(
            filtered_families,
            request.GET.get('page'),
        )
    families = [
        _enrich_family_row(family, today)
        for family in family_pagination['items']
    ]
    previous_year_lukno_unpaid, _previous_income = (
        _previous_year_lukno_totals(all_families, previous_year)
    )
    missing_phone = sum(
        1
        for family in all_families
        if _family_status(family) == 'aktivna' and not _family_has_phone(family)
    )
    visit_due_count = sum(
        1
        for family in all_families
        if _family_status(family) == 'aktivna'
        and _family_needs_visit(family, today)
    )
    # Karton se otvara klijentski (API), ne preko ?family= — da ne
    # onečišćuje filtere / formu za novu obitelj.
    family_card_tab_ids = [tab_id for tab_id, _label in FAMILY_CARD_TABS]
    family_card_tab = 'osnovno'
    family_card_tab_index = 0
    list_query_params = {
        'q': search_term,
        'street': street_filter,
        'lukno': lukno_filter,
        'year': str(lukno_year),
        'status': (
            status_query_value
            if status_query_value != 'aktivna'
            else ''
        ),
        'focus': focus_filter,
    }
    filters_active = _filters_are_active(
        search_term=search_term,
        street_filter=street_filter,
        lukno_filter=lukno_filter,
        lukno_year=lukno_year,
        previous_year=previous_year,
        status_query_value=status_query_value,
        focus_filter=focus_filter,
    )
    unpaid_query = _family_list_query(
        lukno='unpaid',
        year=str(previous_year),
    )
    no_contact_query = _family_list_query(focus='no_contact')
    visit_due_query = _family_list_query(focus='visit_due')
    return {
        'families': families,
        'streets': streets,
        'street_list': data.get('streets', []),
        'empty_contribution_totals': {
            'byYear': [],
            'byCategory': [],
            'grandTotal': 0,
        },
        'family_card_tabs': [
            {
                'id': tab_id,
                'label': tab_label,
                'active': tab_id == family_card_tab,
            }
            for tab_id, tab_label in FAMILY_CARD_TABS
        ],
        'family_card_tab': family_card_tab,
        'family_card_previous_tab': (
            family_card_tab_ids[family_card_tab_index - 1]
            if family_card_tab_index > 0
            else ''
        ),
        'family_card_next_tab': (
            family_card_tab_ids[family_card_tab_index + 1]
            if family_card_tab_index < len(family_card_tab_ids) - 1
            else ''
        ),
        'family_filters': {
            'q': request.GET.get('q', ''),
            'street': street_filter,
            'lukno': lukno_filter,
            'year': lukno_year,
            'status': status_query_value,
            'focus': focus_filter,
        },
        'family_filters_active': filters_active,
        'active_family_filters': _active_family_filters(
            search_term=search_term,
            street_filter=street_filter,
            street_name=(
                streets.get(street_filter, {}).get('name', '')
                if street_filter
                else ''
            ),
            lukno_filter=lukno_filter,
            lukno_year=lukno_year,
            previous_year=previous_year,
            status_query_value=status_query_value,
            focus_filter=focus_filter,
            page=family_pagination['page'],
        ),
        'family_quick_filters': [
            {
                'id': 'unpaid',
                'label': f'Nije platilo lukno {previous_year}.',
                'href': f'?{unpaid_query}',
                'active': lukno_filter == 'unpaid' and not focus_filter,
                'count': previous_year_lukno_unpaid,
            },
            {
                'id': 'no_contact',
                'label': 'Bez telefona',
                'href': f'?{no_contact_query}',
                'active': focus_filter == 'no_contact',
                'count': missing_phone,
            },
            {
                'id': 'visit_due',
                'label': 'Za posjetiti',
                'href': f'?{visit_due_query}',
                'active': focus_filter == 'visit_due',
                'count': visit_due_count,
            },
        ],
        'lukno_year_choices': list(range(year, year - 16, -1)),
        'family_query': _family_list_query(**list_query_params),
        'family_list_query': _family_list_query(
            **list_query_params,
            page=(
                family_pagination['page']
                if family_pagination['page'] > 1
                else ''
            ),
        ),
        'family_print_query': _family_list_query(
            **list_query_params,
            print='1',
        ),
        'family_print_mode': print_mode,
        'family_pagination': family_pagination,
        'family_lukno_status': {
            family.get('id'): _lukno_payment_status(family, previous_year)
            for family in all_families
            if family.get('id')
        },
        'family_stats': {
            'total': len(all_families),
            'shown': family_pagination['total'],
            'previous_year': previous_year,
            'previous_year_lukno_unpaid': previous_year_lukno_unpaid,
            'missing_phone': missing_phone,
            'visit_due': visit_due_count,
        },
        'current_year': year,
    }
