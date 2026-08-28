"""POST akcije za misne nakane."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages

from liturgija.forms import IntentionForm
from liturgija.services.intention_mutations import (
    add_intention,
    delete_intention,
    toggle_intention_paid,
)

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


def handle_intention_page_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
    if action_name == 'add_intention' and page_slug == 'nakane':
        intention_form = IntentionForm(request.POST)
        if intention_form.is_valid():
            add_intention(parish_data, intention_form.cleaned_data)
            parish_data_service.save(parish_data)
            messages.success(request, 'Nakana dodana.')
        else:
            messages.error(request, 'Provjerite unos nakane.')
        return True

    if action_name == 'delete_intention' and page_slug == 'nakane':
        if delete_intention(
            parish_data,
            request.POST.get('intention_id', ''),
        ):
            parish_data_service.save(parish_data)
            messages.success(request, 'Nakana obrisana.')
        return True

    if action_name == 'toggle_intention_paid' and page_slug == 'nakane':
        if toggle_intention_paid(
            parish_data,
            request.POST.get('intention_id', ''),
        ):
            parish_data_service.save(parish_data)
            messages.success(request, 'Status plaćanja ažuriran.')
        return True

    return False
