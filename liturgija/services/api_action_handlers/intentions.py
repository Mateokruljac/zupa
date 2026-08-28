"""API mutacije misnih nakana."""
from __future__ import annotations

from datetime import datetime, timezone

from pastoral.services.api_action_handlers.shared import (
    generate_payment_reference,
    generate_record_identifier,
    normalize_date_value,
)
from liturgija.services.mass_schedule import get_masses_for_date


def _validate_intention_mass_slot(
    parish_data: dict,
    iso_date: str,
    mass_time: str,
) -> dict | None:
    if not iso_date:
        return {'ok': False, 'error': 'missing_date'}
    masses = get_masses_for_date(parish_data, iso_date)
    if not masses:
        return {'ok': False, 'error': 'no_mass_on_date'}
    allowed_times = {
        str(mass.get('time') or '')
        for mass in masses
        if mass.get('time')
    }
    if mass_time and mass_time not in allowed_times:
        return {'ok': False, 'error': 'mass_not_on_date'}
    return None


def create_intention(parish_data: dict, action_payload: dict) -> dict:
    iso_date = normalize_date_value(action_payload.get('date'))
    mass_time = (
        action_payload.get('mass_time')
        or action_payload.get('massTime')
        or ''
    )
    validation_error = _validate_intention_mass_slot(
        parish_data,
        iso_date,
        mass_time,
    )
    if validation_error:
        return validation_error

    is_paid = bool(action_payload.get('paid'))
    intention_record = {
        'id': generate_record_identifier('n'),
        'date': iso_date,
        'massTime': mass_time,
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

    original_date = intention_record.get('date') or ''
    original_mass_time = intention_record.get('massTime') or ''

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

    updated_date = intention_record.get('date') or ''
    updated_mass_time = intention_record.get('massTime') or ''
    mass_slot_changed = (
        updated_date != original_date
        or updated_mass_time != original_mass_time
    )
    if mass_slot_changed:
        validation_error = _validate_intention_mass_slot(
            parish_data,
            updated_date,
            updated_mass_time,
        )
        if validation_error:
            return validation_error
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
