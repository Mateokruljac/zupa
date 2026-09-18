"""Učitavanje i spremanje operativnih parish kolekcija iz ORM modela.

Svaki legacy zapis čuva se kao red s `payload` JSON-om jednakim starom
objektu iz Parish.data, tako da se UI ugovor (camelCase ključevi) ne mijenja.
"""
from __future__ import annotations

import copy
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Prefetch

from pastoral.models import Parish
from financije.models import (
    CashbookEntry,
    FinanceSettings,
    Invoice,
    ParishDebt,
)
from liturgija.models import (
    BulletinIssue,
    BulletinLayout,
    MassException,
    MassIntention,
    MassScheduleLogEntry,
    MassScheduleSlot,
)
from liturgija.services.mass_records import (
    mass_exception_as_legacy_record,
    mass_exception_field_defaults_from_legacy,
    mass_intention_as_legacy_record,
    mass_intention_field_defaults_from_legacy,
    mass_schedule_log_as_legacy_record,
    mass_schedule_log_field_defaults_from_legacy,
    mass_schedule_slot_as_legacy_record,
    mass_schedule_slot_field_defaults_from_legacy,
)
from liturgija.services.zupni_listic import load_config
from ured.services.office_records import (
    announcement_as_legacy_record,
    announcement_field_defaults_from_legacy,
    calendar_event_as_legacy_record,
    calendar_event_field_defaults_from_legacy,
    office_task_as_legacy_record,
    office_task_field_defaults_from_legacy,
    public_submission_as_legacy_record,
    public_submission_field_defaults_from_legacy,
)
from ured.models import (
    Announcement,
    Council,
    CouncilMembership,
    DocumentBinding,
    OfficeTask,
    ParishCalendarEvent,
    ParishFoundingDecree,
    PublicSubmission,
)
from ured.services.council_records import (
    council_as_legacy_record,
    decree_as_legacy_record,
    sync_council_from_legacy,
    sync_founding_decree_from_legacy,
)
from zupa_vjernici.models import Household, HouseholdMembership, PastoralVisit, Street
from zupa_vjernici.services.street_records import (
    street_as_legacy_record,
    street_field_defaults_from_legacy,
)
from zupa_vjernici.services.household_records import (
    household_as_legacy_record,
    household_field_defaults_from_legacy,
    sync_household_nested_records,
    visit_as_legacy_record,
    visit_field_defaults_from_legacy,
)
from financije.services.finance_records import (
    cashbook_as_legacy_record,
    cashbook_field_defaults_from_legacy,
    invoice_as_legacy_record,
    invoice_field_defaults_from_legacy,
    parish_debt_as_legacy_record,
    parish_debt_field_defaults_from_legacy,
)


# Kolekcije koje više ne smiju ostati u Parish.data nakon cutovera.
ORM_BACKED_COLLECTION_KEYS = frozenset({
    'streets',
    'families',
    'visits',
    'parishioners',  # derived — never persist
    'tasks',
    'events',
    'publicSubmissions',
    'announcements',
    'pastoralCouncil',
    'economicCouncil',
    'parishDecree',
    'docBindings',
    'parishDebts',
    'invoices',
    'cashbook',
    'luknoDefaultAmount',
    'intentions',
    'massSchedule',
    'massExceptions',
    'massScheduleLog',
    'zupniListicLayout',
    'zupniListicIssues',
    'zupniListicTemplate',
})


def _record_identifier(record: dict, fallback_prefix: str, index: int) -> str:
    record_id = str(record.get('id') or '').strip()
    if record_id:
        return record_id
    return f'{fallback_prefix}-{index + 1}'


def _payloads_from_queryset(queryset) -> list[dict]:
    return [copy.deepcopy(row.payload or {}) for row in queryset]


def _replace_list_collection(model, parish: Parish, records: list, *, id_prefix: str):
    records = list(records or [])
    keep_identifiers = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        public_identifier = _record_identifier(record, id_prefix, index)
        payload = copy.deepcopy(record)
        payload.setdefault('id', public_identifier)
        keep_identifiers.add(public_identifier)
        model.objects.update_or_create(
            parish=parish,
            public_identifier=public_identifier,
            defaults={'payload': payload},
        )
    model.objects.filter(parish=parish).exclude(
        public_identifier__in=keep_identifiers,
    ).delete()


def _replace_typed_collection(
    model,
    parish: Parish,
    records: list,
    *,
    id_prefix: str,
    defaults_from_legacy,
) -> None:
    keep_identifiers = set()
    for index, record in enumerate(records or []):
        if not isinstance(record, dict):
            continue
        public_identifier = _record_identifier(record, id_prefix, index)
        payload = copy.deepcopy(record)
        payload.setdefault('id', public_identifier)
        keep_identifiers.add(public_identifier)
        model.objects.update_or_create(
            parish=parish,
            public_identifier=public_identifier,
            defaults=defaults_from_legacy(payload),
        )
    model.objects.filter(parish=parish).exclude(
        public_identifier__in=keep_identifiers,
    ).delete()


def _save_liturgical_collections(parish: Parish, parish_data: dict) -> None:
    _replace_typed_collection(
        MassIntention,
        parish,
        parish_data.get('intentions'),
        id_prefix='n',
        defaults_from_legacy=mass_intention_field_defaults_from_legacy,
    )
    _replace_typed_collection(
        MassScheduleSlot,
        parish,
        parish_data.get('massSchedule'),
        id_prefix='ms',
        defaults_from_legacy=mass_schedule_slot_field_defaults_from_legacy,
    )
    _replace_typed_collection(
        MassException,
        parish,
        parish_data.get('massExceptions'),
        id_prefix='mx',
        defaults_from_legacy=mass_exception_field_defaults_from_legacy,
    )
    _replace_typed_collection(
        MassScheduleLogEntry,
        parish,
        parish_data.get('massScheduleLog'),
        id_prefix='msl',
        defaults_from_legacy=mass_schedule_log_field_defaults_from_legacy,
    )

    layout_payload = parish_data.get('zupniListicLayout')
    template_payload = parish_data.get('zupniListicTemplate')
    if layout_payload is None and template_payload is None:
        BulletinLayout.objects.filter(parish=parish).delete()
    else:
        BulletinLayout.objects.update_or_create(
            parish=parish,
            defaults={
                'payload': copy.deepcopy(layout_payload or {}),
                'template_payload': copy.deepcopy(template_payload),
            },
        )
    _replace_list_collection(
        BulletinIssue,
        parish,
        parish_data.get('zupniListicIssues'),
        id_prefix='li',
    )


def save_liturgical_collections(parish: Parish, parish_data: dict) -> None:
    """Spremi samo kolekcije koje mijenja aktivni liturgijski JSON API."""
    with transaction.atomic():
        _save_liturgical_collections(parish, parish_data)
        parish.save(update_fields=['updated_at'])


def _save_financial_collections(parish: Parish, parish_data: dict) -> None:
    _replace_typed_collection(
        ParishDebt,
        parish,
        parish_data.get('parishDebts'),
        id_prefix='pd',
        defaults_from_legacy=parish_debt_field_defaults_from_legacy,
    )
    _replace_typed_collection(
        Invoice,
        parish,
        parish_data.get('invoices'),
        id_prefix='inv',
        defaults_from_legacy=invoice_field_defaults_from_legacy,
    )
    _replace_typed_collection(
        CashbookEntry,
        parish,
        parish_data.get('cashbook'),
        id_prefix='cb',
        defaults_from_legacy=cashbook_field_defaults_from_legacy,
    )

    lukno_raw = parish_data.get('luknoDefaultAmount', 0)
    try:
        lukno_amount = Decimal(str(lukno_raw or 0))
    except (InvalidOperation, TypeError, ValueError):
        lukno_amount = Decimal('0')
    FinanceSettings.objects.update_or_create(
        parish=parish,
        defaults={'lukno_default_amount': lukno_amount},
    )


def save_financial_collections(parish: Parish, parish_data: dict) -> None:
    """Spremi samo ORM kolekcije koje mijenjaju financijske stranice."""
    with transaction.atomic():
        _save_financial_collections(parish, parish_data)
        parish.save(update_fields=['updated_at'])


def load_operational_collections(parish: Parish) -> dict:
    """Sastavi legacy parish_data dict isključivo iz ORM-a."""
    parish_data: dict = {}

    parish_data['streets'] = [
        street_as_legacy_record(street)
        for street in Street.objects.filter(parish=parish).order_by(
            'sort_order',
            'name',
        )
    ]
    parish_data['families'] = [
        household_as_legacy_record(household)
        for household in Household.objects.filter(parish=parish)
        .prefetch_related(
            Prefetch(
                'memberships',
                queryset=HouseholdMembership.objects.select_related(
                    'person',
                ).order_by('sort_order', 'historical_name'),
            ),
            'contributions',
        )
        .order_by('surname', 'public_identifier')
    ]
    parish_data['visits'] = [
        visit_as_legacy_record(visit)
        for visit in PastoralVisit.objects.filter(parish=parish).order_by(
            'public_identifier'
        )
    ]

    parish_data['tasks'] = [
        office_task_as_legacy_record(task)
        for task in OfficeTask.objects.filter(parish=parish)
    ]
    parish_data['events'] = [
        calendar_event_as_legacy_record(event)
        for event in ParishCalendarEvent.objects.filter(parish=parish)
    ]
    parish_data['publicSubmissions'] = [
        public_submission_as_legacy_record(submission)
        for submission in PublicSubmission.objects.filter(parish=parish)
    ]
    parish_data['announcements'] = [
        announcement_as_legacy_record(announcement)
        for announcement in Announcement.objects.filter(parish=parish)
    ]
    parish_data['docBindings'] = _payloads_from_queryset(
        DocumentBinding.objects.filter(parish=parish)
    )

    parish_data['pastoralCouncil'] = {}
    parish_data['economicCouncil'] = {}
    councils = (
        Council.objects.filter(parish=parish)
        .prefetch_related(
            Prefetch(
                'memberships',
                queryset=CouncilMembership.objects.select_related('person'),
            ),
        )
    )
    for council in councils:
        payload = council_as_legacy_record(council)
        if council.council_type == Council.CouncilType.PASTORAL:
            parish_data['pastoralCouncil'] = payload
        elif council.council_type == Council.CouncilType.ECONOMIC:
            parish_data['economicCouncil'] = payload
    founding_decree = ParishFoundingDecree.objects.filter(parish=parish).first()
    parish_data['parishDecree'] = decree_as_legacy_record(founding_decree)

    parish_data['parishDebts'] = [
        parish_debt_as_legacy_record(debt)
        for debt in ParishDebt.objects.filter(parish=parish)
    ]
    parish_data['invoices'] = [
        invoice_as_legacy_record(invoice)
        for invoice in Invoice.objects.filter(parish=parish)
    ]
    parish_data['cashbook'] = [
        cashbook_as_legacy_record(entry)
        for entry in CashbookEntry.objects.filter(parish=parish)
    ]
    finance_settings = FinanceSettings.objects.filter(parish=parish).first()
    parish_data['luknoDefaultAmount'] = float(
        finance_settings.lukno_default_amount
        if finance_settings is not None
        else 0
    )

    parish_data['intentions'] = [
        mass_intention_as_legacy_record(intention)
        for intention in MassIntention.objects.filter(parish=parish)
    ]
    parish_data['massSchedule'] = [
        mass_schedule_slot_as_legacy_record(slot)
        for slot in MassScheduleSlot.objects.filter(parish=parish)
    ]
    parish_data['massExceptions'] = [
        mass_exception_as_legacy_record(exception)
        for exception in MassException.objects.filter(parish=parish)
    ]
    parish_data['massScheduleLog'] = [
        mass_schedule_log_as_legacy_record(entry)
        for entry in MassScheduleLogEntry.objects.filter(parish=parish)
    ]

    bulletin_layout = BulletinLayout.objects.filter(parish=parish).first()
    if bulletin_layout:
        parish_data['zupniListicLayout'] = copy.deepcopy(
            bulletin_layout.payload or {}
        )
        parish_data['zupniListicTemplate'] = copy.deepcopy(
            bulletin_layout.template_payload
        )
    else:
        parish_data['zupniListicLayout'] = {}
        parish_data['zupniListicTemplate'] = None
    if not (parish_data['zupniListicLayout'] or {}).get('blocks'):
        default_layout = copy.deepcopy(load_config()['defaultLayout'])
        default_layout['updatedAt'] = datetime.now().astimezone().isoformat()
        parish_data['zupniListicLayout'] = default_layout

    parish_data['zupniListicIssues'] = _payloads_from_queryset(
        BulletinIssue.objects.filter(parish=parish)
    )

    # Izvedeno polje — nikad se ne sprema u ORM.
    parish_data['parishioners'] = []
    for family in parish_data['families']:
        for family_member in family.get('members') or []:
            parish_data['parishioners'].append({
                'id': family_member.get('id'),
                'family': family.get('surname', ''),
                'name': family_member.get('name', ''),
                'phone': family.get('phone', ''),
                'email': family.get('email', ''),
                'status': (
                    'aktivan'
                    if family.get('status') == 'aktivna'
                    else family.get('status', '')
                ),
                'roles': family_member.get('roles') or [],
            })

    return parish_data


def save_operational_collections(parish: Parish, parish_data: dict) -> None:
    """Upsert svih ORM-backed kolekcija iz legacy dicta."""
    with transaction.atomic():
        # Streets
        street_rows = list(parish_data.get('streets') or [])
        keep_streets = set()
        for index, record in enumerate(street_rows):
            if not isinstance(record, dict):
                continue
            public_identifier = _record_identifier(record, 'st', index)
            payload = copy.deepcopy(record)
            payload.setdefault('id', public_identifier)
            keep_streets.add(public_identifier)
            Street.objects.update_or_create(
                parish=parish,
                public_identifier=public_identifier,
                defaults=street_field_defaults_from_legacy(payload),
            )
        Street.objects.filter(parish=parish).exclude(
            public_identifier__in=keep_streets,
        ).delete()

        street_by_public_id = {
            street.public_identifier: street
            for street in Street.objects.filter(parish=parish)
        }

        # Families / households
        family_rows = list(parish_data.get('families') or [])
        keep_families = set()
        for index, record in enumerate(family_rows):
            if not isinstance(record, dict):
                continue
            public_identifier = _record_identifier(record, 'f', index)
            payload = copy.deepcopy(record)
            payload.setdefault('id', public_identifier)
            keep_families.add(public_identifier)
            street_public_identifier = str(payload.get('streetId') or '')
            household, _created = Household.objects.update_or_create(
                parish=parish,
                public_identifier=public_identifier,
                defaults=household_field_defaults_from_legacy(
                    payload,
                    street=street_by_public_id.get(street_public_identifier),
                ),
            )
            sync_household_nested_records(household, payload)
        Household.objects.filter(parish=parish).exclude(
            public_identifier__in=keep_families,
        ).delete()

        household_by_public_id = {
            household.public_identifier: household
            for household in Household.objects.filter(parish=parish)
        }

        visit_rows = list(parish_data.get('visits') or [])
        keep_visits = set()
        for index, record in enumerate(visit_rows):
            if not isinstance(record, dict):
                continue
            public_identifier = _record_identifier(record, 'v', index)
            payload = copy.deepcopy(record)
            payload.setdefault('id', public_identifier)
            keep_visits.add(public_identifier)
            family_public_identifier = str(payload.get('familyId') or '')
            PastoralVisit.objects.update_or_create(
                parish=parish,
                public_identifier=public_identifier,
                defaults=visit_field_defaults_from_legacy(
                    payload,
                    household=household_by_public_id.get(family_public_identifier),
                ),
            )
        PastoralVisit.objects.filter(parish=parish).exclude(
            public_identifier__in=keep_visits,
        ).delete()

        task_rows = list(parish_data.get('tasks') or [])
        keep_tasks = set()
        for index, record in enumerate(task_rows):
            if not isinstance(record, dict):
                continue
            public_identifier = _record_identifier(record, 't', index)
            payload = copy.deepcopy(record)
            payload.setdefault('id', public_identifier)
            keep_tasks.add(public_identifier)
            OfficeTask.objects.update_or_create(
                parish=parish,
                public_identifier=public_identifier,
                defaults=office_task_field_defaults_from_legacy(payload),
            )
        OfficeTask.objects.filter(parish=parish).exclude(
            public_identifier__in=keep_tasks,
        ).delete()

        event_rows = list(parish_data.get('events') or [])
        keep_events = set()
        for index, record in enumerate(event_rows):
            if not isinstance(record, dict):
                continue
            public_identifier = _record_identifier(record, 'e', index)
            payload = copy.deepcopy(record)
            payload.setdefault('id', public_identifier)
            keep_events.add(public_identifier)
            ParishCalendarEvent.objects.update_or_create(
                parish=parish,
                public_identifier=public_identifier,
                defaults=calendar_event_field_defaults_from_legacy(payload),
            )
        ParishCalendarEvent.objects.filter(parish=parish).exclude(
            public_identifier__in=keep_events,
        ).delete()

        submission_rows = list(parish_data.get('publicSubmissions') or [])
        keep_submissions = set()
        for index, record in enumerate(submission_rows):
            if not isinstance(record, dict):
                continue
            public_identifier = _record_identifier(record, 'ps', index)
            payload = copy.deepcopy(record)
            payload.setdefault('id', public_identifier)
            keep_submissions.add(public_identifier)
            PublicSubmission.objects.update_or_create(
                parish=parish,
                public_identifier=public_identifier,
                defaults=public_submission_field_defaults_from_legacy(payload),
            )
        PublicSubmission.objects.filter(parish=parish).exclude(
            public_identifier__in=keep_submissions,
        ).delete()

        announcement_rows = list(parish_data.get('announcements') or [])
        keep_announcements = set()
        for index, record in enumerate(announcement_rows):
            if not isinstance(record, dict):
                continue
            public_identifier = _record_identifier(record, 'ann', index)
            payload = copy.deepcopy(record)
            payload.setdefault('id', public_identifier)
            keep_announcements.add(public_identifier)
            Announcement.objects.update_or_create(
                parish=parish,
                public_identifier=public_identifier,
                defaults=announcement_field_defaults_from_legacy(payload),
            )
        Announcement.objects.filter(parish=parish).exclude(
            public_identifier__in=keep_announcements,
        ).delete()

        _replace_list_collection(
            DocumentBinding,
            parish,
            parish_data.get('docBindings'),
            id_prefix='db',
        )

        sync_council_from_legacy(
            parish,
            Council.CouncilType.PASTORAL,
            parish_data.get('pastoralCouncil'),
        )
        sync_council_from_legacy(
            parish,
            Council.CouncilType.ECONOMIC,
            parish_data.get('economicCouncil'),
        )
        sync_founding_decree_from_legacy(
            parish,
            parish_data.get('parishDecree'),
        )

        _save_financial_collections(parish, parish_data)

        _save_liturgical_collections(parish, parish_data)


def strip_orm_backed_keys(parish_data: dict) -> dict:
    """Vrati kopiju bez kolekcija koje žive u ORM-u (Parish.data ostaje prazan)."""
    cleaned = copy.deepcopy(parish_data)
    for key in ORM_BACKED_COLLECTION_KEYS:
        cleaned.pop(key, None)
    # Already-cutover sacrament/registry keys also stripped by caller
    return cleaned
