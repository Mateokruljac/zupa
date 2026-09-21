from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
import re

from django.db import transaction

from sakramenti.models import (
    BaptismDetails,
    EventParticipant,
    SacramentalEvent,
)
from django_multitenant.schema import with_tenant_schema
from sakramenti.services.family_card_sacraments import exclude_family_card_events
from pastoral.models import Parish
from zupa_vjernici.models import Person
from isprave.models import (
    RegisterBook,
    RegisterBookYear,
    RegisterEntry,
    RegisterTemplate,
    RegisterTemplateVersion,
    RegistryAuditEvent,
)


LEGACY_BAPTISM_TEMPLATE_CODE = 'legacy-baptism-compatibility'

def parse_iso_date(raw_value) -> date | None:
    if not raw_value:
        return None
    try:
        return date.fromisoformat(str(raw_value))
    except (TypeError, ValueError):
        return None


def split_person_name(full_name: str) -> tuple[str, str] | None:
    name_parts = str(full_name or '').split()
    if len(name_parts) < 2:
        return None
    return ' '.join(name_parts[:-1]), name_parts[-1]


def parse_entry_number(entry_reference: str, register_year: int) -> int | None:
    stripped_reference = str(entry_reference or '').strip()
    if stripped_reference.isdigit():
        return int(stripped_reference)
    year_and_number_match = re.fullmatch(r'(\d{4})\s*/\s*(\d+)', stripped_reference)
    if year_and_number_match and int(year_and_number_match.group(1)) == register_year:
        return int(year_and_number_match.group(2))
    return None


def baptism_stipend_amount(baptism_record: dict) -> Decimal:
    try:
        return Decimal(str(
            baptism_record.get('stipend', baptism_record.get('gift', 0)) or 0
        ))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


@with_tenant_schema
def get_compatibility_template_version() -> RegisterTemplateVersion:
    template, _ = RegisterTemplate.objects.get_or_create(
        code=LEGACY_BAPTISM_TEMPLATE_CODE,
        defaults={
            'event_type': SacramentalEvent.EventType.BAPTISM,
            'name': 'Kompatibilni predložak postojećih zapisa krštenja',
            'owner_scope': RegisterTemplate.OwnerScope.SYSTEM,
            'is_official': False,
            'is_active': True,
        },
    )
    template_version, _ = RegisterTemplateVersion.objects.get_or_create(
        template=template,
        version_number=1,
        defaults={
            'status': RegisterTemplateVersion.Status.PUBLISHED,
            'field_schema': [
                {'code': 'recipient', 'label': 'Krštenik', 'source': 'participant:recipient'},
                {'code': 'parents', 'label': 'Roditelji', 'source': 'participant:parent'},
                {'code': 'godparents', 'label': 'Kumovi', 'source': 'participant:godparent'},
                {'code': 'minister', 'label': 'Slavitelj', 'source': 'event:minister_name'},
            ],
            'validation_schema': {
                'compatibility_only': True,
                'official_form_approved': False,
            },
            'terminology': {'event': 'Krštenje', 'recipient': 'Krštenik'},
            'print_configuration': {'enabled': False},
        },
    )
    return template_version


def _book_years_from_legacy_data(parish: Parish, legacy_book: dict) -> set[int]:
    available_years = {
        int(configured_year)
        for configured_year in legacy_book.get('years') or []
        if str(configured_year).isdigit()
    }
    last_entry_date = parse_iso_date(legacy_book.get('lastEntry'))
    if last_entry_date:
        available_years.add(last_entry_date.year)
    return available_years


@with_tenant_schema
def _create_or_find_register_book(
    parish: Parish,
    template_version: RegisterTemplateVersion,
) -> RegisterBook:
    legacy_books = [
        registry_book
        for registry_book in parish.data.get('registryBooks') or []
        if registry_book.get('type') == 'krštenja'
    ]
    legacy_book = legacy_books[0] if legacy_books else {
        'id': '__generated_baptism_import_book__',
        'title': 'Uvezeni postojeći zapisi krštenja',
        'notes': 'Privremena knjiga nastala sigurnom migracijom postojećih zapisa.',
    }
    register_book = RegisterBook.objects.filter(
        parish=parish,
        template_version__template__event_type=SacramentalEvent.EventType.BAPTISM,
    ).first()
    if register_book is None:
        available_years = _book_years_from_legacy_data(parish, legacy_book)
        register_book = RegisterBook.objects.create(
            parish=parish,
            template_version=template_version,
            title=legacy_book.get('title') or 'Knjiga krštenih',
            year_from=min(available_years) if available_years else None,
            year_until=max(available_years) if available_years else None,
            location=legacy_book.get('location') or '',
            custodian=legacy_book.get('custodian') or '',
            status=RegisterBook.Status.DRAFT,
            notes=legacy_book.get('notes') or '',
        )

    for register_year in _book_years_from_legacy_data(parish, legacy_book):
        RegisterBookYear.objects.get_or_create(
            register_book=register_book,
            year=register_year,
        )
    return register_book


@with_tenant_schema
def _set_single_historical_participant(
    parish: Parish,
    event: SacramentalEvent,
    role: str,
    historical_name: str,
    display_order: int,
) -> None:
    participants = event.participants.filter(role=role).order_by('display_order', 'id')
    primary_participant = participants.first()
    normalized_name = str(historical_name or '').strip()
    if not normalized_name:
        participants.delete()
        return
    if primary_participant is None:
        EventParticipant.objects.create(
            parish=parish,
            event=event,
            role=role,
            historical_name=normalized_name,
            display_order=display_order,
        )
        return
    primary_participant.historical_name = normalized_name
    primary_participant.display_order = display_order
    primary_participant.save(update_fields=('historical_name', 'display_order'))
    participants.exclude(pk=primary_participant.pk).delete()


@with_tenant_schema
def _synchronize_recipient(
    parish: Parish,
    event: SacramentalEvent,
    baptism_record: dict,
) -> None:
    historical_name = str(baptism_record.get('childName') or '').strip()
    split_name = split_person_name(historical_name)
    recipient_participant = event.participants.filter(
        role=EventParticipant.Role.RECIPIENT
    ).select_related('person').order_by('display_order', 'id').first()
    recipient = recipient_participant.person if recipient_participant else None
    if split_name:
        given_names, surname = split_name
        if recipient is None:
            recipient = Person.objects.create(
                parish=parish,
                given_names=given_names,
                surname=surname,
                date_of_birth=parse_iso_date(baptism_record.get('birthDate')),
            )
        else:
            recipient.given_names = given_names
            recipient.surname = surname
            recipient.date_of_birth = parse_iso_date(baptism_record.get('birthDate'))
            recipient.save(update_fields=('given_names', 'surname', 'date_of_birth'))
    else:
        recipient = None

    if recipient_participant is None:
        EventParticipant.objects.create(
            parish=parish,
            event=event,
            role=EventParticipant.Role.RECIPIENT,
            person=recipient,
            historical_name=historical_name,
            display_order=0,
        )
    else:
        recipient_participant.person = recipient
        recipient_participant.historical_name = historical_name
        recipient_participant.display_order = 0
        recipient_participant.save(
            update_fields=('person', 'historical_name', 'display_order')
        )
        event.participants.filter(
            role=EventParticipant.Role.RECIPIENT
        ).exclude(pk=recipient_participant.pk).delete()


@with_tenant_schema
def _synchronize_register_entry(
    parish: Parish,
    event: SacramentalEvent,
    baptism_record: dict,
    register_book: RegisterBook,
    template_version: RegisterTemplateVersion,
    actor=None,
) -> None:
    register_entry = getattr(event, 'register_entry', None)
    baptism_date = parse_iso_date(baptism_record.get('baptismDate'))
    if baptism_date is None:
        if register_entry:
            register_entry.status = RegisterEntry.Status.CANCELLED
            register_entry.save(update_fields=('status', 'updated_at'))
        return

    register_book_year, _ = RegisterBookYear.objects.get_or_create(
        register_book=register_book,
        year=baptism_date.year,
    )
    entry_reference = str(baptism_record.get('registryNo') or '').strip()
    entry_number = parse_entry_number(entry_reference, baptism_date.year)
    if not entry_reference and register_entry and register_entry.entry_reference:
        entry_reference = register_entry.entry_reference
        entry_number = register_entry.entry_number
    if not entry_reference:
        entry_number = max(register_book_year.next_entry_number, 1)
        while RegisterEntry.objects.filter(
            register_book_year=register_book_year,
            entry_number=entry_number,
        ).exclude(pk=register_entry.pk if register_entry else None).exists():
            entry_number += 1
        entry_reference = f'{baptism_date.year}/{entry_number}'
    occupied_entry_numbers = RegisterEntry.objects.filter(
        register_book_year=register_book_year,
        entry_number=entry_number,
    )
    if register_entry:
        occupied_entry_numbers = occupied_entry_numbers.exclude(
            pk=register_entry.pk
        )
    if entry_number and occupied_entry_numbers.exists():
        entry_number = None

    if register_entry is None:
        register_entry = RegisterEntry.objects.create(
            parish=parish,
            register_book_year=register_book_year,
            event=event,
            template_version=template_version,
            entry_number=entry_number,
            entry_reference=entry_reference,
            entry_date=baptism_date,
            status=RegisterEntry.Status.DRAFT,
            created_by=actor if getattr(actor, 'is_authenticated', False) else None,
            updated_by=actor if getattr(actor, 'is_authenticated', False) else None,
        )
    else:
        register_entry.register_book_year = register_book_year
        register_entry.template_version = template_version
        register_entry.entry_number = entry_number
        register_entry.entry_reference = entry_reference
        register_entry.entry_date = baptism_date
        if register_entry.status == RegisterEntry.Status.CANCELLED:
            register_entry.status = RegisterEntry.Status.DRAFT
        register_entry.updated_by = (
            actor if getattr(actor, 'is_authenticated', False) else None
        )
        register_entry.save(update_fields=(
            'register_book_year', 'template_version', 'entry_number',
            'entry_reference', 'entry_date', 'status', 'updated_by', 'updated_at',
        ))
    if entry_number and register_book_year.next_entry_number <= entry_number:
        register_book_year.next_entry_number = entry_number + 1
        register_book_year.save(update_fields=('next_entry_number',))


@transaction.atomic
@with_tenant_schema
def synchronize_baptism_record(
    parish: Parish,
    baptism_record: dict,
    actor=None,
) -> SacramentalEvent:
    """Create or update one baptism in the relational source of truth."""
    source_identifier = str(baptism_record.get('id') or '').strip()
    if not source_identifier:
        raise ValueError('Krštenje nema stabilni identifikator.')

    template_version = get_compatibility_template_version()
    register_book = _create_or_find_register_book(
        parish, template_version
    )
    event = SacramentalEvent.objects.filter(
        parish=parish,
        event_type=SacramentalEvent.EventType.BAPTISM,
        public_identifier=source_identifier,
    ).first()
    created = event is None
    if created:
        event = SacramentalEvent.objects.create(
            parish=parish,
            public_identifier=source_identifier,
            event_type=SacramentalEvent.EventType.BAPTISM,
            source=SacramentalEvent.Source.MANUAL,
            status=SacramentalEvent.Status.DRAFT,
            celebrating_parish=parish,
            created_by=actor if getattr(actor, 'is_authenticated', False) else None,
            updated_by=actor if getattr(actor, 'is_authenticated', False) else None,
        )

    event.event_date = parse_iso_date(baptism_record.get('baptismDate'))
    event.minister_name = baptism_record.get('celebrant') or ''
    event.liturgical_tradition = parish.default_liturgical_tradition
    event.canonical_tradition = parish.canonical_tradition_for_events()
    if event.status == SacramentalEvent.Status.CANCELLED:
        event.status = SacramentalEvent.Status.DRAFT
    event.updated_by = actor if getattr(actor, 'is_authenticated', False) else None
    event.save(update_fields=(
        'event_date', 'minister_name', 'liturgical_tradition',
        'canonical_tradition', 'status', 'updated_by', 'updated_at',
    ))

    _synchronize_recipient(parish, event, baptism_record)
    _set_single_historical_participant(
        parish, event, EventParticipant.Role.PARENT,
        baptism_record.get('parents', ''), 10,
    )
    _set_single_historical_participant(
        parish, event, EventParticipant.Role.GODPARENT,
        baptism_record.get('godparents', ''), 20,
    )
    baptism_details, _ = BaptismDetails.objects.get_or_create(event=event)
    baptism_details.godparent_certificate_received = bool(
        baptism_record.get('godparentCertReceived', False)
    )
    baptism_details.operational_status = baptism_record.get('status') or 'upis'
    baptism_details.stipend = baptism_stipend_amount(baptism_record)
    baptism_details.stipend_paid = bool(baptism_record.get('stipendPaid', False))
    baptism_details.save(update_fields=(
        'godparent_certificate_received',
        'operational_status', 'stipend', 'stipend_paid',
    ))
    _synchronize_register_entry(
        parish, event, baptism_record, register_book,
        template_version, actor=actor,
    )
    RegistryAuditEvent.objects.create(
        parish=parish,
        actor=actor if getattr(actor, 'is_authenticated', False) else None,
        event_type='baptism_created' if created else 'baptism_updated',
        target_type='baptism',
        target_id=source_identifier,
        changed_fields=[
            'recipient', 'birth_date', 'baptism_date', 'parents',
            'godparents', 'minister', 'register_reference', 'status',
        ],
        metadata={'source': 'active_json_interface'},
    )
    return event


@transaction.atomic
@with_tenant_schema
def cancel_synchronized_baptism(
    parish: Parish,
    source_identifier: str,
    actor=None,
) -> bool:
    event = SacramentalEvent.objects.filter(
        parish=parish,
        event_type=SacramentalEvent.EventType.BAPTISM,
        public_identifier=source_identifier,
    ).select_related('register_entry').first()
    if event is None:
        return False
    event.status = SacramentalEvent.Status.CANCELLED
    event.updated_by = actor if getattr(actor, 'is_authenticated', False) else None
    event.save(update_fields=('status', 'updated_by', 'updated_at'))
    register_entry = getattr(event, 'register_entry', None)
    if register_entry:
        register_entry.status = RegisterEntry.Status.CANCELLED
        register_entry.updated_by = event.updated_by
        register_entry.save(update_fields=('status', 'updated_by', 'updated_at'))
    RegistryAuditEvent.objects.create(
        parish=parish,
        actor=event.updated_by,
        event_type='baptism_cancelled',
        target_type='baptism',
        target_id=source_identifier,
        changed_fields=['status'],
        metadata={'source': 'active_json_interface'},
    )
    return True


@transaction.atomic
@with_tenant_schema
def reconcile_baptism_records(
    parish: Parish,
    baptism_records: list[dict],
    actor=None,
) -> dict:
    """Make relational mirrors match an entire active JSON baptism collection."""
    active_identifiers = {
        str(baptism_record.get('id'))
        for baptism_record in baptism_records
        if baptism_record.get('id')
    }
    synchronized_count = 0
    for baptism_record in baptism_records:
        if not baptism_record.get('id'):
            continue
        synchronize_baptism_record(parish, baptism_record, actor=actor)
        synchronized_count += 1

    cancelled_count = 0
    linked_identifiers = SacramentalEvent.objects.filter(
        parish=parish,
        event_type=SacramentalEvent.EventType.BAPTISM,
    ).values_list('public_identifier', flat=True)
    for source_identifier in linked_identifiers:
        if source_identifier in active_identifiers:
            continue
        if cancel_synchronized_baptism(parish, source_identifier, actor=actor):
            cancelled_count += 1
    return {
        'synchronized_count': synchronized_count,
        'cancelled_count': cancelled_count,
    }


@transaction.atomic
@with_tenant_schema
def apply_legacy_baptism_backfill(parish: Parish) -> BaptismBackfillReport:
    locked_parish = Parish.objects.select_for_update().get(pk=parish.pk)
    report = analyze_legacy_baptisms(locked_parish)
    if not report.records_ready and not report.already_imported:
        ParishRegistryConfiguration.objects.update_or_create(
            parish=locked_parish,
            defaults={
                'baptism_backfill_completed_at': (
                    timezone.now() if report.records_skipped == 0 else None
                ),
            },
        )
        RegistryAuditEvent.objects.create(
            parish=locked_parish,
            event_type='legacy_baptism_backfill',
            target_type='parish',
            target_id=str(locked_parish.pk),
            metadata={
                'source_records': report.source_records,
                'records_created': 0,
                'records_skipped': report.records_skipped,
                'compatibility_template_official': False,
            },
        )
        return report

    template_version = get_compatibility_template_version()
    register_book = _create_or_find_register_book(
        locked_parish, template_version, report
    )
    existing_identifiers = set(
        LegacyRecordLink.objects.filter(
            parish=locked_parish,
            source_collection='baptisms',
        ).values_list('source_identifier', flat=True)
    )
    for baptism_record in locked_parish.data.get('baptisms') or []:
        source_identifier = str(baptism_record.get('id') or '').strip()
        if not source_identifier or source_identifier in existing_identifiers:
            continue
        if split_person_name(baptism_record.get('childName', '')) is None:
            continue
        if baptism_record.get('baptismDate') and not parse_iso_date(
            baptism_record.get('baptismDate')
        ):
            continue
        if baptism_record.get('birthDate') and not parse_iso_date(
            baptism_record.get('birthDate')
        ):
            continue
        _create_baptism_record(
            locked_parish, baptism_record, register_book, template_version
        )
        existing_identifiers.add(source_identifier)
        report.records_created += 1

    ParishRegistryConfiguration.objects.update_or_create(
        parish=locked_parish,
        defaults={
            'baptism_backfill_completed_at': (
                timezone.now() if report.records_skipped == 0 else None
            ),
        },
    )
    RegistryAuditEvent.objects.create(
        parish=locked_parish,
        event_type='legacy_baptism_backfill',
        target_type='parish',
        target_id=str(locked_parish.pk),
        metadata={
            'source_records': report.source_records,
            'records_created': report.records_created,
            'records_skipped': report.records_skipped,
            'compatibility_template_official': False,
        },
    )
    return report


@with_tenant_schema
def relational_baptisms_as_legacy_dictionaries(parish: Parish) -> list[dict]:
    baptism_events = exclude_family_card_events(
        SacramentalEvent.objects.filter(
            parish=parish,
            event_type=SacramentalEvent.EventType.BAPTISM,
            baptism_details__isnull=False,
        )
        .exclude(status=SacramentalEvent.Status.CANCELLED)
        .select_related(
            'baptism_details',
            'register_entry',
        )
        .prefetch_related('participants__person')
    )
    records = []
    for event in baptism_events:
        participants = list(event.participants.all())
        participant_names = {
            participant.role: participant.historical_name
            for participant in participants
            if participant.historical_name
        }
        recipient_participant = next(
            (
                participant
                for participant in participants
                if participant.role == EventParticipant.Role.RECIPIENT
            ),
            None,
        )
        recipient = recipient_participant.person if recipient_participant else None
        baptism_details = event.baptism_details
        financial_amount = float(baptism_details.stipend)
        register_entry = getattr(event, 'register_entry', None)
        records.append({
            'id': event.public_identifier,
            'childName': participant_names.get(EventParticipant.Role.RECIPIENT, ''),
            'birthDate': (
                recipient.date_of_birth.isoformat()
                if recipient and recipient.date_of_birth
                else ''
            ),
            'baptismDate': event.event_date.isoformat() if event.event_date else '',
            'parents': participant_names.get(EventParticipant.Role.PARENT, ''),
            'godparents': participant_names.get(EventParticipant.Role.GODPARENT, ''),
            'celebrant': event.minister_name,
            'registryNo': register_entry.entry_reference if register_entry else '',
            'status': baptism_details.operational_status,
            'gift': financial_amount,
            'stipend': financial_amount,
            'stipendPaid': baptism_details.stipend_paid,
            'godparentCertReceived': baptism_details.godparent_certificate_received,
        })
    return sorted(records, key=lambda record: record['id'])


@with_tenant_schema
def select_baptism_records_for_read(
    parish: Parish,
    legacy_baptism_records: list[dict],
) -> tuple[list[dict], str]:
    """Use relational reads only when enabled and demonstrably complete."""
    configuration = ParishRegistryConfiguration.objects.filter(
        parish=parish,
        relational_baptisms_enabled=True,
    ).first()
    if configuration is None:
        return list(legacy_baptism_records), 'legacy-json'

    relational_records = relational_baptisms_as_legacy_dictionaries(parish)
    comparison_fields = (
        'childName', 'birthDate', 'baptismDate', 'parents', 'godparents',
        'celebrant', 'registryNo', 'status', 'godparentCertReceived',
    )
    legacy_by_identifier = {
        str(record.get('id')): record
        for record in legacy_baptism_records
        if record.get('id')
    }
    relational_by_identifier = {
        str(record.get('id')): record
        for record in relational_records
        if record.get('id')
    }
    if legacy_by_identifier.keys() != relational_by_identifier.keys():
        return list(legacy_baptism_records), 'legacy-json-safety-fallback'
    for source_identifier, legacy_record in legacy_by_identifier.items():
        relational_record = relational_by_identifier[source_identifier]
        if any(
            legacy_record.get(field_name, '')
            != relational_record.get(field_name, '')
            for field_name in comparison_fields
        ):
            return list(legacy_baptism_records), 'legacy-json-safety-fallback'
    return relational_records, 'relational'


def compare_legacy_and_relational_baptisms(parish: Parish) -> dict:
    comparison_fields = (
        'childName', 'birthDate', 'baptismDate', 'parents', 'godparents',
        'celebrant', 'registryNo', 'status', 'godparentCertReceived',
    )
    legacy_records = {
        str(record.get('id')): record
        for record in parish.data.get('baptisms') or []
        if record.get('id')
    }
    relational_records = {
        record['id']: record
        for record in relational_baptisms_as_legacy_dictionaries(parish)
    }
    differing_field_count = 0
    mismatched_record_count = 0
    for source_identifier in legacy_records.keys() & relational_records.keys():
        record_has_difference = False
        for field_name in comparison_fields:
            if legacy_records[source_identifier].get(field_name, '') != relational_records[source_identifier].get(field_name, ''):
                differing_field_count += 1
                record_has_difference = True
        if record_has_difference:
            mismatched_record_count += 1
    return {
        'legacy_count': len(legacy_records),
        'relational_count': len(relational_records),
        'missing_relational_count': len(legacy_records.keys() - relational_records.keys()),
        'unexpected_relational_count': len(relational_records.keys() - legacy_records.keys()),
        'mismatched_record_count': mismatched_record_count,
        'differing_field_count': differing_field_count,
    }
