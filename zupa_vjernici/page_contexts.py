"""Kontekst admin stranica župne zajednice."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pastoral.page_context_registry import register_page
from zupa_vjernici.services.families_page import families_page_context
from zupa_vjernici.services.streets import streets_page_context
from zupa_vjernici.services.visits_page import visits_page_context

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


@register_page(
    'obitelji',
    title='Obitelji',
    subtitle=(
        'Karton domaćinstva — članovi, sakramenti, lukno i pastoralne bilješke'
    ),
)
def build_obitelji_context(
    request,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> dict:
    return families_page_context(parish_data, request)


@register_page(
    'ulice',
    title='Ulice',
    subtitle='Popis ulica župe — obitelji po adresi za obilazak',
)
def build_ulice_context(request, parish_data: dict, parish_data_service: ParishDataService) -> dict:
    return streets_page_context(
        parish_data,
        request,
        parish_data_service.load_settings(),
    )


@register_page(
    'posjete',
    title='Posjete',
    subtitle='Pastoralni posjeti obiteljima i bolesnicima',
)
def build_posjete_context(request, parish_data: dict, parish_data_service: ParishDataService) -> dict:
    return visits_page_context(parish_data, request)
