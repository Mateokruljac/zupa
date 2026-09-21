"""
Župno vijeće i osnivački dekret ↔ camelCase dict stranice Vijeća.

`Council` je SCD1 (jedan red po vrsti u župi). Članstvo je SCD2 i veže se
na `Person` kad ime to dopušta. Osnivački dekret nije spremište datoteka.
"""
from __future__ import annotations

from datetime import date

from core.models import close_current_scd2_rows, upsert_current_scd2
from ured.models import Council, CouncilMembership, ParishFoundingDecree
from zupa_vjernici.services.person_identity import find_or_create_person


def _parse_iso_date(value) -> date | None:
    raw = str(value or '').strip()
    if not raw or raw in {'—', '-'}:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _iso_or_empty(value: date | None) -> str:
    return value.isoformat() if value else ''


def membership_as_legacy_record(membership: CouncilMembership) -> dict:
    return {
        'id': membership.public_identifier,
        'name': membership.member_name or (
            str(membership.person) if membership.person_id else ''
        ),
        'role': membership.role or '',
        'phone': membership.phone or '',
        'confirmed': bool(membership.is_confirmed),
    }


def council_as_legacy_record(council: Council) -> dict:
    members = [
        membership_as_legacy_record(membership)
        for membership in CouncilMembership.current.filter(council=council)
    ]
    if council.council_type == Council.CouncilType.ECONOMIC:
        return {
            'budgetYear': council.budget_year,
            'lastReview': _iso_or_empty(council.last_meeting_on),
            'nextReview': _iso_or_empty(council.next_meeting_on),
            'members': members,
        }
    return {
        'established': _iso_or_empty(council.established_on),
        'lastMeeting': _iso_or_empty(council.last_meeting_on),
        'nextMeeting': _iso_or_empty(council.next_meeting_on),
        'members': members,
    }


def decree_as_legacy_record(decree: ParishFoundingDecree | None) -> dict:
    if decree is None:
        return {}
    return {
        'name': decree.official_name or '',
        'established': decree.established_text or '',
        'territory': decree.territory or '',
        'decreeRef': decree.decree_reference or '',
    }


def sync_council_from_legacy(parish, council_type: str, payload) -> None:
    """Spremi vijeće i otvorena članstva iz UI dicta.

    `payload is None` briše SCD1 vijeće. Članstva kojih više nema zatvaraju
    se umjesto DELETE, da ostane trag mandata.
    """
    if payload is None:
        Council.objects.filter(parish=parish, council_type=council_type).delete()
        return
    if not isinstance(payload, dict):
        payload = {}
    title = (
        'Župno ekonomsko vijeće'
        if council_type == Council.CouncilType.ECONOMIC
        else 'Župno pastoralno vijeće'
    )
    defaults = {
        'title': title,
        'established_on': _parse_iso_date(payload.get('established')),
        'last_meeting_on': _parse_iso_date(
            payload.get('lastMeeting') or payload.get('lastReview')
        ),
        'next_meeting_on': _parse_iso_date(
            payload.get('nextMeeting') or payload.get('nextReview')
        ),
    }
    budget_year = payload.get('budgetYear')
    try:
        defaults['budget_year'] = int(budget_year) if budget_year not in (None, '') else None
    except (TypeError, ValueError):
        defaults['budget_year'] = None
    council, _created = Council.objects.update_or_create(
        parish=parish,
        council_type=council_type,
        defaults=defaults,
    )
    members = payload.get('members') if isinstance(payload.get('members'), list) else []
    keep_identifiers = set()
    for index, member_record in enumerate(members):
        if not isinstance(member_record, dict):
            continue
        public_identifier = str(member_record.get('id') or f'{council_type}-{index + 1}')
        keep_identifiers.add(public_identifier)
        full_name = str(member_record.get('name') or '')
        person = find_or_create_person(
            parish,
            full_name=full_name,
            relation=str(member_record.get('role') or ''),
        )
        upsert_current_scd2(
            CouncilMembership,
            {
                'council': council,
                'public_identifier': public_identifier,
            },
            {
                'person': person,
                'member_name': full_name,
                'role': str(member_record.get('role') or ''),
                'phone': str(member_record.get('phone') or ''),
                'is_confirmed': bool(member_record.get('confirmed')),
            },
        )
    close_current_scd2_rows(
        council.memberships.exclude(public_identifier__in=keep_identifiers),
    )


def sync_founding_decree_from_legacy(parish, payload) -> None:
    if not isinstance(payload, dict) or not payload:
        ParishFoundingDecree.objects.filter(parish=parish).delete()
        return
    ParishFoundingDecree.objects.update_or_create(
        parish=parish,
        defaults={
            'official_name': str(payload.get('name') or ''),
            'established_text': str(payload.get('established') or ''),
            'territory': str(payload.get('territory') or ''),
            'decree_reference': str(payload.get('decreeRef') or ''),
        },
    )
