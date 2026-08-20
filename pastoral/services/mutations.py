"""Mutacije parish podataka — umjesto client-side save preko API-ja."""
from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone

from django.utils.dateparse import parse_date

from pastoral.services.dates import today_iso


def mark_debt_paid(data: dict, source: dict) -> bool:
    if not source:
        return False
    stype = source.get('type')
    if stype == 'contribution':
        fam = next((f for f in data.get('families', []) if f.get('id') == source.get('familyId')), None)
        if not fam:
            return False
        row = next((c for c in fam.get('contributions', []) if c.get('year') == source.get('year')), None)
        if not row:
            return False
        row['luknoPaid'] = True
        row['luknoPaidAt'] = today_iso()
        return True
    if stype == 'intention':
        n = next((x for x in data.get('intentions', []) if x.get('id') == source.get('id')), None)
        if not n:
            return False
        n['paid'] = True
        n['paymentId'] = n.get('paymentId') or f"MAN-{uuid.uuid4().hex[:6].upper()}"
        n['paidAt'] = datetime.now(timezone.utc).isoformat()
        return True
    if stype in ('baptisms', 'weddings', 'funerals'):
        n = next((x for x in data.get(stype, []) if x.get('id') == source.get('id')), None)
        if not n:
            return False
        n['stipendPaid'] = True
        n['stipendPaidAt'] = today_iso()
        return True
    if stype == 'firstCommunion':
        g = next((x for x in data.get('firstCommunion', []) if x.get('id') == source.get('id')), None)
        if not g:
            return False
        g['groupFeePaid'] = True
        g['groupFeePaidAt'] = today_iso()
        return True
    if stype == 'confirmations':
        g = next((x for x in data.get('confirmations', []) if x.get('id') == source.get('id')), None)
        if not g:
            return False
        g['groupFeePaid'] = True
        g['groupFeePaidAt'] = today_iso()
        return True
    if stype == 'parishDebts':
        d = next((x for x in data.get('parishDebts', []) if x.get('id') == source.get('id')), None)
        if not d:
            return False
        d['paid'] = True
        d['paidAt'] = today_iso()
        return True
    return False


def parse_debt_source(raw: str) -> dict | None:
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


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
    before = len(data.get('intentions', []))
    data['intentions'] = [n for n in data.get('intentions', []) if n.get('id') != intention_id]
    return len(data['intentions']) < before


def toggle_intention_paid(data: dict, intention_id: str) -> bool:
    n = next((x for x in data.get('intentions', []) if x.get('id') == intention_id), None)
    if not n:
        return False
    n['paid'] = not n.get('paid')
    if n['paid']:
        n['paymentId'] = n.get('paymentId') or f"MAN-{uuid.uuid4().hex[:6].upper()}"
        n['paidAt'] = datetime.now(timezone.utc).isoformat()
    return True


def add_parish_debt(data: dict, cleaned: dict) -> dict:
    item = {
        'id': f"pd_{uuid.uuid4().hex[:8]}",
        'direction': cleaned.get('direction') or 'payable',
        'category': cleaned.get('category') or 'ostalo',
        'label': cleaned['label'],
        'amount': float(cleaned['amount']),
        'paid': cleaned.get('paid', False),
        'notes': cleaned.get('notes') or '',
        'contact': cleaned.get('contact') or '',
        'dueDate': cleaned['due_date'].isoformat() if cleaned.get('due_date') else '',
        'year': cleaned['due_date'].year if cleaned.get('due_date') else date.today().year,
    }
    data.setdefault('parishDebts', []).append(item)
    return item


def delete_sacrament(data: dict, array_key: str, record_id: str) -> bool:
    before = len(data.get(array_key, []))
    data[array_key] = [r for r in data.get(array_key, []) if r.get('id') != record_id]
    return len(data[array_key]) < before


def add_sacrament_record(data: dict, array_key: str, fields: dict) -> dict:
    item = {'id': f"{array_key[:3]}_{uuid.uuid4().hex[:8]}", **fields}
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
    if record is None:
        return False
    record.update(fields)
    return True


def _parse_optional_date(value):
    if not value:
        return None
    if hasattr(value, 'isoformat'):
        return value
    return parse_date(str(value))
