"""Form POST mutacije misnih nakana."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone


def add_intention(data: dict, cleaned: dict) -> dict:
    item = {
        'id': f"n_{uuid.uuid4().hex[:8]}",
        'date': cleaned['date'].isoformat(),
        'massTime': cleaned['mass_time'],
        'requestedBy': cleaned['requested_by'],
        'intentionFor': cleaned['intention_for'],
        'stipend': float(cleaned['stipend']),
        'paid': cleaned.get('paid', False),
        'notes': cleaned.get('notes') or '',
    }
    data.setdefault('intentions', []).append(item)
    return item


def delete_intention(data: dict, intention_id: str) -> bool:
    previous_count = len(data.get('intentions', []))
    data['intentions'] = [
        intention
        for intention in data.get('intentions', [])
        if intention.get('id') != intention_id
    ]
    return len(data['intentions']) < previous_count


def toggle_intention_paid(data: dict, intention_id: str) -> bool:
    intention = next(
        (
            intention_record
            for intention_record in data.get('intentions', [])
            if intention_record.get('id') == intention_id
        ),
        None,
    )
    if not intention:
        return False
    intention['paid'] = not intention.get('paid')
    if intention['paid']:
        intention['paymentId'] = (
            intention.get('paymentId')
            or f"MAN-{uuid.uuid4().hex[:6].upper()}"
        )
        intention['paidAt'] = datetime.now(timezone.utc).isoformat()
    return True
