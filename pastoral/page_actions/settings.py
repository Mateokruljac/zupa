"""POST akcije postavki župe."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages

from pastoral.forms import ParishSettingsForm
from pastoral.services.admin_interface_theme import (
    synchronize_admin_interface_theme,
)

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


def _updated_parish_settings(
    current_parish_settings: dict,
    cleaned_form_data: dict,
) -> dict:
    """Ažurira samo vrijednosti dostupne u obrascu i čuva ostale postavke."""
    updated_parish_settings = current_parish_settings.copy()
    updated_parish_settings.update({
        'name': cleaned_form_data['name'],
        'shortName': (
            cleaned_form_data.get('short_name')
            or cleaned_form_data['name']
        ),
        'city': cleaned_form_data['city'],
        'diocese': cleaned_form_data['diocese'],
        'pastor': cleaned_form_data['pastor'],
        'phone': cleaned_form_data.get('phone') or '',
        'email': cleaned_form_data.get('email') or '',
        'primaryColor': (
            cleaned_form_data.get('primary_color') or '#5c2e3a'
        ),
        'accentColor': (
            cleaned_form_data.get('accent_color') or '#b8922a'
        ),
        'logoUrl': cleaned_form_data.get('logo_url') or '',
        'defaultMassIntentionStipend': float(
            cleaned_form_data.get('default_mass_intention_stipend') or 0
        ),
    })
    return updated_parish_settings


def handle_settings_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
    if page_slug != 'postavke' or action_name != 'save_settings':
        return False

    settings_form = ParishSettingsForm(request.POST)
    if not settings_form.is_valid():
        messages.error(
            request,
            'Postavke nisu spremljene. Provjerite unesene podatke.',
        )
        return True

    parish_settings = _updated_parish_settings(
        parish_data_service.load_settings(),
        settings_form.cleaned_data,
    )
    parish_data_service.save_settings(parish_settings)
    synchronize_admin_interface_theme(
        parish_settings.get('primaryColor'),
        parish_settings.get('accentColor'),
    )
    messages.success(request, 'Podaci o župi su spremljeni.')
    return True
