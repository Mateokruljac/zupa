"""POST akcije osnovnog kartona obitelji."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages

from pastoral.forms import FamilyForm
from pastoral.services.api_action_handlers.families import create_family

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


def handle_family_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
    if page_slug != 'obitelji' or action_name != 'add_family':
        return False

    family_form = FamilyForm(
        request.POST,
        streets=parish_data.get('streets', []),
    )
    if family_form.is_valid():
        cleaned_data = family_form.cleaned_data
        action_result = create_family(parish_data, {
            'surname': cleaned_data['surname'],
            'street_id': cleaned_data.get('street_id') or '',
            'address': cleaned_data['address'],
            'phone': cleaned_data.get('phone') or '',
            'email': cleaned_data.get('email') or '',
            'origin_place': cleaned_data.get('origin_place') or '',
        })
        if action_result.get('ok'):
            parish_data_service.save(parish_data)
            messages.success(request, 'Osnovni karton obitelji je dodan.')
        else:
            messages.error(request, 'Karton obitelji nije mogao biti spremljen.')
    else:
        messages.error(request, 'Provjerite osnovne podatke obitelji.')
    return True
