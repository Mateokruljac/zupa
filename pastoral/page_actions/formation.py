"""POST akcije obrazaca za krizmu i prvu pričest."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages

from pastoral.forms import (
    ConfirmationCandidateForm,
    ConfirmationGroupForm,
    ConfirmationYearForm,
    FirstCommunionCandidateForm,
    FirstCommunionGroupForm,
    FirstCommunionYearForm,
)
from pastoral.services.api_action_handlers.formation import (
    create_confirmation_year,
    create_first_communion_year,
    delete_confirmation_candidate,
    delete_first_communion_candidate,
    update_first_communion_group,
    update_confirmation_group,
    upsert_confirmation_candidate,
    upsert_first_communion_candidate,
)

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


def _optional_date(calendar_date) -> str:
    return calendar_date.isoformat() if calendar_date else ''


def _confirmation_candidate_payload(
    cleaned_data: dict,
    candidate_id: str = '',
    existing_oib: str = '',
) -> dict:
    return {
        'id': candidate_id,
        'year': cleaned_data['year'],
        'name': cleaned_data['name'],
        'birthDate': _optional_date(cleaned_data.get('birth_date')),
        'school': cleaned_data.get('school') or '',
        'class': cleaned_data.get('school_class') or '',
        'group': cleaned_data.get('formation_group') or '',
        'baptized': _optional_date(cleaned_data.get('baptism_date')),
        'sponsor': cleaned_data.get('sponsor') or '',
        'status': cleaned_data['status'],
        'oib': existing_oib,
    }


def _existing_confirmation_candidate_oib(
    parish_data: dict,
    confirmation_year: int,
    candidate_id: str,
) -> str:
    confirmation_group = next(
        (
            group
            for group in parish_data.get('confirmations', [])
            if group.get('year') == confirmation_year
        ),
        {},
    )
    confirmation_candidate = next(
        (
            candidate
            for candidate in confirmation_group.get('candidates', [])
            if candidate.get('id') == candidate_id
        ),
        {},
    )
    return confirmation_candidate.get('oib', '')


def _first_communion_candidate_payload(
    cleaned_data: dict,
    candidate_id: str = '',
) -> dict:
    first_name = cleaned_data['first_name']
    last_name = cleaned_data['last_name']
    return {
        'id': candidate_id,
        'year': cleaned_data['year'],
        'fields': {
            'firstName': first_name,
            'lastName': last_name,
            'name': f'{first_name} {last_name}'.strip(),
            'school': cleaned_data.get('school') or '',
            'class': cleaned_data.get('school_class') or '',
            'parents': cleaned_data.get('parents') or '',
            'status': cleaned_data.get('status') or 'priprema',
            'paid': cleaned_data.get('paid', False),
        },
    }


def handle_formation_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
    if page_slug == 'krizma' and action_name == 'add_confirmation_year':
        confirmation_year_form = ConfirmationYearForm(request.POST)
        if confirmation_year_form.is_valid():
            confirmation_year = confirmation_year_form.cleaned_data['year']
            action_result = create_confirmation_year(
                parish_data,
                {'year': confirmation_year},
            )
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(
                    request,
                    f'Godina krizme {confirmation_year} je dodana.',
                )
            else:
                messages.error(request, 'Ta godina krizme već postoji.')
        else:
            messages.error(request, 'Unesite ispravnu godinu krizme.')
        return True

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
            action_result = upsert_confirmation_candidate(
                parish_data,
                _confirmation_candidate_payload(cleaned_data),
            )
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Krizmanik je dodan u odabranu godinu.')
        else:
            messages.error(
                request,
                'Provjerite podatke krizmanika; podaci godine ostali su spremljeni.',
            )
        return True

    if page_slug == 'krizma' and action_name == 'update_confirmation_candidate':
        confirmation_candidate_form = ConfirmationCandidateForm(request.POST)
        if confirmation_candidate_form.is_valid():
            cleaned_data = confirmation_candidate_form.cleaned_data
            candidate_id = request.POST.get('candidate_id', '')
            action_result = upsert_confirmation_candidate(
                parish_data,
                _confirmation_candidate_payload(
                    cleaned_data,
                    candidate_id,
                    _existing_confirmation_candidate_oib(
                        parish_data,
                        cleaned_data['year'],
                        candidate_id,
                    ),
                ),
            )
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Podaci krizmanika su spremljeni.')
            else:
                messages.error(request, 'Krizmanik nije pronađen.')
        else:
            messages.error(request, 'Provjerite podatke krizmanika.')
        return True

    if page_slug == 'krizma' and action_name == 'delete_confirmation_candidate':
        action_result = delete_confirmation_candidate(parish_data, {
            'year': request.POST.get('year'),
            'id': request.POST.get('candidate_id', ''),
        })
        if action_result.get('ok'):
            parish_data_service.save(parish_data)
            messages.success(request, 'Krizmanik je obrisan.')
        else:
            messages.error(request, 'Krizmanik nije pronađen.')
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
            action_result = upsert_first_communion_candidate(
                parish_data,
                _first_communion_candidate_payload(cleaned_data),
            )
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Prvopričesnik je dodan u odabranu godinu.')
        else:
            messages.error(request, 'Provjerite podatke prvopričesnika.')
        return True

    if page_slug == 'prva-pricest' and action_name == 'add_first_communion_year':
        first_communion_year_form = FirstCommunionYearForm(request.POST)
        if first_communion_year_form.is_valid():
            first_communion_year = first_communion_year_form.cleaned_data['year']
            action_result = create_first_communion_year(
                parish_data,
                {'year': first_communion_year},
            )
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(
                    request,
                    f'Godina prve pričesti {first_communion_year} je dodana.',
                )
            else:
                messages.error(request, 'Ta godina prve pričesti već postoji.')
        else:
            messages.error(request, 'Unesite ispravnu godinu prve pričesti.')
        return True

    if page_slug == 'prva-pricest' and action_name == 'save_first_communion_group':
        first_communion_group_form = FirstCommunionGroupForm(request.POST)
        if first_communion_group_form.is_valid():
            cleaned_data = first_communion_group_form.cleaned_data
            action_result = update_first_communion_group(parish_data, {
                'year': cleaned_data['year'],
                'group_name': cleaned_data.get('group_name') or '',
                'ceremony_date': _optional_date(cleaned_data.get('ceremony_date')),
                'celebrant': cleaned_data.get('celebrant') or '',
                'group_fee': cleaned_data.get('group_fee') or 0,
                'group_fee_paid': cleaned_data.get('group_fee_paid', False),
            })
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Podaci godine prve pričesti su spremljeni.')
            else:
                messages.error(request, 'Godina prve pričesti nije pronađena.')
        else:
            messages.error(request, 'Provjerite podatke godine prve pričesti.')
        return True

    if (
        page_slug == 'prva-pricest'
        and action_name == 'update_first_communion_candidate'
    ):
        first_communion_candidate_form = FirstCommunionCandidateForm(request.POST)
        if first_communion_candidate_form.is_valid():
            action_result = upsert_first_communion_candidate(
                parish_data,
                _first_communion_candidate_payload(
                    first_communion_candidate_form.cleaned_data,
                    request.POST.get('candidate_id', ''),
                ),
            )
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Podaci prvopričesnika su spremljeni.')
            else:
                messages.error(request, 'Prvopričesnik nije pronađen.')
        else:
            messages.error(request, 'Provjerite podatke prvopričesnika.')
        return True

    if (
        page_slug == 'prva-pricest'
        and action_name == 'delete_first_communion_candidate'
    ):
        action_result = delete_first_communion_candidate(parish_data, {
            'year': request.POST.get('year'),
            'id': request.POST.get('candidate_id', ''),
        })
        if action_result.get('ok'):
            parish_data_service.save(parish_data)
            messages.success(request, 'Prvopričesnik je obrisan.')
        else:
            messages.error(request, 'Prvopričesnik nije pronađen.')
        return True

    return False
