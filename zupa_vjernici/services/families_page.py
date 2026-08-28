"""Kontekst stranice Obitelji."""
from __future__ import annotations

from datetime import date
from urllib.parse import urlencode

from pastoral.services.dates import parse_iso_date
from pregled.services.dashboard import calculate_parish_population_statistics

FAMILY_PAGE_SIZE = 15
FAMILY_CARD_TABS = (
    ('osnovno', 'Osnovno'),
    ('clanovi', 'Članovi'),
    ('lukno', 'Lukno i darovi'),
    ('biljeske', 'Bilješke'),
)


def filter_families(
    families: list[dict],
    *,
    street_id: str = '',
    search_term: str = '',
    lukno: str = '',
    lukno_year: int | None = None,
) -> list[dict]:
    """Vrati obitelji koje odgovaraju ulici, pretrazi i statusu lukna."""
    matching_families = list(families)
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
    matching_families.sort(key=lambda family: (family.get('surname') or '').casefold())
    return matching_families


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
    if search_term in (family.get('surname') or '').casefold():
        return True
    if search_term in (family.get('address') or '').casefold():
        return True
    return any(
        search_term in (family_member.get('name') or '').casefold()
        for family_member in family.get('members') or []
    )


def families_page_context(data: dict, request) -> dict:
    streets = {
        street['id']: street
        for street in data.get('streets', [])
    }
    street_filter = request.GET.get('street', '')
    search_term = (request.GET.get('q') or '').strip()
    year = date.today().year
    previous_year = year - 1
    lukno_filter = _normalized_lukno_filter(request.GET.get('lukno', ''))
    all_families = list(data.get('families', []))
    families = filter_families(
        all_families,
        street_id=street_filter,
        search_term=search_term,
        lukno=lukno_filter,
        lukno_year=previous_year,
    )
    family_pagination = paginate_families(families, request.GET.get('page'))
    families = family_pagination['items']
    lukno_unpaid = 0
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
    family_composition = [
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
    ]
    today = date.today()
    enriched_families = []
    pastoral_due = 0
    missing_contact = 0
    for family in families:
        annual_contribution = next(
            (
                contribution
                for contribution in family.get('contributions', [])
                if contribution.get('year') == year
            ),
            None,
        )
        if annual_contribution and not annual_contribution.get('luknoPaid'):
            lukno_unpaid += 1
        enriched_family = dict(family)
        last_visit = parse_iso_date(enriched_family.get('lastVisit'))
        enriched_family['last_visit_days'] = (
            (today - last_visit).days
            if last_visit
            else None
        )
        enriched_family['needs_pastoral_followup'] = (
            not last_visit
            or enriched_family['last_visit_days'] > 365
            or 'posjetiti' in (
                enriched_family.get('pastoralNotes') or ''
            ).casefold()
        )
        if enriched_family['needs_pastoral_followup']:
            pastoral_due += 1
        if not enriched_family.get('phone') and not enriched_family.get('email'):
            missing_contact += 1
        enriched_families.append(enriched_family)
    families = enriched_families
    selected_family_id = request.GET.get('family', '')
    selected_family = next(
        (
            family
            for family in all_families
            if family.get('id') == selected_family_id
        ),
        None,
    )
    selected_family_profile = None
    if selected_family:
        visits = sorted(
            [
                visit
                for visit in data.get('visits', [])
                if visit.get('familyId') == selected_family.get('id')
            ],
            key=lambda visit: visit.get('scheduled') or '',
            reverse=True,
        )
        current_contribution = next(
            (
                contribution
                for contribution in selected_family.get('contributions', [])
                if contribution.get('year') == year
            ),
            None,
        )
        data_gaps = []
        if not selected_family.get('phone'):
            data_gaps.append('telefon')
        if not selected_family.get('email'):
            data_gaps.append('e-mail')
        if not selected_family.get('streetId'):
            data_gaps.append('teritorijalna pripadnost')
        
        selected_family_profile = {
            'visits': visits,
            'last_visit': visits[0] if visits else None,
            'open_visits': sum(1 for visit in visits if not visit.get('done')),
            'current_contribution': current_contribution,
            'data_gaps': data_gaps,
            'tags': selected_family.get('tags') or [],
            'notes': selected_family.get('pastoralNotes') or '',
        }
    family_card_tab_ids = [tab_id for tab_id, _label in FAMILY_CARD_TABS]
    family_card_tab = request.GET.get('tab', 'osnovno')
    if family_card_tab not in family_card_tab_ids:
        family_card_tab = 'osnovno'
    family_card_tab_index = family_card_tab_ids.index(family_card_tab)
    return {
        'families': families,
        'streets': streets,
        'street_list': data.get('streets', []),
        'selected_family': selected_family,
        'selected_family_profile': selected_family_profile,
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
        'family_card_edit': request.GET.get('edit') == '1',
        'family_filters': {
            'q': request.GET.get('q', ''),
            'street': street_filter,
            'lukno': lukno_filter,
        },
        'family_query': urlencode({
            key: value
            for key, value in {
                'q': search_term,
                'street': street_filter,
                'lukno': lukno_filter,
            }.items()
            if value
        }),
        'family_list_query': urlencode({
            key: value
            for key, value in {
                'q': search_term,
                'street': street_filter,
                'lukno': lukno_filter,
                'page': (
                    family_pagination['page']
                    if family_pagination['page'] > 1
                    else ''
                ),
            }.items()
            if value
        }),
        'family_pagination': family_pagination,
        'family_stats': {
            'total': len(all_families),
            'shown': family_pagination['total'],
            'members': total_members,
            'members_average': members_average_display,
            'streets_count': len(data.get('streets', [])),
            'lukno_unpaid': lukno_unpaid,
            'previous_year': previous_year,
            'previous_year_lukno_unpaid': previous_year_lukno_unpaid,
            'previous_year_lukno_income': previous_year_lukno_income,
            'pastoral_due': pastoral_due,
            'missing_contact': missing_contact,
        },
        'family_composition': family_composition,
        'current_year': year,
    }
