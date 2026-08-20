"""Normalizacija podataka koja se izvršava samo kada je aktivna faza 2."""
from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path


PHASE_TWO_DIRECTORY = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def _interparish_demo_data() -> dict:
    demo_path = (
        PHASE_TWO_DIRECTORY
        / 'interparish_collaboration'
        / 'data'
        / 'deanery_demo.json'
    )
    try:
        with demo_path.open(encoding='utf-8') as source:
            return json.load(source)
    except (OSError, json.JSONDecodeError):
        return {
            'deanery': {},
            'parishDirectory': [],
            'interparishRequests': [],
        }


def migrate_interparish_collaboration(data: dict) -> None:
    defaults = _interparish_demo_data()
    if not isinstance(data.get('deanery'), dict) or not data.get('deanery'):
        data['deanery'] = copy.deepcopy(defaults.get('deanery', {}))
    if (
        not isinstance(data.get('parishDirectory'), list)
        or not data.get('parishDirectory')
    ):
        data['parishDirectory'] = copy.deepcopy(
            defaults.get('parishDirectory', [])
        )
    if (
        not isinstance(data.get('interparishRequests'), list)
        or not data.get('interparishRequests')
    ):
        data['interparishRequests'] = copy.deepcopy(
            defaults.get('interparishRequests', [])
        )


@lru_cache(maxsize=1)
def _operations_center_demo_data() -> dict:
    demo_path = (
        PHASE_TWO_DIRECTORY
        / 'operations_center'
        / 'data'
        / 'operations_demo.json'
    )
    try:
        with demo_path.open(encoding='utf-8') as source:
            return json.load(source)
    except (OSError, json.JSONDecodeError):
        return {}


def migrate_operations_center(data: dict) -> None:
    defaults = _operations_center_demo_data()
    collection_names = (
        'officeCorrespondence',
        'officeApprovals',
        'communications',
        'facilityTasks',
        'officeAppointments',
        'roomBookings',
        'serviceRota',
        'complianceControls',
        'parishContracts',
        'handoverChecklist',
    )
    for collection_name in collection_names:
        if (
            not isinstance(data.get(collection_name), list)
            or not data.get(collection_name)
        ):
            data[collection_name] = copy.deepcopy(
                defaults.get(collection_name, [])
            )


def migrate_phase_two_data(data: dict) -> None:
    migrate_interparish_collaboration(data)
    migrate_operations_center(data)
