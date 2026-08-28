"""Kompatibilna fasada API akcija koje koristi `/api/action/` endpoint.

Domenske mutacije žive u odgovarajućim Django appovima. Ovaj modul zadržava
stabilni registar naziva akcija i sinkronizaciju krštenja bez promjene JSON
ugovora.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction

from pastoral.services.api_action_handlers.shared import normalize_parish_data
from liturgija.api_actions import (
    create_intention,
    delete_intention,
    delete_listic_issue,
    delete_mass_schedule,
    mark_intention_paid,
    render_listic_preview,
    toggle_intention_paid,
    update_intention,
    upsert_listic_issue,
    upsert_mass_schedule,
)

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


ACTION_HANDLERS = {
    'create_intention': create_intention,
    'update_intention': update_intention,
    'delete_intention': delete_intention,
    'mark_intention_paid': mark_intention_paid,
    'upsert_mass_schedule': upsert_mass_schedule,
    'delete_mass_schedule': delete_mass_schedule,
    'upsert_listic_issue': upsert_listic_issue,
    'delete_listic_issue': delete_listic_issue,
    'render_listic_preview': render_listic_preview,
}
LITURGICAL_ACTION_NAMES = frozenset(ACTION_HANDLERS)
LITURGICAL_RESPONSE_KEYS = (
    'intentions',
    'massSchedule',
    'massExceptions',
    'massScheduleLog',
    'zupniListicLayout',
    'zupniListicIssues',
    'zupniListicTemplate',
)


READ_ONLY_ACTION_NAMES = frozenset({
    'render_listic_preview',
})
MUTATING_LITURGICAL_ACTION_NAMES = (
    LITURGICAL_ACTION_NAMES - READ_ONLY_ACTION_NAMES
)

SETTINGS_AWARE_ACTION_NAMES = READ_ONLY_ACTION_NAMES | frozenset({
    'upsert_listic_issue',
})


def dispatch_action(
    action_name: str,
    action_payload: dict,
    parish_data_service: ParishDataService,
    actor=None,
) -> dict:
    action_handler = ACTION_HANDLERS.get(action_name)
    if not action_handler:
        return {
            'ok': False,
            'error': 'unknown_action',
            'action': action_name,
        }

    if action_name in MUTATING_LITURGICAL_ACTION_NAMES:
        with transaction.atomic():
            parish_data_service.lock_for_update()
            return _dispatch_action(
                action_name,
                action_payload,
                parish_data_service,
                action_handler,
            )
    return _dispatch_action(
        action_name,
        action_payload,
        parish_data_service,
        action_handler,
    )


def _dispatch_action(
    action_name: str,
    action_payload: dict,
    parish_data_service: ParishDataService,
    action_handler,
) -> dict:

    parish_data = parish_data_service.load()
    parish_settings = parish_data_service.load_settings()
    if action_name in SETTINGS_AWARE_ACTION_NAMES:
        action_result = action_handler(
            parish_data,
            action_payload or {},
            parish_settings,
        )
    else:
        action_result = action_handler(parish_data, action_payload or {})

    if action_name in READ_ONLY_ACTION_NAMES:
        return action_result if isinstance(action_result, dict) else {'ok': True}
    if not action_result.get('ok', True):
        return action_result

    if action_name in LITURGICAL_ACTION_NAMES:
        parish_data_service.save_liturgical(parish_data)
    else:
        parish_data_service.save(parish_data)
    additional_response_data = {
        response_key: response_value
        for response_key, response_value in action_result.items()
        if response_key != 'ok'
    }
    if action_name in LITURGICAL_ACTION_NAMES:
        response_data = {
            key: parish_data.get(key)
            for key in LITURGICAL_RESPONSE_KEYS
        }
        response_is_partial = True
    else:
        # Zadržava testni/compatibility contract kada se registry eksplicitno
        # nadomjesti izvan aktivnog liturgijskog API-ja.
        response_data = parish_data_service.load()
        response_is_partial = False
    return {
        'ok': True,
        'data': response_data,
        'dataPartial': response_is_partial,
        **additional_response_data,
    }
