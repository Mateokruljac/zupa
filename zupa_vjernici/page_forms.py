"""Priprema formi za stranice obitelji, ulica i posjeta."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from pastoral.services.api_action_handlers.shared import (
    DEFAULT_ANNUAL_CONTRIBUTION_AMOUNT,
)
from zupa_vjernici.forms import (
    FamilyContributionForm,
    FamilyForm,
    FamilyMemberForm,
    FamilyNotesForm,
    StreetForm,
    VisitForm,
)

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


def attach_family_forms(page_context: dict) -> None:
    streets = page_context.get('street_list', [])
    # Karton se puni preko API-ja; forme ovdje ostaju prazne predloške.
    page_context['new_family_form'] = FamilyForm(
        streets=streets,
        auto_id='new_family_%s',
        initial={'status': 'aktivna'},
    )
    page_context['family_form'] = FamilyForm(
        streets=streets,
        auto_id='edit_family_%s',
        initial={'status': 'aktivna'},
    )
    page_context['family_member_form'] = FamilyMemberForm()
    page_context['family_contribution_form'] = FamilyContributionForm(
        initial={
            'year': date.today().year,
            'category': 'lukno',
            'amount': DEFAULT_ANNUAL_CONTRIBUTION_AMOUNT,
            'paid_at': date.today(),
        },
    )
    page_context['family_notes_form'] = FamilyNotesForm()


def attach_street_forms(page_context: dict) -> None:
    selected_street = page_context.get('selected_street')
    page_context['street_create_form'] = StreetForm(auto_id='new_street_%s')
    if selected_street:
        page_context['street_form'] = StreetForm(
            auto_id='edit_street_%s',
            initial={
                'name': selected_street.get('name', ''),
                'city': selected_street.get('city', ''),
                'notes': selected_street.get('notes', ''),
            },
        )
    else:
        page_context['street_form'] = StreetForm(auto_id='edit_street_%s')


def attach_visit_forms(
    request,
    parish_data_service: ParishDataService,
    page_context: dict,
) -> None:
    parish_data = parish_data_service.load()
    families = parish_data.get('families', [])
    visit_initial_values = {'scheduled': parish_data_service.today_iso()}
    family_id = request.GET.get('family') or request.GET.get('family_id')
    if family_id:
        selected_family = next(
            (
                family
                for family in families
                if family.get('id') == family_id
            ),
            None,
        )
        if selected_family:
            visit_initial_values.update({
                'person': (
                    f"Obitelj {selected_family.get('surname', '')}".strip()
                ),
                'address': selected_family.get('address', ''),
                'family_id': selected_family.get('id', ''),
                'visit_type': 'obitelj',
            })
            page_context['prefilled_family'] = selected_family
    page_context['visit_form'] = VisitForm(initial=visit_initial_values)

    visit_id = request.GET.get('visit')
    if not visit_id:
        return
    selected_visit = next(
        (
            visit
            for visit in parish_data.get('visits', [])
            if visit.get('id') == visit_id
        ),
        None,
    )
    if not selected_visit:
        return
    page_context['selected_visit'] = selected_visit
    page_context['visit_form'] = VisitForm(initial={
        'scheduled': selected_visit.get('scheduled'),
        'person': selected_visit.get('person', ''),
        'visit_type': selected_visit.get('type', 'obitelj'),
        'address': selected_visit.get('address', ''),
        'family_id': selected_visit.get('familyId', ''),
        'report': selected_visit.get('report', ''),
    })


def attach_parish_community_forms(
    request,
    page_slug: str,
    parish_data_service: ParishDataService,
    page_context: dict,
) -> bool:
    if page_slug == 'obitelji':
        attach_family_forms(page_context)
        page_context['street_create_form'] = StreetForm(auto_id='family_new_street_%s')
        return True
    if page_slug == 'ulice':
        attach_street_forms(page_context)
        return True
    if page_slug == 'posjete':
        attach_visit_forms(request, parish_data_service, page_context)
        return True
    return False
