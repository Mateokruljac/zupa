"""Kontekst admin stranica Isprava."""
from __future__ import annotations

from typing import TYPE_CHECKING

from isprave.services.documents_page import documents_page_context
from isprave.services.registry_books import registry_books_page_context
from pastoral.page_context_registry import register_page

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


@register_page(
    'potvrde',
    title='Dokumenti i potvrde',
    subtitle='Pronađite zapis, odaberite dokument i ispišite ga',
)
def build_potvrde_context(request, parish_data: dict, parish_data_service: ParishDataService) -> dict:
    return documents_page_context(
        parish_data,
        parish_data_service.load_settings(),
        request,
    )


@register_page(
    'maticne-knjige',
    title='Matične knjige',
    subtitle='Pregled knjiga u župi',
)
def build_maticne_knjige_context(
    request,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> dict:
    return registry_books_page_context(parish_data, request)
