"""Spremanje jedne kartice obitelji i njezin prikaz za modal."""
from __future__ import annotations

from datetime import date

from django.db import transaction
from django.forms import Form

from django_multitenant.schema import with_tenant_schema
from pastoral.services.api_action_handlers.shared import find_family
from pastoral.services.data import ParishDataService
from zupa_vjernici.forms import (
    FamilyContributionForm,
    FamilyForm,
    FamilyMemberForm,
    FamilyNotesForm,
)
from zupa_vjernici.services.api_action_handlers.families import (
    update_family,
    update_family_notes,
    upsert_contribution,
    upsert_family_member,
)


class FamilyCardRejected(Exception):
    def __init__(self, status_code: int, code: str, fields: dict | None = None):
        self.status_code = status_code
        self.code = code
        self.fields = fields or {}


def family_card_snapshot(parish_data: dict, family: dict, year: int) -> dict:
    """Podaci koje modal prikazuje za jednu obitelj."""
    streets = {
        street.get('id'): street
        for street in parish_data.get('streets') or []
        if street.get('id')
    }
    street = streets.get(family.get('streetId'))
    contributions = sorted(
        list(family.get('contributions') or []),
        key=lambda contribution: contribution.get('year') or 0,
        reverse=True,
    )
    current_contribution = next(
        (
            contribution
            for contribution in contributions
            if contribution.get('year') == year
        ),
        None,
    )
    if current_contribution is None:
        lukno_status = 'none'
    elif current_contribution.get('luknoPaid'):
        lukno_status = 'paid'
    else:
        lukno_status = 'unpaid'
    data_gaps = []
    if not family.get('phone'):
        data_gaps.append('telefon')
    if not family.get('email'):
        data_gaps.append('e-mail')
    if not family.get('streetId'):
        data_gaps.append('teritorijalna pripadnost')
    return {
        'id': family.get('id') or '',
        'surname': family.get('surname') or '',
        'address': family.get('address') or '',
        'phone': family.get('phone') or '',
        'email': family.get('email') or '',
        'status': family.get('status') or 'aktivna',
        'streetId': family.get('streetId') or '',
        'streetName': (street or {}).get('name') or '',
        'pastoralNotes': family.get('pastoralNotes') or '',
        'dataGaps': data_gaps,
        'currentYear': year,
        'luknoStatus': lukno_status,
        'members': [
            {
                'id': member.get('id') or '',
                'givenName': member.get('givenName') or '',
                'surname': member.get('surname') or '',
                'name': member.get('name') or '',
                'relation': member.get('relation') or '',
                'birthDate': member.get('birthDate') or '',
                'birthYear': str(member.get('birthYear') or ''),
            }
            for member in family.get('members') or []
        ],
        'contributions': [
            {
                'year': int(contribution.get('year') or 0),
                'luknoAmount': float(contribution.get('luknoAmount') or 0),
                'luknoPaid': bool(contribution.get('luknoPaid')),
                'luknoPaidAt': contribution.get('luknoPaidAt') or '',
                'churchDonation': float(contribution.get('churchDonation') or 0),
                'donationDate': contribution.get('donationDate') or '',
                'notes': contribution.get('notes') or '',
            }
            for contribution in contributions
        ],
    }


def _require_form(form: Form) -> dict:
    if form.is_valid():
        return form.cleaned_data
    raise FamilyCardRejected(
        422,
        'invalid',
        {
            field_name: [str(error) for error in errors]
            for field_name, errors in form.errors.items()
        },
    )


def _require_saved(action_result: dict) -> None:
    if action_result.get('ok'):
        return
    raise FamilyCardRejected(400, action_result.get('error') or 'not_saved')


@with_tenant_schema
def _save_family_change(request, family_id: str, apply) -> dict:
    parish_data_service = ParishDataService.for_request(request)
    with transaction.atomic():
        parish_data_service.lock_for_update()
        parish_data = parish_data_service.load()
        if find_family(parish_data, family_id) is None:
            raise FamilyCardRejected(404, 'not_found')
        apply(parish_data)
        parish_data_service.save(parish_data)
    parish_data = parish_data_service.load()
    family = find_family(parish_data, family_id)
    if family is None:
        raise FamilyCardRejected(404, 'not_found')
    return family_card_snapshot(parish_data, family, date.today().year)


def save_family_basics(request, family_id: str, form_data: dict) -> dict:
    def apply(parish_data: dict) -> None:
        family_form = FamilyForm(form_data, streets=parish_data.get('streets') or [])
        cleaned_data = _require_form(family_form)
        _require_saved(update_family(parish_data, {
            'id': family_id,
            'surname': cleaned_data.get('surname') or '',
            'street_id': cleaned_data.get('street_id') or '',
            'address': cleaned_data.get('address') or '',
            'phone': cleaned_data.get('phone') or '',
            'email': cleaned_data.get('email') or '',
            'status': cleaned_data.get('status') or 'aktivna',
        }))

    return _save_family_change(request, family_id, apply)


def save_family_member_card(request, family_id: str, form_data: dict) -> dict:
    def apply(parish_data: dict) -> None:
        member_form = FamilyMemberForm(form_data)
        cleaned_data = _require_form(member_form)
        birth_date = cleaned_data.get('birth_date')
        _require_saved(upsert_family_member(parish_data, {
            'family_id': family_id,
            'member_id': form_data.get('member_id') or '',
            'given_name': cleaned_data.get('given_name') or '',
            'surname': cleaned_data.get('surname') or '',
            'relation': cleaned_data.get('relation') or '',
            'birth_date': birth_date.isoformat() if birth_date else '',
        }))

    return _save_family_change(request, family_id, apply)


def save_family_contribution_card(request, family_id: str, form_data: dict) -> dict:
    def apply(parish_data: dict) -> None:
        contribution_form = FamilyContributionForm(form_data)
        cleaned_data = _require_form(contribution_form)
        lukno_paid_at = cleaned_data.get('lukno_paid_at')
        donation_date = cleaned_data.get('donation_date')
        _require_saved(upsert_contribution(parish_data, {
            'family_id': family_id,
            'year': cleaned_data['year'],
            'lukno_amount': cleaned_data['lukno_amount'],
            'lukno_paid': cleaned_data.get('lukno_paid', False),
            'lukno_paid_at': lukno_paid_at.isoformat() if lukno_paid_at else '',
            'church_donation': cleaned_data.get('church_donation') or 0,
            'donation_date': donation_date.isoformat() if donation_date else '',
            'notes': cleaned_data.get('notes') or '',
        }))

    return _save_family_change(request, family_id, apply)


def save_family_notes_card(request, family_id: str, form_data: dict) -> dict:
    def apply(parish_data: dict) -> None:
        notes_form = FamilyNotesForm(form_data)
        cleaned_data = _require_form(notes_form)
        _require_saved(update_family_notes(parish_data, {
            'family_id': family_id,
            'pastoral_notes': cleaned_data.get('pastoral_notes') or '',
        }))

    return _save_family_change(request, family_id, apply)
