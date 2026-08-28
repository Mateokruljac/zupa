"""API mutacije za obitelji, ulice i pastoralne posjete."""
from __future__ import annotations

from pastoral.services.api_action_handlers.shared import (
    find_family,
    generate_record_identifier,
)
from pastoral.services.dates import today_iso
from zupa_vjernici.services.api_action_handlers.families import (
    create_family,
    delete_contribution,
    delete_family,
    delete_family_member,
    delete_relative,
    update_family,
    update_family_notes,
    update_spouse,
    upsert_contribution,
    upsert_family_member,
    upsert_relative,
)
from zupa_vjernici.services.api_action_handlers.streets import (
    delete_street,
    upsert_street,
)


def upsert_visit(data: dict, action_payload: dict) -> dict:
    payload = dict(action_payload.get('fields') or action_payload)
    visit_id = action_payload.get('id')
    if visit_id:
        visit_record = next(
            (
                visit
                for visit in data.get('visits', [])
                if visit.get('id') == visit_id
            ),
            None,
        )
        if not visit_record:
            return {'ok': False, 'error': 'not_found'}
        visit_record.update(payload)
        if visit_record.get('done') and visit_record.get('familyId'):
            family = find_family(data, visit_record['familyId'])
            if family:
                family['lastVisit'] = today_iso()
        return {'ok': True, 'item': visit_record}
    item = {
        'id': generate_record_identifier('v'),
        'done': False,
        **payload,
    }
    data.setdefault('visits', []).append(item)
    return {'ok': True, 'item': item}


def toggle_visit_done(data: dict, action_payload: dict) -> dict:
    visit_record = next(
        (
            visit
            for visit in data.get('visits', [])
            if visit.get('id') == action_payload.get('id')
        ),
        None,
    )
    if not visit_record:
        return {'ok': False, 'error': 'not_found'}
    visit_record['done'] = not visit_record.get('done')
    if visit_record['done'] and visit_record.get('familyId'):
        family = find_family(data, visit_record['familyId'])
        if family:
            family['lastVisit'] = today_iso()
    return {'ok': True, 'item': visit_record}

