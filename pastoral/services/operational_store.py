"""Učitavanje i spremanje operativnih kolekcija župe iz ORM-a.

Ovo je adapter, ne izvor istine. UI i dalje razgovara camelCase dictom
(bivši `Parish.data`). Čitanje SCD2 ide samo s otvorenih redova
(`Street.current`, `Household.current`). `Parish.data` se na spremanju prazni.

Nove poslovne kolone ne smiju ići u `payload`.
"""
from __future__ import annotations

import copy
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Prefetch

from core.models import close_current_scd2_rows
from core.utils import _parse_iso_date, _decimal_amount
from pastoral.models import Parish
from financije.models import (
    CashbookEntry,
    FinanceSettings,
    Invoice,
    ParishDebt,
)
from django_multitenant.schema import with_tenant_schema
from liturgija.models import (
    BulletinIssue,
    MassException,
    MassIntention,
    MassScheduleSlot,
)
from liturgija.services.bulletin_records import (
    bulletin_issue_as_legacy_record,
    bulletin_issue_field_defaults_from_legacy,
)
from liturgija.services.mass_records import (
    mass_exception_as_legacy_record,
    mass_intention_as_legacy_record,
    mass_schedule_slot_as_legacy_record,
)
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
    upsert_current_street,
)
from zupa_vjernici.services.household_records import (
    household_as_legacy_record,
    household_field_defaults_from_legacy,
    sync_household_nested_records,
    upsert_current_household,
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
    'zupniListicIssues',
})


def _weekdays_list(value) -> list[int]:
    """JSON lista dana → intovi; nebrojčane stavke se preskaču."""
    if not isinstance(value, list):
        return []
    weekdays = []
    for item in value:
        try:
            weekdays.append(int(item))
        except (TypeError, ValueError):
            continue
    return weekdays


def mass_schedule_slot_field_defaults_from_legacy(record: dict) -> dict:
    """JS dict → kwargs za ``MassScheduleSlot``."""
    return {
        'day_label': str(record.get('day') or ''),
        'mass_time': str(record.get('time') or ''),
        'weekdays': _weekdays_list(record.get('weekdays')),
        'location': str(record.get('location') or ''),
        'notes': str(record.get('notes') or ''),
        'valid_from': _parse_iso_date(record.get('validFrom')),
        'valid_until': _parse_iso_date(record.get('validUntil')),
        'no_mass': bool(record.get('noMass')),
    }


def mass_intention_field_defaults_from_legacy(record: dict) -> dict:
    """JS dict → kwargs za ``MassIntention``."""
    return {
        'intention_date': _parse_iso_date(record.get('date')),
        'mass_time': str(record.get('massTime') or ''),
        'intention_for': str(record.get('intentionFor') or ''),
        'stipend': _decimal_amount(record.get('stipend')),
        'is_paid': bool(record.get('paid')),
        'notes': str(record.get('notes') or ''),
    }


def mass_exception_field_defaults_from_legacy(record: dict) -> dict:
    """JS dict → kwargs za iznimku mise."""
    return {
        'exception_date': _parse_iso_date(record.get('date')),
        'cancel_all': bool(record.get('cancelAll')),
        'cancel_times': list(record.get('cancelTimes') or [])
        if isinstance(record.get('cancelTimes'), list)
        else [],
        'note': str(record.get('note') or ''),
    }


def _record_identifier(record: dict, fallback_prefix: str, index: int) -> str:
    record_id = str(record.get('id') or '').strip()
    if record_id:
        return record_id
    return f'{fallback_prefix}-{index + 1}'


def _payloads_from_queryset(queryset) -> list[dict]:
    return [copy.deepcopy(row.payload or {}) for row in queryset]


@with_tenant_schema
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


@with_tenant_schema
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


def _replace_mass_intentions(records: list) -> None:
    keep_pks = set()
    for record in records or []:
        if not isinstance(record, dict):
            continue
        defaults = mass_intention_field_defaults_from_legacy(record)
        try:
            pk = uuid.UUID(str(record.get('id')))
        except (ValueError, TypeError, AttributeError):
            pk = None
        if pk:
            intention = MassIntention.objects.filter(pk=pk).first()
            if intention is not None:
                for field_name, field_value in defaults.items():
                    setattr(intention, field_name, field_value)
                intention.save()
                keep_pks.add(intention.pk)
                continue
        intention = MassIntention(**defaults)
        intention.save()
        keep_pks.add(intention.pk)
    MassIntention.objects.exclude(pk__in=keep_pks).delete()


def _replace_mass_schedule_slots(records: list) -> None:
    keep_pks = set()
    for record in records or []:
        if not isinstance(record, dict):
            continue
        defaults = mass_schedule_slot_field_defaults_from_legacy(record)
        try:
            pk = uuid.UUID(str(record.get('id')))
        except (ValueError, TypeError, AttributeError):
            pk = None
        if pk:
            slot = MassScheduleSlot.objects.filter(pk=pk).first()
            if slot is not None:
                for field_name, field_value in defaults.items():
                    setattr(slot, field_name, field_value)
                slot.save()
                keep_pks.add(slot.pk)
                continue
        slot = MassScheduleSlot(**defaults)
        slot.save()
        keep_pks.add(slot.pk)
    MassScheduleSlot.objects.exclude(pk__in=keep_pks).delete()


def _replace_mass_exceptions(records: list) -> None:
    keep_pks = set()
    for record in records or []:
        if not isinstance(record, dict):
            continue
        defaults = mass_exception_field_defaults_from_legacy(record)
        try:
            pk = uuid.UUID(str(record.get('id')))
        except (ValueError, TypeError, AttributeError):
            pk = None
        if pk:
            exception = MassException.objects.filter(pk=pk).first()
            if exception is not None:
                for field_name, field_value in defaults.items():
                    setattr(exception, field_name, field_value)
                exception.save()
                keep_pks.add(exception.pk)
                continue
        exception = MassException(**defaults)
        exception.save()
        keep_pks.add(exception.pk)
    MassException.objects.exclude(pk__in=keep_pks).delete()


def _replace_bulletin_issues(records: list) -> None:
    keep_pks = set()
    for record in records or []:
        if not isinstance(record, dict):
            continue
        defaults = bulletin_issue_field_defaults_from_legacy(record)
        if defaults['week_start'] is None or defaults['week_end'] is None:
            continue
        try:
            pk = uuid.UUID(str(record.get('id')))
        except (ValueError, TypeError, AttributeError):
            pk = None
        issue = None
        if pk:
            issue = BulletinIssue.objects.filter(pk=pk).first()
        if issue is None:
            issue = BulletinIssue(**defaults)
            issue.save()
        else:
            for field_name, field_value in defaults.items():
                setattr(issue, field_name, field_value)
            issue.save()
        keep_pks.add(issue.pk)
    BulletinIssue.objects.exclude(pk__in=keep_pks).delete()


@with_tenant_schema
def _save_liturgical_collections(parish: Parish, parish_data: dict) -> None:
    _replace_mass_intentions(parish_data.get('intentions'))
    _replace_mass_schedule_slots(parish_data.get('massSchedule'))
    _replace_mass_exceptions(parish_data.get('massExceptions'))
    _replace_bulletin_issues(parish_data.get('zupniListicIssues'))


@with_tenant_schema
def save_liturgical_collections(parish: Parish, parish_data: dict) -> None:
    """Spremi samo kolekcije koje mijenja aktivni liturgijski JSON API."""
    with transaction.atomic():
        _save_liturgical_collections(parish, parish_data)
        parish.save(update_fields=['updated_at'])


@with_tenant_schema
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


@with_tenant_schema
def save_financial_collections(parish: Parish, parish_data: dict) -> None:
    """Spremi samo ORM kolekcije koje mijenjaju financijske stranice."""
    with transaction.atomic():
        _save_financial_collections(parish, parish_data)
        parish.save(update_fields=['updated_at'])


@with_tenant_schema
def load_operational_collections(parish: Parish) -> dict:
    """Sastavi legacy parish_data dict isključivo iz ORM-a."""
    parish_data: dict = {}

    parish_data['streets'] = [
        street_as_legacy_record(street)
        for street in Street.current.filter(parish=parish).order_by(
            'sort_order',
            'name',
        )
    ]
    parish_data['families'] = [
        household_as_legacy_record(household)
        for household in Household.current.filter(parish=parish)
        .prefetch_related(
            Prefetch(
                'memberships',
                queryset=HouseholdMembership.current.select_related(
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
                queryset=CouncilMembership.current.select_related('person'),
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
        for intention in MassIntention.objects.all()
    ]
    parish_data['massSchedule'] = [
        mass_schedule_slot_as_legacy_record(slot)
        for slot in MassScheduleSlot.objects.all()
    ]
    parish_data['massExceptions'] = [
        mass_exception_as_legacy_record(exception)
        for exception in MassException.objects.all()
    ]

    parish_data['zupniListicIssues'] = [
        bulletin_issue_as_legacy_record(issue)
        for issue in BulletinIssue.objects.all()
    ]

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


@with_tenant_schema
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
            upsert_current_street(
                parish,
                public_identifier,
                street_field_defaults_from_legacy(payload),
            )
        close_current_scd2_rows(
            Street.objects.filter(parish=parish).exclude(
                public_identifier__in=keep_streets,
            ),
        )

        street_by_public_id = {
            street.public_identifier: street
            for street in Street.current.filter(parish=parish)
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
            household, _created = upsert_current_household(
                parish,
                public_identifier,
                household_field_defaults_from_legacy(
                    payload,
                    street=street_by_public_id.get(street_public_identifier),
                ),
            )
            sync_household_nested_records(household, payload)
        close_current_scd2_rows(
            Household.objects.filter(parish=parish).exclude(
                public_identifier__in=keep_families,
            ),
        )

        household_by_public_id = {
            household.public_identifier: household
            for household in Household.current.filter(parish=parish)
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
