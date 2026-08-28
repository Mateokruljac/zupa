"""POST akcije za župni ured."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ured.page_actions_calendar import handle_calendar_action
from ured.page_actions_councils import handle_council_action
from ured.page_actions_settings import handle_settings_action
from ured.page_actions_submissions import handle_public_submissions_action

__all__ = (
    'handle_calendar_action',
    'handle_council_action',
    'handle_settings_action',
    'handle_public_submissions_action',
    'handle_ured_action',
)

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


def handle_ured_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
    for action_handler in (
        handle_calendar_action,
        handle_council_action,
        handle_settings_action,
        handle_public_submissions_action,
    ):
        if action_handler(
            request,
            page_slug,
            action_name,
            parish_data,
            parish_data_service,
        ):
            return True
    return False
