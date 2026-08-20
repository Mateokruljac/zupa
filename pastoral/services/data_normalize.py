"""Migracije parish podataka — centralizirano (prije data-seed.js + *-engine migrate)."""
from __future__ import annotations

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


def migrate_all(data: dict) -> dict:
    migrate_mass_schedule(data)
    migrate_listic_data(data)
    migrate_invoices(data)
    migrate_cashbook(data)
    migrate_visits(data)
    migrate_staff_messages(data)
    from phase_two.module_registry import PRODUCT_MODULES

    if any(product_module.is_available for product_module in PRODUCT_MODULES):
        from phase_two.data_migrations import migrate_phase_two_data

        migrate_phase_two_data(data)
    if not isinstance(data.get('publicSubmissions'), list):
        data['publicSubmissions'] = []
    if not isinstance(data.get('announcements'), list):
        data['announcements'] = []
    return data
