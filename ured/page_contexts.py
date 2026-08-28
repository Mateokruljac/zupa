"""Kontekst admin stranica Župnog ureda."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pastoral.page_context_registry import register_page
from ured.services.councils_page import councils_page_context
from ured.services.kalendar import calendar_page_context
from ured.services.public_submissions_page import public_submissions_context
from ured.services.reminders_page import reminders_page_context

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


@register_page(
    'vijeca',
    title='Vijeća ŽPV/ŽEV',
    subtitle='Članovi i sastanci',
)
def build_vijeca_context(request, parish_data: dict, parish_data_service: ParishDataService) -> dict:
    return councils_page_context(parish_data, request)


@register_page(
    'podsjetnici',
    title='Podsjetnici',
    subtitle='Inbox obaveza župnog ureda',
)
def build_podsjetnici_context(
    request,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> dict:
    return reminders_page_context(parish_data, request)


@register_page(
    'kalendar',
    title='Događaji i zadaci',
    subtitle='Župni kalendar, liturgija i obaveze ureda',
)
def build_kalendar_context(request, parish_data: dict, parish_data_service: ParishDataService) -> dict:
    return calendar_page_context(parish_data, request)


@register_page(
    'javne-prijave',
    title='Javne prijave',
    subtitle='Prijave s weba',
)
def build_javne_prijave_context(
    request,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> dict:
    return public_submissions_context(parish_data, request)


@register_page(
    'postavke',
    title='Postavke',
    subtitle='Naziv župe, logo, boje',
)
def build_postavke_context(request, parish_data: dict, parish_data_service: ParishDataService) -> dict:
    return {
        'settings': parish_data_service.load_settings(),
        'parish_decree': parish_data.get('parishDecree', {}),
    }
