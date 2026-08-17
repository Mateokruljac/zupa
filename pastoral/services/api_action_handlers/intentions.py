"""API mutacije misnih nakana."""
from __future__ import annotations

from datetime import datetime, timezone

from pastoral.services.api_action_handlers.shared import (
    generate_payment_reference,
    generate_record_identifier,
    normalize_date_value,
)


def create_intention(parish_data: dict, action_payload: dict) -> dict:
    is_paid = bool(action_payload.get('paid'))
    intention_record = {
        'id': generate_record_identifier('n'),
        'date': normalize_date_value(action_payload.get('date')),
        'massTime': (
            action_payload.get('mass_time')
            or action_payload.get('massTime')
            or ''
        ),
        'requestedBy': (
            action_payload.get('requested_by')
            or action_payload.get('requestedBy')
            or ''
        ),
        'intentionFor': (
            action_payload.get('intention_for')
            or action_payload.get('intentionFor')
            or ''
        ),
        'stipend': float(action_payload.get('stipend') or 0),
        'paid': is_paid,
        'notes': action_payload.get('notes') or '',
        'paymentId': (
            action_payload.get('payment_id')
            or action_payload.get('paymentId')
            or ('' if not is_paid else generate_payment_reference())
        ),
        'paidAt': (
            action_payload.get('paid_at')
            or action_payload.get('paidAt')
            or (
                datetime.now(timezone.utc).isoformat()
                if is_paid
                else ''
            )
        ),
    }
    parish_data.setdefault('intentions', []).append(intention_record)
    return {'ok': True, 'item': intention_record}


def update_intention(parish_data: dict, action_payload: dict) -> dict:
    intention_record = next(
        (
            intention
            for intention in parish_data.get('intentions', [])
            if intention.get('id') == action_payload.get('id')
        ),
        None,
    )
    if not intention_record:
        return {'ok': False, 'error': 'not_found'}

    field_mappings = (
        ('date', 'date'),
        ('mass_time', 'massTime'),
        ('massTime', 'massTime'),
        ('intention_for', 'intentionFor'),
        ('intentionFor', 'intentionFor'),
        ('requested_by', 'requestedBy'),
        ('requestedBy', 'requestedBy'),
        ('notes', 'notes'),
    )
    for source_field, destination_field in field_mappings:
        if source_field not in action_payload:
            continue
        field_value = action_payload[source_field]
        intention_record[destination_field] = (
            normalize_date_value(field_value)
            if destination_field == 'date'
            else field_value
        )
    if 'stipend' in action_payload:
        intention_record['stipend'] = float(
            action_payload['stipend'] or 0
        )
    return {'ok': True, 'item': intention_record}


def delete_intention(parish_data: dict, action_payload: dict) -> dict:
    intention_id = (
        action_payload.get('id') or action_payload.get('intention_id')
    )
    previous_intention_count = len(parish_data.get('intentions', []))
    parish_data['intentions'] = [
        intention
        for intention in parish_data.get('intentions', [])
        if intention.get('id') != intention_id
    ]
    return {
        'ok': len(parish_data['intentions']) < previous_intention_count,
    }


def mark_intention_paid(parish_data: dict, action_payload: dict) -> dict:
    intention_record = next(
        (
            intention
            for intention in parish_data.get('intentions', [])
            if intention.get('id') == action_payload.get('id')
        ),
        None,
    )
    if not intention_record:
        return {'ok': False, 'error': 'not_found'}
    intention_record['paid'] = True
    intention_record['paymentId'] = (
        action_payload.get('payment_id')
        or action_payload.get('paymentId')
        or generate_payment_reference()
    )
    intention_record['paidAt'] = (
        action_payload.get('paid_at')
        or action_payload.get('paidAt')
        or datetime.now(timezone.utc).isoformat()
    )
    return {'ok': True, 'item': intention_record}


def toggle_intention_paid(parish_data: dict, action_payload: dict) -> dict:
    intention_record = next(
        (
            intention
            for intention in parish_data.get('intentions', [])
            if intention.get('id') == action_payload.get('id')
        ),
        None,
    )
    if not intention_record:
        return {'ok': False, 'error': 'not_found'}
    intention_record['paid'] = not intention_record.get('paid')
    if intention_record['paid']:
        intention_record['paymentId'] = (
            intention_record.get('paymentId')
            or generate_payment_reference()
        )
        intention_record['paidAt'] = datetime.now(timezone.utc).isoformat()
    return {'ok': True, 'item': intention_record}
