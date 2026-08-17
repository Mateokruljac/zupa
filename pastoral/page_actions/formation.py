"""POST akcije obrazaca za krizmu i prvu pričest."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages

from pastoral.forms import (
    ConfirmationCandidateForm,
    ConfirmationGroupForm,
    FirstCommunionCandidateForm,
)
from pastoral.services.api_action_handlers.formation import (
    create_confirmation_year,
    update_confirmation_group,
    upsert_confirmation_candidate,
    upsert_first_communion_candidate,
)

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


def _optional_date(calendar_date) -> str:
    return calendar_date.isoformat() if calendar_date else ''


def handle_formation_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
    if page_slug == 'krizma' and action_name == 'save_confirmation_group':
        confirmation_group_form = ConfirmationGroupForm(request.POST)
        if confirmation_group_form.is_valid():
            cleaned_data = confirmation_group_form.cleaned_data
            action_payload = {
                'year': cleaned_data['year'],
                'ceremony_date': _optional_date(cleaned_data.get('ceremony_date')),
                'bishop': cleaned_data.get('bishop') or '',
                'group_fee': cleaned_data.get('group_fee') or 0,
                'group_fee_paid': cleaned_data.get('group_fee_paid', False),
            }
            action_result = update_confirmation_group(
                parish_data,
                action_payload,
            )
            if action_result.get('error') == 'not_found':
                action_result = create_confirmation_year(
                    parish_data,
                    action_payload,
                )
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Podaci godine krizme su spremljeni.')
            else:
                messages.error(request, 'Godina krizme nije mogla biti spremljena.')
        else:
            messages.error(
                request,
                'Provjerite samo podatke godine krizme; kandidati nisu mijenjani.',
            )
        return True

    if page_slug == 'krizma' and action_name == 'add_confirmation_candidate':
        confirmation_candidate_form = ConfirmationCandidateForm(request.POST)
        if confirmation_candidate_form.is_valid():
            cleaned_data = confirmation_candidate_form.cleaned_data
            action_result = upsert_confirmation_candidate(parish_data, {
                'year': cleaned_data['year'],
                'name': cleaned_data['name'],
                'birthDate': _optional_date(cleaned_data.get('birth_date')),
                'school': cleaned_data.get('school') or '',
                'class': cleaned_data.get('school_class') or '',
                'group': cleaned_data.get('formation_group') or '',
                'baptized': _optional_date(cleaned_data.get('baptism_date')),
                'sponsor': cleaned_data.get('sponsor') or '',
                'status': cleaned_data['status'],
                'oib': '',
            })
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Krizmanik je dodan u odabranu godinu.')
        else:
            messages.error(
                request,
                'Provjerite podatke krizmanika; podaci godine ostali su spremljeni.',
            )
        return True

    if (
        page_slug == 'prva-pricest'
        and action_name == 'add_first_communion_candidate'
    ):
        first_communion_candidate_form = FirstCommunionCandidateForm(
            request.POST
        )
        if first_communion_candidate_form.is_valid():
            cleaned_data = first_communion_candidate_form.cleaned_data
            full_name = (
                f"{cleaned_data['first_name']} {cleaned_data['last_name']}"
            ).strip()
            action_result = upsert_first_communion_candidate(parish_data, {
                'year': cleaned_data['year'],
                'fields': {
                    'firstName': cleaned_data['first_name'],
                    'lastName': cleaned_data['last_name'],
                    'name': full_name,
                    'school': cleaned_data.get('school') or '',
                    'class': cleaned_data.get('school_class') or '',
                    'parents': cleaned_data.get('parents') or '',
                    'status': cleaned_data.get('status') or 'priprema',
                    'paid': cleaned_data.get('paid', False),
                },
            })
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Prvopričesnik je dodan u odabranu godinu.')
        else:
            messages.error(request, 'Provjerite podatke prvopričesnika.')
        return True

    return False
