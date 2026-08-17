"""Javna ulazna točka za POST akcije administracijskih stranica."""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from pastoral.page_actions.deanery import handle_deanery_action
from pastoral.page_actions.councils import handle_council_action
from pastoral.page_actions.families import handle_family_action
from pastoral.page_actions.formation import handle_formation_action
from pastoral.page_actions.finance import handle_finance_action
from pastoral.page_actions.office_records import handle_office_records_action
from pastoral.page_actions.operations import handle_operations_action
from pastoral.page_actions.sacraments import handle_sacrament_action

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


PageActionHandler = Callable[[object, str, str, dict, 'ParishDataService'], bool]

PAGE_ACTION_HANDLERS: tuple[PageActionHandler, ...] = (
    handle_council_action,
    handle_family_action,
    handle_formation_action,
    handle_finance_action,
    handle_sacrament_action,
    handle_office_records_action,
    handle_deanery_action,
    handle_operations_action,
)


def handle_page_post(
    request,
    page: str,
    parish_data_service: ParishDataService,
) -> bool:
    """Obrađuje POST i vraća ``True`` kada je akcija prepoznata."""
    action_name = request.POST.get('action')
    if not action_name:
        return False

    parish_data = parish_data_service.load()
    for action_handler in PAGE_ACTION_HANDLERS:
        if action_handler(
            request,
            page,
            action_name,
            parish_data,
            parish_data_service,
        ):
            return True
    return False
