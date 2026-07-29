"""Ulice župe — kontekst stranice (bivši renderUlicePage u app.js)."""
from __future__ import annotations


def streets_page_context(data: dict, request) -> dict:
    streets = sorted(
        data.get('streets', []),
        key=lambda s: (s.get('sortOrder', 0), (s.get('name') or '').lower()),
    )
    families_by_street: dict[str, list] = {}
    unassigned: list = []
    for fam in data.get('families', []):
        sid = fam.get('streetId') or ''
        if sid:
            families_by_street.setdefault(sid, []).append(fam)
        else:
            unassigned.append(fam)

    selected_id = (request.GET.get('street') or '').strip()
    selected = next((s for s in streets if s.get('id') == selected_id), None)
    street_families = sorted(
        families_by_street.get(selected_id, []),
        key=lambda f: (f.get('surname') or '').lower(),
    )

    assigned_count = sum(len(fams) for fams in families_by_street.values())
    show_form = request.GET.get('new') == '1' or (bool(selected) and request.GET.get('edit') == '1')

    return {
        'streets': streets,
        'selected_street': selected,
        'selected_street_id': selected_id,
        'street_families': street_families,
        'family_counts': {sid: len(fams) for sid, fams in families_by_street.items()},
        'unassigned_families': sorted(unassigned, key=lambda f: (f.get('surname') or '').lower()),
        'assigned_families_count': assigned_count,
        'show_street_form': show_form,
        'street_form_mode': (
            'edit' if selected and request.GET.get('edit') == '1'
            else 'new' if request.GET.get('new') == '1'
            else None
        ),
    }
