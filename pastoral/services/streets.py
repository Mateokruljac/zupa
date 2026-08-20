"""Ulice župe — kontekst stranice (bivši renderUlicePage u app.js)."""
from __future__ import annotations

from urllib.parse import quote_plus


def streets_page_context(
    data: dict,
    request,
    parish_settings: dict | None = None,
) -> dict:
    streets = sorted(
        data.get('streets', []),
        key=lambda street: (
            street.get('sortOrder', 0),
            (street.get('name') or '').lower(),
        ),
    )
    families_by_street: dict[str, list] = {}
    unassigned_families: list = []
    for family in data.get('families', []):
        street_id = family.get('streetId') or ''
        if street_id:
            families_by_street.setdefault(street_id, []).append(family)
        else:
            unassigned_families.append(family)

    selected_street_id = (request.GET.get('street') or '').strip()
    selected_street = next(
        (
            street
            for street in streets
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
    if selected_street:
        parish_city = (parish_settings or {}).get('city') or ''
        street_map_query = ', '.join(
            address_part
            for address_part in (
                selected_street.get('name') or '',
                parish_city,
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

    assigned_families_count = sum(
        len(street_families)
        for street_families in families_by_street.values()
    )
    show_street_form = (
        request.GET.get('new') == '1'
        or (
            bool(selected_street)
            and request.GET.get('edit') == '1'
        )
    )

    return {
        'streets': streets,
        'selected_street': selected_street,
        'selected_street_id': selected_street_id,
        'street_families': street_families,
        'street_map_query': street_map_query,
        'street_map_embed_url': street_map_embed_url,
        'street_map_external_url': street_map_external_url,
        'family_counts': {
            street_id: len(street_families)
            for street_id, street_families in families_by_street.items()
        },
        'unassigned_families': sorted(
            unassigned_families,
            key=lambda family: (family.get('surname') or '').lower(),
        ),
        'assigned_families_count': assigned_families_count,
        'show_street_form': show_street_form,
        'street_form_mode': (
            'edit' if selected_street and request.GET.get('edit') == '1'
            else 'new' if request.GET.get('new') == '1'
            else None
        ),
    }
