"""Kompatibilna fasada API akcija koje koristi `/api/action/` endpoint.

Domenske mutacije žive u odgovarajućim Django appovima. Ovaj modul zadržava
stabilni registar naziva akcija i sinkronizaciju krštenja bez promjene JSON
ugovora.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction

from liturgija.api_actions import (
    create_intention,
    delete_intention,
    delete_listic_issue,
    delete_mass_schedule,
    render_listic_preview,
    update_intention,
    upsert_listic_issue,
    upsert_mass_schedule,
)
from django_multitenant.schema import with_tenant_schema

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


ACTION_HANDLERS = {
    'create_intention': create_intention,
    'update_intention': update_intention,
    'delete_intention': delete_intention,
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


READ_ONLY_ACTION_NAMES = frozenset({
    'render_listic_preview',
})
# Handler sam piše u bazu; dict se ne smije ponovo spremati (ponovno bi stvorio red).
DATABASE_WRITTEN_ACTION_NAMES = frozenset({
    'create_intention',
    'update_intention',
    'delete_intention',
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
    elif action_name == 'create_intention':
        # Samo podaci forme.
        action_result = action_handler(action_payload or {})
    elif action_name == 'update_intention':
        # JS šalje { id, data: polja forme }.
        payload = action_payload or {}
        action_result = action_handler(payload.get('id'), payload.get('data') or {})
    elif action_name == 'delete_intention':
        # JS šalje samo id (string), stariji klijent može poslati { id }.
        intention_id = (
            action_payload.get('id')
            if isinstance(action_payload, dict)
            else action_payload
        )
        action_result = action_handler(intention_id)
    else:
        action_result = action_handler(parish_data, action_payload or {})

    if action_name in READ_ONLY_ACTION_NAMES:
        return action_result if isinstance(action_result, dict) else {'ok': True}
    if not action_result.get('ok', True):
        return action_result

    if action_name in DATABASE_WRITTEN_ACTION_NAMES:
        parish_data = parish_data_service.load()
    elif action_name in LITURGICAL_ACTION_NAMES:
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
