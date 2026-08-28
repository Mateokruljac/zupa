"""Kontekst admin stranica Liturgije."""
from __future__ import annotations

from typing import TYPE_CHECKING

from liturgija.services.mass_schedule import migrate_mass_schedule
from liturgija.services.nakane import nakane_page_context
from liturgija.services.zupni_listic import (
    load_config,
    migrate_listic_data,
    zupni_listic_page_context,
)
from pastoral.page_context_registry import register_page

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


@register_page(
    'nakane',
    title='Kalendar misnih nakana',
    subtitle='Upis nakan po danu i misi',
)
def build_nakane_context(request, parish_data: dict, parish_data_service: ParishDataService) -> dict:
    page_context = nakane_page_context(parish_data, request)
    page_context['nakane_bootstrap']['defaultStipend'] = float(
        parish_data_service.load_settings().get('defaultMassIntentionStipend', 0) or 0
    )
    return page_context


@register_page(
    'mise',
    title='Raspored misa',
    subtitle='Stalni termini i veza na misne nakane',
)
def build_mise_context(request, parish_data: dict, parish_data_service: ParishDataService) -> dict:
    migrate_mass_schedule(parish_data)
    return {
        'mise_bootstrap': {
            'massSchedule': parish_data.get('massSchedule', []),
            'massExceptions': parish_data.get('massExceptions', []),
            'intentions': parish_data.get('intentions', []),
            'defaultStipend': float(
                parish_data_service.load_settings().get(
                    'defaultMassIntentionStipend', 0
                ) or 0
            ),
        },
    }


@register_page('zupni-listic', title='Župni listić')
def build_zupni_listic_context(
    request,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> dict:
    parish_settings = parish_data_service.load_settings()
    migrate_listic_data(parish_data)
    page_context = zupni_listic_page_context(parish_data, parish_settings, request)
    bulletin_configuration = load_config()
    page_context['listic_bootstrap'] = {
        'config': {
            'blockTypes': bulletin_configuration['blockTypes'],
            'defaultLayout': bulletin_configuration['defaultLayout'],
        },
        'editLayout': page_context['listic_edit_layout'],
        'savedLayout': page_context['listic_layout'],
    }
    return page_context
