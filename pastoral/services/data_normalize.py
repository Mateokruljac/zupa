"""Migracije parish podataka — centralizirano (prije data-seed.js + *-engine migrate)."""
from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path

from pastoral.services.mass_schedule import migrate_mass_schedule
from pastoral.services.zupni_listic import migrate_listic_data


def migrate_invoices(data: dict) -> None:
    if not isinstance(data.get('invoices'), list):
        data['invoices'] = []
    for inv in data['invoices']:
        if not inv.get('direction'):
            inv['direction'] = 'outgoing' if inv.get('linkedSource') else 'incoming'
        if not inv.get('supplierName'):
            inv['supplierName'] = inv.get('payerName') or ''
        if not inv.get('status'):
            inv['status'] = 'placen' if inv.get('paidAmount', 0) >= inv.get('total', 0) else (
                'primljen' if inv.get('direction') == 'incoming' else 'izdan'
            )
        if inv.get('vatRate') is None:
            inv['vatRate'] = 0
        if inv.get('paidAmount') is None:
            inv['paidAmount'] = inv.get('total') if inv.get('status') == 'placen' else 0


def migrate_cashbook(data: dict) -> None:
    if not isinstance(data.get('cashbook'), list):
        data['cashbook'] = []
    for e in data['cashbook']:
        e.setdefault('ledger', 'plavi')
        e.setdefault('category', '')


def migrate_visits(data: dict) -> None:
    if not isinstance(data.get('visits'), list):
        data['visits'] = []
    if not isinstance(data.get('registryBooks'), list):
        data['registryBooks'] = []
    if not isinstance(data.get('docBindings'), list):
        data['docBindings'] = []


def migrate_staff_messages(data: dict) -> None:
    if not isinstance(data.get('staffMessages'), list):
        data['staffMessages'] = []


@lru_cache(maxsize=1)
def _deanery_demo() -> dict:
    path = Path(__file__).resolve().parent.parent / 'data' / 'deanery_demo.json'
    try:
        with path.open(encoding='utf-8') as source:
            return json.load(source)
    except (OSError, json.JSONDecodeError):
        return {'deanery': {}, 'parishDirectory': [], 'interparishRequests': []}


def migrate_deanery(data: dict) -> None:
    """Dodaje mali reprezentativni demo, nikada masovno generirane vjernike."""
    defaults = _deanery_demo()
    if not isinstance(data.get('deanery'), dict) or not data.get('deanery'):
        data['deanery'] = copy.deepcopy(defaults.get('deanery', {}))
    if not isinstance(data.get('parishDirectory'), list) or not data.get('parishDirectory'):
        data['parishDirectory'] = copy.deepcopy(defaults.get('parishDirectory', []))
    if not isinstance(data.get('interparishRequests'), list) or not data.get('interparishRequests'):
        data['interparishRequests'] = copy.deepcopy(defaults.get('interparishRequests', []))


@lru_cache(maxsize=1)
def _operations_demo() -> dict:
    path = Path(__file__).resolve().parent.parent / 'data' / 'operations_demo.json'
    try:
        with path.open(encoding='utf-8') as source:
            return json.load(source)
    except (OSError, json.JSONDecodeError):
        return {}


def migrate_operations(data: dict) -> None:
    """Dodaje mali operativni demo bez masovnog generiranja osoba ili obitelji."""
    defaults = _operations_demo()
    collections = (
        'officeCorrespondence', 'officeApprovals', 'communications', 'facilityTasks',
        'officeAppointments', 'roomBookings', 'serviceRota', 'complianceControls',
        'parishContracts', 'handoverChecklist',
    )
    for key in collections:
        if not isinstance(data.get(key), list) or not data.get(key):
            data[key] = copy.deepcopy(defaults.get(key, []))


def migrate_all(data: dict) -> dict:
    migrate_mass_schedule(data)
    migrate_listic_data(data)
    migrate_invoices(data)
    migrate_cashbook(data)
    migrate_visits(data)
    migrate_staff_messages(data)
    migrate_deanery(data)
    migrate_operations(data)
    if not isinstance(data.get('publicSubmissions'), list):
        data['publicSubmissions'] = []
    if not isinstance(data.get('announcements'), list):
        data['announcements'] = []
    return data
