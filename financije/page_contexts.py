"""Kontekst admin stranica Financija."""
from __future__ import annotations

from typing import TYPE_CHECKING

from financije.services.cashbook import cashbook_page_context
from financije.services.debts import debts_page_context
from financije.services.finance_reports import finance_reports_context
from financije.services.invoices_page import invoices_page_context
from pastoral.page_context_registry import register_page

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


@register_page(
    'dugovanja',
    title='Dugovanja',
    subtitle='Prema župi i dugovanja župe',
)
def build_dugovanja_context(
    request,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> dict:
    return debts_page_context(parish_data, request)


@register_page(
    'racuni',
    title='Ulazni računi',
    subtitle='Računi koje župa prima od dobavljača',
)
def build_racuni_context(request, parish_data: dict, parish_data_service: ParishDataService) -> dict:
    return invoices_page_context(parish_data, request)


@register_page(
    'blagajna',
    title='Blagajna',
    subtitle='Knjige crkvenih računa, kolekti, gradnje i misnih obveza',
)
def build_blagajna_context(
    request,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> dict:
    return cashbook_page_context(parish_data, request)


@register_page(
    'financijska-izvjestaja',
    title='Financijski pregled',
    subtitle='Prihodi, rashodi i otvorene obveze',
)
def build_finance_reports_page_context(
    request,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> dict:
    return finance_reports_context(parish_data, request)
