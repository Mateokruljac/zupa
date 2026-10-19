"""Laka vremenska traka članstva kućanstva iz SCD2 verzija.

Samo pastoralno bitni događaji: dolazak, odlazak i promjena odnosa.
Ispravke imena, redoslijeda i sitnih polja se namjerno ne prikazuju.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from django.db import DatabaseError

from core.models import OPEN_ENDED_VALID_TO
from zupa_vjernici.models import Household, HouseholdMembership

EVENT_JOINED = 'joined'
EVENT_LEFT = 'left'
EVENT_RELATION_CHANGED = 'relation_changed'

_EVENT_LABELS = {
    EVENT_JOINED: 'Dodan/a u kućanstvo',
    EVENT_LEFT: 'Napustio/la kućanstvo',
    EVENT_RELATION_CHANGED: 'Promjena odnosa',
}


def _iso(value) -> str:
    if not value:
        return ''
    return value.isoformat() if hasattr(value, 'isoformat') else str(value)


def _display_name(membership: HouseholdMembership) -> str:
    return (
        (membership.historical_name or '').strip()
        or str(membership.public_identifier or '')
    )


def build_membership_timeline(
    versions: list[HouseholdMembership],
    *,
    limit: int = 40,
) -> list[dict]:
    """Iz SCD2 redova sastavi događaje sorted od najnovijeg."""
    by_member: dict[str, list[HouseholdMembership]] = defaultdict(list)
    for membership in versions:
        member_id = membership.public_identifier or ''
        if not member_id:
            continue
        by_member[member_id].append(membership)

    events: list[dict] = []
    for member_id, chain in by_member.items():
        chain.sort(
            key=lambda row: (
                row.date_from or OPEN_ENDED_VALID_TO,
                row.created_at or row.date_from or OPEN_ENDED_VALID_TO,
            ),
        )
        first = chain[0]
        name = _display_name(first)
        events.append({
            'id': f'{member_id}:{EVENT_JOINED}:{_iso(first.date_from)}',
            'type': EVENT_JOINED,
            'at': _iso(first.date_from),
            'memberId': member_id,
            'name': name,
            'relation': first.role or '',
            'relationFrom': '',
            'relationTo': first.role or '',
            'label': _EVENT_LABELS[EVENT_JOINED],
            'detail': first.role or '',
        })
        for previous, current in zip(chain, chain[1:]):
            previous_role = (previous.role or '').strip()
            current_role = (current.role or '').strip()
            if previous_role == current_role:
                continue
            name = _display_name(current)
            events.append({
                'id': (
                    f'{member_id}:{EVENT_RELATION_CHANGED}:'
                    f'{_iso(current.date_from)}'
                ),
                'type': EVENT_RELATION_CHANGED,
                'at': _iso(current.date_from),
                'memberId': member_id,
                'name': name,
                'relation': current_role,
                'relationFrom': previous_role,
                'relationTo': current_role,
                'label': _EVENT_LABELS[EVENT_RELATION_CHANGED],
                'detail': (
                    f'{previous_role} → {current_role}'
                    if previous_role and current_role
                    else current_role or previous_role
                ),
            })
        latest = chain[-1]
        if latest.date_to and latest.date_to != OPEN_ENDED_VALID_TO:
            left_on = latest.date_to + timedelta(days=1)
            name = _display_name(latest)
            events.append({
                'id': f'{member_id}:{EVENT_LEFT}:{_iso(left_on)}',
                'type': EVENT_LEFT,
                'at': _iso(left_on),
                'memberId': member_id,
                'name': name,
                'relation': latest.role or '',
                'relationFrom': '',
                'relationTo': latest.role or '',
                'label': _EVENT_LABELS[EVENT_LEFT],
                'detail': latest.role or '',
            })

    events.sort(
        key=lambda event: (event.get('at') or '', event.get('id') or ''),
        reverse=True,
    )
    return events[:limit]


def membership_timeline_for_family(family_public_identifier: str) -> list[dict]:
    """Učitaj SCD2 članstva obitelji i vrati timeline događaje."""
    family_id = (family_public_identifier or '').strip()
    if not family_id:
        return []
    try:
        household = (
            Household.current.filter(public_identifier=family_id).first()
            or Household.objects.filter(public_identifier=family_id)
            .order_by('-date_from')
            .first()
        )
        if household is None:
            return []
        versions = list(
            HouseholdMembership.objects.filter(household_id=household.pk)
            .order_by('public_identifier', 'date_from', 'created_at')
        )
    except DatabaseError:
        return []
    return build_membership_timeline(versions)
