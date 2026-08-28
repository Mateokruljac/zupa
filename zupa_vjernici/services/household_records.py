"""Pretvorba Household / PastoralVisit ORM ↔ legacy API dict."""
from __future__ import annotations

import copy
from datetime import date
from decimal import Decimal, InvalidOperation

from zupa_vjernici.models import (
    Household,
    HouseholdContribution,
    HouseholdMember,
    HouseholdRelative,
    PastoralVisit,
)


def _parse_iso_date(value) -> date | None:
    raw = str(value or '').strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _iso_or_empty(value: date | None) -> str:
    return value.isoformat() if value else ''


def _decimal_amount(value) -> Decimal:
    try:
        return Decimal(str(value if value is not None else 0))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


def _string_or_empty(value) -> str:
    if value is None:
        return ''
    return str(value)


def member_as_legacy_record(member: HouseholdMember) -> dict:
    birth_year = member.birth_year
    if birth_year.isdigit():
        birth_year_value: int | str = int(birth_year)
    else:
        birth_year_value = birth_year
    return {
        'id': member.public_identifier,
        'name': member.name or '',
        'birthYear': birth_year_value,
        'relation': member.relation or '',
        'sacraments': list(member.sacraments or []),
        'roles': list(member.roles or []),
        'notes': member.notes or '',
    }


def contribution_as_legacy_record(contribution: HouseholdContribution) -> dict:
    return {
        'id': contribution.public_identifier,
        'year': contribution.year,
        'luknoPaid': bool(contribution.lukno_paid),
        'luknoAmount': float(contribution.lukno_amount or 0),
        'luknoPaidAt': _iso_or_empty(contribution.lukno_paid_at),
        'churchDonation': float(contribution.church_donation or 0),
        'donationDate': _iso_or_empty(contribution.donation_date),
        'notes': contribution.notes or '',
    }


def relative_as_legacy_record(relative: HouseholdRelative) -> dict:
    return {
        'id': relative.public_identifier,
        'name': relative.name or '',
        'relation': relative.relation or '',
        'birthYear': relative.birth_year or '',
        'notes': relative.notes or '',
    }


def household_as_legacy_record(household: Household) -> dict:
    return {
        'id': household.public_identifier,
        'surname': household.surname or '',
        'streetId': household.street_public_identifier or '',
        'address': household.address or '',
        'phone': household.phone or '',
        'email': household.email or '',
        'status': household.status or 'aktivna',
        'preferredMass': household.preferred_mass or '',
        'pastoralNotes': household.pastoral_notes or '',
        'originPlace': household.origin_place or '',
        'lastVisit': _iso_or_empty(household.last_visit_on),
        'tags': list(household.tags or []),
        'husband': copy.deepcopy(household.husband or {}),
        'wife': copy.deepcopy(household.wife or {}),
        'members': [
            member_as_legacy_record(member)
            for member in household.members.all()
        ],
        'contributions': [
            contribution_as_legacy_record(contribution)
            for contribution in household.contributions.all()
        ],
        'relatives': [
            relative_as_legacy_record(relative)
            for relative in household.relatives.all()
        ],
    }


def household_field_defaults_from_legacy(record: dict, street=None) -> dict:
    return {
        'surname': str(record.get('surname') or ''),
        'street': street,
        'street_public_identifier': str(record.get('streetId') or ''),
        'address': str(record.get('address') or ''),
        'phone': str(record.get('phone') or ''),
        'email': str(record.get('email') or ''),
        'status': str(record.get('status') or 'aktivna'),
        'preferred_mass': str(record.get('preferredMass') or ''),
        'pastoral_notes': str(record.get('pastoralNotes') or ''),
        'origin_place': str(record.get('originPlace') or ''),
        'last_visit_on': _parse_iso_date(record.get('lastVisit')),
        'tags': list(record.get('tags') or [])
        if isinstance(record.get('tags'), list)
        else [],
        'husband': copy.deepcopy(record.get('husband') or {})
        if isinstance(record.get('husband'), dict)
        else {},
        'wife': copy.deepcopy(record.get('wife') or {})
        if isinstance(record.get('wife'), dict)
        else {},
        'payload': {},
    }


def sync_household_nested_records(household: Household, record: dict) -> None:
    members = record.get('members') if isinstance(record.get('members'), list) else []
    keep_members = set()
    for index, member_record in enumerate(members):
        if not isinstance(member_record, dict):
            continue
        public_identifier = str(
            member_record.get('id') or f'm-{household.public_identifier}-{index + 1}'
        )
        keep_members.add(public_identifier)
        HouseholdMember.objects.update_or_create(
            household=household,
            public_identifier=public_identifier,
            defaults={
                'name': str(member_record.get('name') or ''),
                'birth_year': _string_or_empty(member_record.get('birthYear')),
                'relation': str(member_record.get('relation') or ''),
                'sacraments': list(member_record.get('sacraments') or [])
                if isinstance(member_record.get('sacraments'), list)
                else [],
                'roles': list(member_record.get('roles') or [])
                if isinstance(member_record.get('roles'), list)
                else [],
                'notes': str(member_record.get('notes') or ''),
                'sort_order': index,
            },
        )
    household.members.exclude(public_identifier__in=keep_members).delete()

    contributions = (
        record.get('contributions')
        if isinstance(record.get('contributions'), list)
        else []
    )
    keep_contributions = set()
    for index, contribution_record in enumerate(contributions):
        if not isinstance(contribution_record, dict):
            continue
        public_identifier = str(
            contribution_record.get('id')
            or f'yc-{household.public_identifier}-{index + 1}'
        )
        keep_contributions.add(public_identifier)
        year_raw = contribution_record.get('year')
        try:
            year_value = int(year_raw) if year_raw not in (None, '') else 0
        except (TypeError, ValueError):
            year_value = 0
        HouseholdContribution.objects.update_or_create(
            household=household,
            public_identifier=public_identifier,
            defaults={
                'year': year_value,
                'lukno_paid': bool(contribution_record.get('luknoPaid')),
                'lukno_amount': _decimal_amount(
                    contribution_record.get('luknoAmount')
                ),
                'lukno_paid_at': _parse_iso_date(
                    contribution_record.get('luknoPaidAt')
                ),
                'church_donation': _decimal_amount(
                    contribution_record.get('churchDonation')
                ),
                'donation_date': _parse_iso_date(
                    contribution_record.get('donationDate')
                ),
                'notes': str(contribution_record.get('notes') or ''),
            },
        )
    household.contributions.exclude(
        public_identifier__in=keep_contributions,
    ).delete()

    relatives = (
        record.get('relatives')
        if isinstance(record.get('relatives'), list)
        else []
    )
    keep_relatives = set()
    for index, relative_record in enumerate(relatives):
        if not isinstance(relative_record, dict):
            continue
        public_identifier = str(
            relative_record.get('id')
            or f'rel-{household.public_identifier}-{index + 1}'
        )
        keep_relatives.add(public_identifier)
        HouseholdRelative.objects.update_or_create(
            household=household,
            public_identifier=public_identifier,
            defaults={
                'name': str(relative_record.get('name') or ''),
                'relation': str(relative_record.get('relation') or ''),
                'birth_year': _string_or_empty(relative_record.get('birthYear')),
                'notes': str(relative_record.get('notes') or ''),
                'sort_order': index,
            },
        )
    household.relatives.exclude(public_identifier__in=keep_relatives).delete()


def visit_as_legacy_record(visit: PastoralVisit) -> dict:
    return {
        'id': visit.public_identifier,
        'scheduled': _iso_or_empty(visit.scheduled_on),
        'type': visit.visit_type or '',
        'person': visit.person_name or '',
        'familyId': visit.family_public_identifier or '',
        'address': visit.address or '',
        'priest': visit.priest or '',
        'purpose': visit.purpose or '',
        'done': bool(visit.is_done),
        'report': visit.report or '',
    }


def visit_field_defaults_from_legacy(record: dict, household=None) -> dict:
    return {
        'household': household,
        'family_public_identifier': str(record.get('familyId') or ''),
        'scheduled_on': _parse_iso_date(record.get('scheduled')),
        'is_done': bool(record.get('done')),
        'visit_type': str(record.get('type') or ''),
        'person_name': str(record.get('person') or ''),
        'address': str(record.get('address') or ''),
        'priest': str(record.get('priest') or ''),
        'purpose': str(record.get('purpose') or ''),
        'report': str(record.get('report') or ''),
        'payload': {},
    }
