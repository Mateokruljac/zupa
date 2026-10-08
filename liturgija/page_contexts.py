"""Kontekst admin stranica Liturgije (naslov + JSON za JS)."""
from __future__ import annotations

from liturgija.services.zupni_listic import (
    load_config,
    zupni_listic_page_context,
)
from pastoral.page_context_registry import register_page
from pastoral.services.dates import today_iso
from pastoral.services.data import ParishDataService


def _mass_page_bootstrap(
    parish_data: dict,
    parish_data_service: ParishDataService,
    **extra,
) -> dict:
    return {
        'intentions': parish_data.get('intentions', []),
        'massSchedule': parish_data.get('massSchedule', []),
        'massExceptions': parish_data.get('massExceptions', []),
        'defaultStipend': float(
            parish_data_service.load_settings().get(
                'defaultMassIntentionStipend', 0,
            ) or 0
        ),
        **extra,
    }


@register_page(
    'nakane',
    title='Kalendar misnih nakana',
    subtitle='Upis nakan po danu i misi',
)
def build_nakane_context(request, parish_data: dict, parish_data_service: ParishDataService) -> dict:
    selected_date = request.GET.get('date') or today_iso()
    if selected_date == 'today':
        selected_date = today_iso()
    return {
        'nakane_bootstrap': _mass_page_bootstrap(
            parish_data,
            parish_data_service,
            filterDate=selected_date,
        ),
    }


@register_page(
    'mise',
    title='Raspored misa',
    subtitle='Stalni termini i veza na misne nakane',
)
def build_mise_context(request, parish_data: dict, parish_data_service: ParishDataService) -> dict:
    return {
        'mise_bootstrap': _mass_page_bootstrap(parish_data, parish_data_service),
    }


@register_page('zupni-listic', title='Župni listić')
def build_zupni_listic_context(
    request,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> dict:
    parish_settings = parish_data_service.load_settings()
    if not isinstance(parish_data.get('zupniListicIssues'), list):
        parish_data['zupniListicIssues'] = []
    page_context = zupni_listic_page_context(parish_data, parish_settings, request)
    config = load_config()
    page_context['listic_bootstrap'] = {
        'config': {
            'blockTypes': config['blockTypes'],
            'defaultLayout': config['defaultLayout'],
        },
        'editLayout': page_context['listic_edit_layout'],
    }
    return page_context
