"""API mutacije ulica i kvartova župe."""
from __future__ import annotations

from pastoral.services.api_action_handlers.shared import (
    generate_record_identifier,
)


def upsert_street(parish_data: dict, action_payload: dict) -> dict:
    street_id = action_payload.get('id')
    street_payload = {
        'name': (action_payload.get('name') or '').strip(),
        'zone': (action_payload.get('zone') or '').strip(),
        'notes': (action_payload.get('notes') or '').strip(),
    }
    if not street_payload['name']:
        return {'ok': False, 'error': 'name_required'}
    if street_id:
        street = next(
            (
                existing_street
                for existing_street in parish_data.get('streets', [])
                if existing_street.get('id') == street_id
            ),
            None,
        )
        if not street:
            return {'ok': False, 'error': 'not_found'}
        street.update(street_payload)
        return {'ok': True, 'item': street}

    street = {
        'id': generate_record_identifier('st'),
        'sortOrder': len(parish_data.get('streets', [])) + 1,
        **street_payload,
    }
    parish_data.setdefault('streets', []).append(street)
    return {'ok': True, 'item': street}


def delete_street(parish_data: dict, action_payload: dict) -> dict:
    street_id = action_payload.get('id')
    parish_data['streets'] = [
        street
        for street in parish_data.get('streets', [])
        if street.get('id') != street_id
    ]
    return {'ok': True}
