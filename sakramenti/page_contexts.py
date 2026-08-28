"""Kontekst admin stranica Sakramenata."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pastoral.page_context_registry import register_page
from sakramenti.services.page_context import (
    anointing_context,
    baptisms_context,
    first_communion_page_context,
    funerals_context,
    krizma_page_context,
    weddings_context,
)

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


@register_page(
    'krsenja',
    title='Krštenja',
    subtitle='Matična evidencija krštenja',
)
def build_krsenja_context(request, parish_data: dict, parish_data_service: ParishDataService) -> dict:
    return baptisms_context(parish_data, request)


@register_page(
    'prva-pricest',
    title='Prva pričest',
    subtitle='Evidencija prvopričesnika — škola, roditelji, plaćanje',
)
def build_prva_pricest_context(
    request,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> dict:
    return first_communion_page_context(parish_data, request)


@register_page(
    'krizma',
    title='Krizma',
    subtitle='Evidencija krizmanika — godina, priprema',
)
def build_krizma_context(request, parish_data: dict, parish_data_service: ParishDataService) -> dict:
    return krizma_page_context(parish_data, request)


@register_page(
    'vjencanja',
    title='Vjenčanja',
    subtitle='Mladoženja, mlada, kumovi, datum i svećenik',
)
def build_vjencanja_context(
    request,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> dict:
    return weddings_context(parish_data, request)


@register_page(
    'pogrebi',
    title='Pogrebi',
    subtitle='Pokojnik, misa, groblje, svećenik i naknada',
)
def build_pogrebi_context(request, parish_data: dict, parish_data_service: ParishDataService) -> dict:
    return funerals_context(parish_data, request)


@register_page(
    'pomazanje',
    title='Pomazanje',
    subtitle='Tko, kada i gdje — bolesničko pomazanje',
)
def build_pomazanje_context(
    request,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> dict:
    return anointing_context(parish_data, request)
