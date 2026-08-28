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
    selected_family = page_context.get('selected_family')
    family_initial_values = {'status': 'aktivna'}
    if selected_family:
        family_initial_values.update({
            'surname': selected_family.get('surname', ''),
            'street_id': selected_family.get('streetId', ''),
            'address': selected_family.get('address', ''),
            'phone': selected_family.get('phone', ''),
            'email': selected_family.get('email', ''),
            'origin_place': selected_family.get('originPlace', ''),
            'status': selected_family.get('status', 'aktivna'),
            'pastoral_notes': selected_family.get('pastoralNotes', ''),
        })
    page_context['family_form'] = FamilyForm(
        streets=page_context.get('street_list', []),
        initial=family_initial_values,
    )
    page_context['family_member_form'] = FamilyMemberForm()
    page_context['family_contribution_form'] = FamilyContributionForm(
        initial={
            'year': date.today().year,
            'lukno_amount': DEFAULT_ANNUAL_CONTRIBUTION_AMOUNT,
            'church_donation': 0,
        },
    )
    page_context['family_notes_form'] = FamilyNotesForm(
        initial={
            'pastoral_notes': (
                selected_family.get('pastoralNotes', '')
                if selected_family
                else ''
            ),
        },
    )


def attach_street_forms(page_context: dict) -> None:
    selected_street = page_context.get('selected_street')
    page_context['street_create_form'] = StreetForm(auto_id='new_street_%s')
    if selected_street:
        page_context['street_form'] = StreetForm(
            auto_id='edit_street_%s',
            initial={
                'name': selected_street.get('name', ''),
                'zone': selected_street.get('zone', ''),
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
                'purpose': 'Pastoralni posjet',
            })
            page_context['prefilled_family'] = selected_family
    page_context['visit_form'] = VisitForm(
        families=families,
        initial=visit_initial_values,
    )

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
    page_context['visit_form'] = VisitForm(families=families, initial={
        'scheduled': selected_visit.get('scheduled'),
        'person': selected_visit.get('person', ''),
        'visit_type': selected_visit.get('type', 'obitelj'),
        'address': selected_visit.get('address', ''),
        'priest': selected_visit.get('priest', ''),
        'purpose': selected_visit.get('purpose', ''),
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
        return True
    if page_slug == 'ulice':
        attach_street_forms(page_context)
        return True
    if page_slug == 'posjete':
        attach_visit_forms(request, parish_data_service, page_context)
        return True
    return False
