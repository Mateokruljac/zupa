"""Mutacije zapisa sakramenata u parish JSON-u."""
from __future__ import annotations

import uuid


def delete_sacrament(data: dict, array_key: str, record_id: str) -> bool:
    before = len(data.get(array_key, []))
    data[array_key] = [
        record
        for record in data.get(array_key, [])
        if record.get('id') != record_id
    ]
    return len(data[array_key]) < before


def add_sacrament_record(data: dict, array_key: str, fields: dict) -> dict:
    item = {
        'id': f"{array_key[:3]}_{uuid.uuid4().hex[:8]}",
        **fields,
    }
    data.setdefault(array_key, []).append(item)
    return item


def update_sacrament_record(
    data: dict,
    array_key: str,
    record_id: str,
    fields: dict,
) -> bool:
    record = next(
        (
            existing_record
            for existing_record in data.get(array_key, [])
            if existing_record.get('id') == record_id
        ),
        None,
    )
    if not record:
        return False
    record.update(fields)
    return True
