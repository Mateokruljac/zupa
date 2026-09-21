"""
Registracija admin stranica Financija u pastoral shell.

Import ovog modula (`page_context_registry`) veže slugove na buildere.
Svaki builder samo prosljeđuje `parish_data` odgovarajućem servisu;
ne učitava ORM. `parish_data_service` je u potpisu registra, ovdje se
ne koristi (čitanje je već obavio shell).

Slugovi: `dugovanja`, `racuni`, `blagajna`, `financijska-izvjestaja`.
"""
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
    """
    Kontekst ekrana potraživanja i obveza.

    Filteri i pogled (`prema-zupi` / `zupa-duguje`) čitaju se iz GET-a
    u `debts_page_context`.
    """
    return debts_page_context(parish_data, request)


@register_page(
    'racuni',
    title='Ulazni računi',
    subtitle='Računi koje župa prima od dobavljača',
)
def build_racuni_context(request, parish_data: dict, parish_data_service: ParishDataService) -> dict:
    """Kontekst knjige ulaznih računa; izlazni računi nisu na ovom ekranu."""
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
    """Kontekst četiri knjige računa; GET `year` i `ledger` biraju prikaz."""
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
    """
    Nadzorna ploča financija: saldo crkvene knjige, otvoreni dugovi, računi.

    Nije službeni godišnji izvještaj biskupiji — operativni pregled ureda.
    """
    return finance_reports_context(parish_data, request)
