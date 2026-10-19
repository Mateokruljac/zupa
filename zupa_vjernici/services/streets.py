"""Ulice župe — kontekst stranice (bivši renderUlicePage u app.js)."""
from __future__ import annotations

from urllib.parse import quote_plus, urlencode

from zupa_vjernici.services.street_records import street_name_history

STREET_PAGE_SIZE = 15


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


def paginate_streets(
    streets: list[dict],
    page_number: object,
    *,
    page_size: int = STREET_PAGE_SIZE,
) -> dict:
    total = len(streets)
    page_count = max(1, (total + page_size - 1) // page_size) if total else 1
    try:
        current_page = int(page_number or 1)
    except (TypeError, ValueError):
        current_page = 1
    current_page = min(max(current_page, 1), page_count)
    start_index = (current_page - 1) * page_size
    end_index = start_index + page_size
    return {
        'items': streets[start_index:end_index],
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


def filter_streets(streets: list[dict], *, search_term: str = '') -> list[dict]:
    matching_streets = list(streets)
    normalized_search = search_term.casefold()
    if normalized_search:
        matching_streets = [
            street
            for street in matching_streets
            if normalized_search in (street.get('name') or '').casefold()
        ]
    return matching_streets


def _street_query(**params) -> str:
    cleaned = {
        key: value
        for key, value in params.items()
        if value not in (None, '')
    }
    return urlencode(cleaned)


def streets_page_context(
    data: dict,
    request,
    parish_settings: dict | None = None,
    parish=None,
) -> dict:
    families_by_street: dict[str, list] = {}
    for family in data.get('families', []):
        street_id = family.get('streetId') or ''
        if street_id:
            families_by_street.setdefault(street_id, []).append(family)

    family_counts = {
        street_id: len(street_families)
        for street_id, street_families in families_by_street.items()
    }

    sort_key = (request.GET.get('sort') or 'families').strip().casefold()
    if sort_key not in {'families', 'name'}:
        sort_key = 'families'
    sort_dir = (request.GET.get('dir') or 'desc').strip().casefold()
    if sort_dir not in {'asc', 'desc'}:
        sort_dir = 'desc' if sort_key == 'families' else 'asc'

    all_streets = list(data.get('streets', []))
    reverse = sort_dir == 'desc'
    if sort_key == 'families':
        # Broj obitelji (desc/asc); unutar istog broja uvijek A→Ž.
        sign = -1 if reverse else 1
        all_streets.sort(
            key=lambda street: (
                sign * family_counts.get(street.get('id') or '', 0),
                (street.get('name') or '').casefold(),
            ),
        )
    else:
        all_streets.sort(
            key=lambda street: (street.get('name') or '').casefold(),
            reverse=reverse,
        )

    search_term = (request.GET.get('q') or '').strip()
    filtered_streets = filter_streets(all_streets, search_term=search_term)
    street_pagination = paginate_streets(
        filtered_streets,
        request.GET.get('page'),
    )
    streets = street_pagination['items']

    selected_street_id = (request.GET.get('street') or '').strip()
    selected_street = next(
        (
            street
            for street in all_streets
            if street.get('id') == selected_street_id
        ),
        None,
    )
    street_families = sorted(
        families_by_street.get(selected_street_id, []),
        key=lambda family: (family.get('surname') or '').lower(),
    )
    street_map_query = ''
    street_map_embed_url = ''
    street_map_external_url = ''
    street_history = []
    if selected_street:
        parish_city = (parish_settings or {}).get('city') or ''
        street_city = (selected_street.get('city') or '').strip() or parish_city
        street_map_query = ', '.join(
            address_part
            for address_part in (
                selected_street.get('name') or '',
                street_city,
                'Hrvatska',
            )
            if address_part
        )
        encoded_map_query = quote_plus(street_map_query)
        street_map_embed_url = (
            f'https://www.google.com/maps?q={encoded_map_query}&output=embed'
        )
        street_map_external_url = (
            f'https://www.google.com/maps/search/?api=1&query={encoded_map_query}'
        )
        if parish is not None:
            street_history = street_name_history(
                parish,
                selected_street.get('id') or '',
            )

    assigned_families_count = sum(
        len(street_families_list)
        for street_families_list in families_by_street.values()
    )

    street_card_tab = request.GET.get('tab', 'ulica')
    if street_card_tab not in {'ulica', 'obitelji'}:
        street_card_tab = 'ulica'

    street_filter_params = {}
    if search_term:
        street_filter_params['q'] = search_term
    if sort_key != 'families':
        street_filter_params['sort'] = sort_key
    if not (sort_key == 'families' and sort_dir == 'desc'):
        street_filter_params['dir'] = sort_dir
    street_list_params = dict(street_filter_params)
    if street_pagination['page'] > 1:
        street_list_params['page'] = street_pagination['page']

    families_sort_dir = (
        'asc' if sort_key == 'families' and sort_dir == 'desc' else 'desc'
    )
    name_sort_dir = (
        'desc' if sort_key == 'name' and sort_dir == 'asc' else 'asc'
    )

    return {
        'streets': streets,
        'all_streets_count': len(all_streets),
        'selected_street': selected_street,
        'selected_street_id': selected_street_id,
        'street_families': street_families,
        'street_map_query': street_map_query,
        'street_map_embed_url': street_map_embed_url,
        'street_map_external_url': street_map_external_url,
        'street_history': street_history,
        'family_counts': family_counts,
        'assigned_families_count': assigned_families_count,
        'show_new_street_dialog': request.GET.get('new') == '1',
        'street_card_tab': street_card_tab,
        'street_filters': {
            'q': search_term,
            'sort': sort_key,
            'dir': sort_dir,
        },
        'street_sort_families_href': (
            f'?{_street_query(q=search_term, sort="families", dir=families_sort_dir)}'
        ),
        'street_sort_name_href': (
            f'?{_street_query(q=search_term, sort="name", dir=name_sort_dir)}'
        ),
        'street_query': urlencode(street_filter_params),
        'street_list_query': urlencode(street_list_params),
        'street_pagination': street_pagination,
    }
