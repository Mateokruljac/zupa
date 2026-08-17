"""Zajedničke pomoćne funkcije API mutacija župnih podataka."""
from __future__ import annotations

from datetime import date
import uuid

from django.utils.dateparse import parse_date


DEFAULT_ANNUAL_CONTRIBUTION_AMOUNT = 150


def generate_record_identifier(record_prefix: str) -> str:
    return f"{record_prefix}_{uuid.uuid4().hex[:8]}"


def normalize_date_value(date_value) -> str:
    if not date_value:
        return ''
    if hasattr(date_value, 'isoformat'):
        return date_value.isoformat()
    parsed_date = parse_date(str(date_value))
    return parsed_date.isoformat() if parsed_date else str(date_value)


def synchronize_parishioners(parish_data: dict) -> None:
    parishioners = []
    for family in parish_data.get('families', []):
        for family_member in family.get('members') or []:
            parishioners.append({
                'id': family_member.get('id'),
                'family': family.get('surname', ''),
                'name': family_member.get('name', ''),
                'phone': family.get('phone', ''),
                'email': family.get('email', ''),
                'status': (
                    'aktivan'
                    if family.get('status') == 'aktivna'
                    else family.get('status', '')
                ),
                'roles': family_member.get('roles') or [],
            })
    parish_data['parishioners'] = parishioners


def migrate_family_contributions(family: dict) -> None:
    if not isinstance(family.get('contributions'), list):
        family['contributions'] = []
    if not family['contributions']:
        current_year = date.today().year
        for contribution_year in (
            current_year - 2,
            current_year - 1,
            current_year,
        ):
            family['contributions'].append({
                'id': generate_record_identifier('yc'),
                'year': contribution_year,
                'luknoPaid': False,
                'luknoAmount': DEFAULT_ANNUAL_CONTRIBUTION_AMOUNT,
                'luknoPaidAt': '',
                'churchDonation': 0,
                'donationDate': '',
                'notes': '',
            })
    family['contributions'].sort(
        key=lambda contribution: contribution.get('year', 0),
        reverse=True,
    )


def normalize_parish_data(parish_data: dict) -> dict:
    for family in parish_data.get('families', []):
        migrate_family_contributions(family)
    synchronize_parishioners(parish_data)

    from pastoral.services.data_normalize import migrate_all
    migrate_all(parish_data)
    return parish_data


def find_family(parish_data: dict, family_id: str) -> dict | None:
    return next(
        (
            family
            for family in parish_data.get('families', [])
            if family.get('id') == family_id
        ),
        None,
    )


def find_confirmation_group(parish_data: dict, year: int) -> dict | None:
    return next(
        (
            confirmation_group
            for confirmation_group in parish_data.get('confirmations', [])
            if confirmation_group.get('year') == year
        ),
        None,
    )


def find_first_communion_group(parish_data: dict, year: int) -> dict | None:
    return next(
        (
            first_communion_group
            for first_communion_group in parish_data.get('firstCommunion', [])
            if first_communion_group.get('year') == year
        ),
        None,
    )


def generate_payment_reference() -> str:
    return f"PAY-{uuid.uuid4().hex[:8].upper()}"
