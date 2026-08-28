"""API mutacije za sakramente i sakramentalnu pripravu."""
from __future__ import annotations

from pastoral.services.api_action_handlers.shared import (
    generate_record_identifier,
)

SACRAMENT_COLLECTIONS = frozenset({
    'baptisms', 'weddings', 'funerals', 'anointing',
})


def upsert_sacrament(data: dict, action_payload: dict) -> dict:
    collection_name = (
        action_payload.get('array_key')
        or action_payload.get('arrayKey')
    )
    if collection_name not in SACRAMENT_COLLECTIONS:
        return {'ok': False, 'error': 'array_key_required'}
    fields = dict(action_payload.get('fields') or {})
    record_id = action_payload.get('id')
    records = data.setdefault(collection_name, [])
    if record_id:
        record = next(
            (
                existing_record
                for existing_record in records
                if existing_record.get('id') == record_id
            ),
            None,
        )
        if not record:
            return {'ok': False, 'error': 'not_found'}
        record.update(fields)
        return {'ok': True, 'item': record}
    prefix = {
        'baptisms': 'b',
        'weddings': 'w',
        'funerals': 'f',
        'anointing': 'a',
    }.get(collection_name, 's')
    item = {
        'id': generate_record_identifier(prefix),
        **fields,
    }
    if collection_name == 'anointing':
        records.insert(0, item)
    else:
        records.append(item)
    return {'ok': True, 'item': item}


def delete_sacrament_record(data: dict, action_payload: dict) -> dict:
    collection_name = (
        action_payload.get('array_key')
        or action_payload.get('arrayKey')
    )
    if collection_name not in SACRAMENT_COLLECTIONS:
        return {'ok': False, 'error': 'array_key_required'}
    record_id = action_payload.get('id')
    before_count = len(data.get(collection_name, []))
    data[collection_name] = [
        record
        for record in data.get(collection_name, [])
        if record.get('id') != record_id
    ]
    return {'ok': len(data.get(collection_name, [])) < before_count}

