"""POST akcije osnovnog kartona obitelji."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages

from pastoral.forms import FamilyForm, FamilyMemberForm
from pastoral.services.api_action_handlers.families import (
    create_family,
    update_family,
    upsert_family_member,
)

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


def handle_family_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
    if page_slug != 'obitelji':
        return False

    if action_name == 'save_family_member':
        family_member_form = FamilyMemberForm(request.POST)
        if family_member_form.is_valid():
            action_result = upsert_family_member(parish_data, {
                'family_id': request.POST.get('family_id', ''),
                **family_member_form.cleaned_data,
            })
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Član obitelji je dodan.')
            else:
                messages.error(request, 'Član obitelji nije mogao biti spremljen.')
        else:
            messages.error(request, 'Provjerite podatke člana obitelji.')
        return True

    if action_name not in {'add_family', 'update_family'}:
        return False

    family_form = FamilyForm(
        request.POST,
        streets=parish_data.get('streets', []),
    )
    if family_form.is_valid():
        cleaned_data = family_form.cleaned_data
        if action_name == 'add_family':
            action_result = create_family(parish_data, cleaned_data)
        else:
            action_result = update_family(parish_data, {
                'id': request.POST.get('family_id', ''),
                **cleaned_data,
            })
        if action_result.get('ok'):
            parish_data_service.save(parish_data)
            success_message = (
                'Karton obitelji je dodan.'
                if action_name == 'add_family'
                else 'Podaci obitelji su spremljeni.'
            )
            messages.success(request, success_message)
        else:
            messages.error(request, 'Karton obitelji nije mogao biti spremljen.')
    else:
        messages.error(request, 'Provjerite osnovne podatke obitelji.')
    return True
