"""Kompatibilna fasada API akcija koje koristi `/api/action/` endpoint.

Domenske mutacije žive u odgovarajućim Django appovima. Ovaj modul zadržava
stabilni registar naziva akcija i sinkronizaciju krštenja bez promjene JSON
ugovora.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction

from liturgija.api_actions import (
    delete_listic_issue,
    delete_mass_schedule,
    render_listic_preview,
    upsert_listic_issue,
    upsert_mass_schedule,
)
from django_multitenant.schema import with_tenant_schema

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


ACTION_HANDLERS = {
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
    'zupniListicIssues',
)
READ_ONLY_ACTION_NAMES = frozenset({'render_listic_preview'})
MUTATING_LITURGICAL_ACTION_NAMES = LITURGICAL_ACTION_NAMES - READ_ONLY_ACTION_NAMES
SETTINGS_AWARE_ACTION_NAMES = READ_ONLY_ACTION_NAMES | {'upsert_listic_issue'}


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


@with_tenant_schema
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
        # Handleri već pišu ORM; parish_data je usklađen za odgovor.
        response_data = {
            key: parish_data.get(key)
            for key in LITURGICAL_RESPONSE_KEYS
        }
        response_is_partial = True
    else:
        parish_data_service.save(parish_data)
        response_data = parish_data_service.load()
        response_is_partial = False

    additional_response_data = {
        response_key: response_value
        for response_key, response_value in action_result.items()
        if response_key != 'ok'
    }
    return {
        'ok': True,
        'data': response_data,
        'dataPartial': response_is_partial,
        **additional_response_data,
    }
