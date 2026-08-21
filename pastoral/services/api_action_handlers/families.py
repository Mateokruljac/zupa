"""API mutacije obitelji, članova, doprinosa i rodbinskih veza."""
from __future__ import annotations

from datetime import date

from pastoral.services.api_action_handlers.shared import (
    DEFAULT_ANNUAL_CONTRIBUTION_AMOUNT,
    find_family,
    generate_record_identifier,
    normalize_date_value,
    synchronize_parishioners,
)
from pastoral.services.dates import today_iso


def create_family(parish_data: dict, action_payload: dict) -> dict:
    current_year = date.today().year
    family = {
        'id': generate_record_identifier('fam'),
        'surname': (action_payload.get('surname') or '').strip(),
        'streetId': (
            action_payload.get('street_id')
            or action_payload.get('streetId')
            or ''
        ),
        'address': (action_payload.get('address') or '').strip(),
        'phone': (action_payload.get('phone') or '').strip(),
        'email': (action_payload.get('email') or '').strip(),
        'status': 'aktivna',
        'preferredMass': '',
        'pastoralNotes': (
            action_payload.get('pastoral_notes')
            or action_payload.get('pastoralNotes')
            or ''
        ).strip(),
        'originPlace': (
            action_payload.get('origin_place')
            or action_payload.get('originPlace')
            or ''
        ).strip(),
        'createdAt': today_iso(),
        'tags': action_payload.get('tags') or [],
        'relatives': [],
        'husband': None,
        'wife': None,
        'members': [],
        'contributions': [],
    }
    if action_payload.get('status') in {'aktivna', 'neaktivna'}:
        family['status'] = action_payload['status']
    if not family['surname']:
        return {'ok': False, 'error': 'surname_required'}

    annual_contribution = {
        'id': generate_record_identifier('yc'),
        'year': current_year,
        'luknoPaid': bool(
            action_payload.get('lukno_paid')
            or action_payload.get('luknoPaid')
        ),
        'luknoAmount': float(
            action_payload.get('lukno_amount')
            or action_payload.get('luknoAmount')
            or DEFAULT_ANNUAL_CONTRIBUTION_AMOUNT
        ),
        'luknoPaidAt': (
            today_iso()
            if action_payload.get('lukno_paid')
            or action_payload.get('luknoPaid')
            else ''
        ),
        'churchDonation': float(
            action_payload.get('church_donation')
            or action_payload.get('churchDonation')
            or 0
        ),
        'donationDate': '',
        'notes': '',
    }
    family['contributions'].append(annual_contribution)
    parish_data.setdefault('families', []).append(family)
    synchronize_parishioners(parish_data)
    return {'ok': True, 'item': family}


def update_family(parish_data: dict, action_payload: dict) -> dict:
    family = find_family(parish_data, action_payload.get('id'))
    if not family:
        return {'ok': False, 'error': 'not_found'}

    field_mappings = (
        ('surname', 'surname'),
        ('streetId', 'street_id'),
        ('streetId', 'streetId'),
        ('address', 'address'),
        ('phone', 'phone'),
        ('email', 'email'),
        ('status', 'status'),
        ('preferredMass', 'preferred_mass'),
        ('preferredMass', 'preferredMass'),
        ('pastoralNotes', 'pastoral_notes'),
        ('pastoralNotes', 'pastoralNotes'),
        ('originPlace', 'origin_place'),
        ('originPlace', 'originPlace'),
    )
    for destination_field, source_field in field_mappings:
        if source_field in action_payload:
            family[destination_field] = action_payload[source_field]
    if 'tags' in action_payload:
        family['tags'] = (
            action_payload['tags']
            if isinstance(action_payload['tags'], list)
            else [
                tag.strip()
                for tag in str(action_payload['tags']).split(',')
                if tag.strip()
            ]
        )
    synchronize_parishioners(parish_data)
    return {'ok': True, 'item': family}


def delete_family(parish_data: dict, action_payload: dict) -> dict:
    family_id = action_payload.get('id') or action_payload.get('family_id')
    parish_data['families'] = [
        family
        for family in parish_data.get('families', [])
        if family.get('id') != family_id
    ]
    synchronize_parishioners(parish_data)
    return {'ok': True}


def upsert_family_member(parish_data: dict, action_payload: dict) -> dict:
    family = find_family(
        parish_data,
        action_payload.get('family_id') or action_payload.get('fam_id'),
    )
    if not family:
        return {'ok': False, 'error': 'not_found'}

    family_member_payload = {
        'name': (action_payload.get('name') or '').strip(),
        'relation': (action_payload.get('relation') or '').strip(),
        'birthYear': (
            action_payload.get('birth_year')
            or action_payload.get('birthYear')
            or ''
        ),
        'roles': action_payload.get('roles') or [],
        'notes': (action_payload.get('notes') or '').strip(),
    }
    family_member_id = (
        action_payload.get('id') or action_payload.get('member_id')
    )
    if family_member_id:
        family_member = next(
            (
                existing_member
                for existing_member in family.get('members') or []
                if existing_member.get('id') == family_member_id
            ),
            None,
        )
        if not family_member:
            return {'ok': False, 'error': 'not_found'}
        family_member.update(family_member_payload)
    else:
        family_member = {
            'id': generate_record_identifier('m'),
            'sacraments': [],
            **family_member_payload,
        }
        family.setdefault('members', []).append(family_member)
    synchronize_parishioners(parish_data)
    return {'ok': True, 'item': family_member}


def delete_family_member(parish_data: dict, action_payload: dict) -> dict:
    family = find_family(
        parish_data,
        action_payload.get('family_id') or action_payload.get('fam_id'),
    )
    if not family:
        return {'ok': False, 'error': 'not_found'}
    family_member_id = (
        action_payload.get('id') or action_payload.get('member_id')
    )
    family['members'] = [
        family_member
        for family_member in family.get('members') or []
        if family_member.get('id') != family_member_id
    ]
    synchronize_parishioners(parish_data)
    return {'ok': True}


def upsert_contribution(parish_data: dict, action_payload: dict) -> dict:
    family = find_family(
        parish_data,
        action_payload.get('family_id') or action_payload.get('fam_id'),
    )
    if not family:
        return {'ok': False, 'error': 'not_found'}
    contribution_year = int(
        action_payload.get('year') or date.today().year
    )
    annual_contribution = next(
        (
            contribution
            for contribution in family.get('contributions') or []
            if contribution.get('year') == contribution_year
        ),
        None,
    )
    if not annual_contribution:
        annual_contribution = {
            'id': generate_record_identifier('yc'),
            'year': contribution_year,
        }
        family.setdefault('contributions', []).append(annual_contribution)
    annual_contribution['luknoPaid'] = bool(
        action_payload.get('lukno_paid')
        or action_payload.get('luknoPaid')
    )
    annual_contribution['luknoAmount'] = float(
        action_payload.get('lukno_amount')
        or action_payload.get('luknoAmount')
        or DEFAULT_ANNUAL_CONTRIBUTION_AMOUNT
    )
    annual_contribution['luknoPaidAt'] = normalize_date_value(
        action_payload.get('lukno_paid_at')
        or action_payload.get('luknoPaidAt')
    )
    if (
        annual_contribution['luknoPaid']
        and not annual_contribution['luknoPaidAt']
    ):
        annual_contribution['luknoPaidAt'] = today_iso()
    annual_contribution['churchDonation'] = float(
        action_payload.get('church_donation')
        or action_payload.get('churchDonation')
        or 0
    )
    annual_contribution['donationDate'] = normalize_date_value(
        action_payload.get('donation_date')
        or action_payload.get('donationDate')
    )
    annual_contribution['notes'] = (
        action_payload.get('notes') or ''
    ).strip()
    family['contributions'].sort(
        key=lambda contribution: contribution.get('year', 0),
        reverse=True,
    )
    return {'ok': True, 'item': annual_contribution}


def delete_contribution(parish_data: dict, action_payload: dict) -> dict:
    family = find_family(
        parish_data,
        action_payload.get('family_id') or action_payload.get('fam_id'),
    )
    if not family:
        return {'ok': False, 'error': 'not_found'}
    contribution_year = int(action_payload.get('year'))
    family['contributions'] = [
        contribution
        for contribution in family.get('contributions') or []
        if contribution.get('year') != contribution_year
    ]
    return {'ok': True}


def update_spouse(parish_data: dict, action_payload: dict) -> dict:
    family = find_family(
        parish_data,
        action_payload.get('family_id') or action_payload.get('fam_id'),
    )
    if not family:
        return {'ok': False, 'error': 'not_found'}
    spouse_type = (
        action_payload.get('which')
        or action_payload.get('spouse')
        or 'husband'
    )
    spouse_fields = (
        'name',
        'birthYear',
        'birthPlace',
        'baptismDate',
        'baptismPlace',
        'weddingChurch',
        'notes',
    )
    family[spouse_type] = {
        field_name: action_payload.get(field_name, '')
        for field_name in spouse_fields
    }
    return {'ok': True}


def upsert_relative(parish_data: dict, action_payload: dict) -> dict:
    family = find_family(
        parish_data,
        action_payload.get('family_id') or action_payload.get('fam_id'),
    )
    if not family:
        return {'ok': False, 'error': 'not_found'}
    relative_payload = {
        'name': (action_payload.get('name') or '').strip(),
        'relation': (action_payload.get('relation') or '').strip(),
        'birthYear': (
            action_payload.get('birth_year')
            or action_payload.get('birthYear')
            or ''
        ),
        'notes': (action_payload.get('notes') or '').strip(),
    }
    relative_id = action_payload.get('id')
    if relative_id:
        relative = next(
            (
                existing_relative
                for existing_relative in family.get('relatives') or []
                if existing_relative.get('id') == relative_id
            ),
            None,
        )
        if not relative:
            return {'ok': False, 'error': 'not_found'}
        relative.update(relative_payload)
    else:
        relative = {
            'id': generate_record_identifier('rel'),
            **relative_payload,
        }
        family.setdefault('relatives', []).append(relative)
    return {'ok': True, 'item': relative}


def delete_relative(parish_data: dict, action_payload: dict) -> dict:
    family = find_family(
        parish_data,
        action_payload.get('family_id') or action_payload.get('fam_id'),
    )
    if not family:
        return {'ok': False, 'error': 'not_found'}
    relative_id = action_payload.get('id')
    family['relatives'] = [
        relative
        for relative in family.get('relatives') or []
        if relative.get('id') != relative_id
    ]
    return {'ok': True}


def update_family_notes(parish_data: dict, action_payload: dict) -> dict:
    family = find_family(
        parish_data,
        action_payload.get('family_id') or action_payload.get('fam_id'),
    )
    if not family:
        return {'ok': False, 'error': 'not_found'}
    family['pastoralNotes'] = (
        action_payload.get('pastoral_notes')
        or action_payload.get('pastoralNotes')
        or ''
    ).strip()
    return {'ok': True}
