"""Mutacije godina i kandidata za krizmu i prvu pričest."""
from __future__ import annotations

from pastoral.services.api_action_handlers.shared import (
    find_confirmation_group,
    find_first_communion_group,
    generate_record_identifier,
    normalize_date_value,
)
from pastoral.services.dates import today_iso


def create_confirmation_year(parish_data: dict, action_payload: dict) -> dict:
    confirmation_year = int(action_payload.get('year'))
    if find_confirmation_group(parish_data, confirmation_year):
        return {'ok': False, 'error': 'year_exists'}
    confirmation_group = {
        'id': generate_record_identifier('conf'),
        'year': confirmation_year,
        'bishop': (action_payload.get('bishop') or '').strip(),
        'ceremonyDate': normalize_date_value(
            action_payload.get('ceremony_date')
            or action_payload.get('ceremonyDate')
        ),
        'groupFee': float(
            action_payload.get('group_fee')
            or action_payload.get('groupFee')
            or 0
        ),
        'groupFeePaid': False,
        'candidates': [],
    }
    parish_data.setdefault('confirmations', []).insert(0, confirmation_group)
    return {'ok': True, 'item': confirmation_group}


def update_confirmation_group(parish_data: dict, action_payload: dict) -> dict:
    confirmation_group = find_confirmation_group(
        parish_data,
        int(action_payload.get('year')),
    )
    if not confirmation_group:
        return {'ok': False, 'error': 'not_found'}
    confirmation_group['ceremonyDate'] = normalize_date_value(
        action_payload.get('ceremony_date')
        or action_payload.get('ceremonyDate')
    )
    confirmation_group['bishop'] = (
        action_payload.get('bishop') or ''
    ).strip()
    confirmation_group['groupFee'] = float(
        action_payload.get('group_fee')
        or action_payload.get('groupFee')
        or 0
    )
    confirmation_group['groupFeePaid'] = bool(
        action_payload.get('group_fee_paid')
        or action_payload.get('groupFeePaid')
    )
    if (
        confirmation_group['groupFeePaid']
        and not confirmation_group.get('groupFeePaidAt')
    ):
        confirmation_group['groupFeePaidAt'] = today_iso()
    return {'ok': True, 'item': confirmation_group}


def upsert_confirmation_candidate(parish_data: dict, action_payload: dict) -> dict:
    confirmation_year = int(action_payload.get('year'))
    confirmation_group = find_confirmation_group(parish_data, confirmation_year)
    if not confirmation_group:
        confirmation_group = create_confirmation_year(
            parish_data,
            {'year': confirmation_year},
        )['item']
    candidate_payload = {
        field_name: action_payload.get(field_name, '')
        for field_name in (
            'name', 'birthDate', 'school', 'class', 'group',
            'baptized', 'sponsor', 'status', 'oib',
        )
    }
    candidate_id = action_payload.get('id')
    if candidate_id:
        confirmation_candidate = next(
            (
                existing_candidate
                for existing_candidate in confirmation_group.get('candidates') or []
                if existing_candidate.get('id') == candidate_id
            ),
            None,
        )
        if not confirmation_candidate:
            return {'ok': False, 'error': 'not_found'}
        confirmation_candidate.update(candidate_payload)
        return {'ok': True, 'item': confirmation_candidate}
    confirmation_candidate = {
        'id': generate_record_identifier('cr'),
        **candidate_payload,
    }
    confirmation_group.setdefault('candidates', []).append(
        confirmation_candidate
    )
    return {'ok': True, 'item': confirmation_candidate}


def delete_confirmation_candidate(parish_data: dict, action_payload: dict) -> dict:
    confirmation_group = find_confirmation_group(
        parish_data,
        int(action_payload.get('year')),
    )
    if not confirmation_group:
        return {'ok': False, 'error': 'not_found'}
    candidate_id = action_payload.get('id')
    confirmation_group['candidates'] = [
        confirmation_candidate
        for confirmation_candidate in confirmation_group.get('candidates') or []
        if confirmation_candidate.get('id') != candidate_id
    ]
    return {'ok': True}


def create_first_communion_year(parish_data: dict, action_payload: dict) -> dict:
    first_communion_year = int(action_payload.get('year'))
    if find_first_communion_group(parish_data, first_communion_year):
        return {'ok': False, 'error': 'year_exists'}
    first_communion_group = {
        'id': generate_record_identifier('fc'),
        'year': first_communion_year,
        'groupName': (
            action_payload.get('group_name')
            or action_payload.get('groupName')
            or f'Skupina {first_communion_year}'
        ).strip(),
        'celebrant': (action_payload.get('celebrant') or '').strip(),
        'ceremonyDate': normalize_date_value(
            action_payload.get('ceremony_date')
            or action_payload.get('ceremonyDate')
        ),
        'groupFee': 0,
        'groupFeePaid': False,
        'candidates': [],
    }
    parish_data.setdefault('firstCommunion', []).insert(
        0,
        first_communion_group,
    )
    return {'ok': True, 'item': first_communion_group}


def update_first_communion_group(
    parish_data: dict,
    action_payload: dict,
) -> dict:
    first_communion_group = find_first_communion_group(
        parish_data,
        int(action_payload.get('year')),
    )
    if not first_communion_group:
        return {'ok': False, 'error': 'not_found'}

    first_communion_group['groupName'] = (
        action_payload.get('group_name') or ''
    ).strip()
    first_communion_group['ceremonyDate'] = normalize_date_value(
        action_payload.get('ceremony_date')
    )
    first_communion_group['celebrant'] = (
        action_payload.get('celebrant') or ''
    ).strip()
    first_communion_group['groupFee'] = float(
        action_payload.get('group_fee') or 0
    )
    first_communion_group['groupFeePaid'] = bool(
        action_payload.get('group_fee_paid')
    )
    if (
        first_communion_group['groupFeePaid']
        and not first_communion_group.get('groupFeePaidAt')
    ):
        first_communion_group['groupFeePaidAt'] = today_iso()
    return {'ok': True, 'item': first_communion_group}


def upsert_first_communion_candidate(
    parish_data: dict,
    action_payload: dict,
) -> dict:
    first_communion_year = int(action_payload.get('year'))
    first_communion_group = find_first_communion_group(
        parish_data,
        first_communion_year,
    )
    if not first_communion_group:
        first_communion_group = create_first_communion_year(
            parish_data,
            {'year': first_communion_year},
        )['item']
    candidate_payload = dict(
        action_payload.get('fields') or action_payload
    )
    candidate_id = action_payload.get('id')
    if candidate_id:
        first_communion_candidate = next(
            (
                existing_candidate
                for existing_candidate in first_communion_group.get('candidates') or []
                if existing_candidate.get('id') == candidate_id
            ),
            None,
        )
        if not first_communion_candidate:
            return {'ok': False, 'error': 'not_found'}
        first_communion_candidate.update(candidate_payload)
        return {'ok': True, 'item': first_communion_candidate}
    first_communion_candidate = {
        'id': generate_record_identifier('c'),
        **candidate_payload,
    }
    first_communion_group.setdefault('candidates', []).append(
        first_communion_candidate
    )
    return {'ok': True, 'item': first_communion_candidate}


def delete_first_communion_candidate(
    parish_data: dict,
    action_payload: dict,
) -> dict:
    first_communion_group = find_first_communion_group(
        parish_data,
        int(action_payload.get('year')),
    )
    if not first_communion_group:
        return {'ok': False, 'error': 'not_found'}
    candidate_id = action_payload.get('id')
    first_communion_group['candidates'] = [
        first_communion_candidate
        for first_communion_candidate in first_communion_group.get('candidates') or []
        if first_communion_candidate.get('id') != candidate_id
    ]
    return {'ok': True}
