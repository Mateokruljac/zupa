"""Javna ulazna točka za POST akcije administracijskih stranica."""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from django.db import transaction

from financije.page_actions import handle_finance_action
from isprave.page_actions import handle_registry_books_action
from liturgija.page_actions import handle_intention_page_action
from sakramenti.page_actions import handle_sakramenti_action
from ured.page_actions import handle_ured_action
from zupa_vjernici.page_actions import handle_parish_community_action

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


PageActionHandler = Callable[[object, str, str, dict, 'ParishDataService'], bool]

MVP_PAGE_ACTION_HANDLERS: tuple[PageActionHandler, ...] = (
    handle_ured_action,
    handle_parish_community_action,
    handle_sakramenti_action,
    handle_finance_action,
    handle_intention_page_action,
    handle_registry_books_action,
)

# Javno ime ostaje stabilno za postojeće integracije koje nadomještaju skup
# handlera.
PAGE_ACTION_HANDLERS = MVP_PAGE_ACTION_HANDLERS


def page_action_handlers() -> tuple[PageActionHandler, ...]:
    """Vraća registrirane page action handlere."""
    return PAGE_ACTION_HANDLERS


def handle_page_post(
    request,
    page: str,
    parish_data_service: ParishDataService,
) -> bool:
    """Obrađuje POST i vraća ``True`` kada je akcija prepoznata."""
    action_name = request.POST.get('action')
    if not action_name:
        return False

    with transaction.atomic():
        parish_data_service.lock_for_update()
        parish_data = parish_data_service.load()
        for action_handler in page_action_handlers():
            if action_handler(
                request,
                page,
                action_name,
                parish_data,
                parish_data_service,
            ):
                return True
    return False
