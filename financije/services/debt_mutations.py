"""Mutacije dugovanja u parish JSON podacima."""
from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone

from pastoral.services.dates import today_iso


def mark_debt_paid(data: dict, source: dict) -> bool:
    if not source:
        return False
    source_type = source.get('type')
    if source_type == 'contribution':
        family = next(
            (
                family_record
                for family_record in data.get('families', [])
                if family_record.get('id') == source.get('familyId')
            ),
            None,
        )
        if not family:
            return False
        contribution = next(
            (
                contribution_record
                for contribution_record in family.get('contributions', [])
                if contribution_record.get('year') == source.get('year')
            ),
            None,
        )
        if not contribution:
            return False
        contribution['luknoPaid'] = True
        contribution['luknoPaidAt'] = today_iso()
        return True
    if source_type == 'intention':
        intention = next(
            (
                intention_record
                for intention_record in data.get('intentions', [])
                if intention_record.get('id') == source.get('id')
            ),
            None,
        )
        if not intention:
            return False
        intention['paid'] = True
        intention['paymentId'] = (
            intention.get('paymentId')
            or f"MAN-{uuid.uuid4().hex[:6].upper()}"
        )
        intention['paidAt'] = datetime.now(timezone.utc).isoformat()
        return True
    if source_type in ('baptisms', 'weddings', 'funerals'):
        sacrament_record = next(
            (
                record
                for record in data.get(source_type, [])
                if record.get('id') == source.get('id')
            ),
            None,
        )
        if not sacrament_record:
            return False
        sacrament_record['stipendPaid'] = True
        sacrament_record['stipendPaidAt'] = today_iso()
        return True
    if source_type == 'firstCommunion':
        group = next(
            (
                group_record
                for group_record in data.get('firstCommunion', [])
                if group_record.get('id') == source.get('id')
            ),
            None,
        )
        if not group:
            return False
        group['groupFeePaid'] = True
        group['groupFeePaidAt'] = today_iso()
        return True
    if source_type == 'confirmations':
        group = next(
            (
                group_record
                for group_record in data.get('confirmations', [])
                if group_record.get('id') == source.get('id')
            ),
            None,
        )
        if not group:
            return False
        group['groupFeePaid'] = True
        group['groupFeePaidAt'] = today_iso()
        return True
    if source_type == 'parishDebts':
        parish_debt = next(
            (
                debt_record
                for debt_record in data.get('parishDebts', [])
                if debt_record.get('id') == source.get('id')
            ),
            None,
        )
        if not parish_debt:
            return False
        parish_debt['paid'] = True
        parish_debt['paidAt'] = today_iso()
        return True
    return False


def parse_debt_source(raw: str) -> dict | None:
    try:
        source = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    return source if isinstance(source, dict) else None


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
        'dueDate': (
            cleaned['due_date'].isoformat()
            if cleaned.get('due_date')
            else ''
        ),
        'year': (
            cleaned['due_date'].year
            if cleaned.get('due_date')
            else date.today().year
        ),
    }
    data.setdefault('parishDebts', []).append(item)
    return item
