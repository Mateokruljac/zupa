from datetime import date
from decimal import Decimal, InvalidOperation
import re

from django.db import migrations


def parse_date(raw_value):
    if not raw_value:
        return None
    try:
        return date.fromisoformat(str(raw_value))
    except (TypeError, ValueError):
        return None


def parse_person_name(full_name):
    name_parts = str(full_name or '').split()
    if len(name_parts) < 2:
        return None
    return ' '.join(name_parts[:-1]), name_parts[-1]


def parse_entry_number(entry_reference, register_year):
    normalized_reference = str(entry_reference or '').strip()
    if normalized_reference.isdigit():
        return int(normalized_reference)
    reference_match = re.fullmatch(r'(\d{4})\s*/\s*(\d+)', normalized_reference)
    if reference_match and int(reference_match.group(1)) == register_year:
        return int(reference_match.group(2))
    return None


def decimal_amount(raw_value):
    try:
        return Decimal(str(raw_value or 0))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


def get_template_version(models):
    register_template, _ = models['RegisterTemplate'].objects.get_or_create(
        code='baptism-register',
        defaults={
            'event_type': 'baptism',
            'name': 'Matična knjiga krštenih',
            'owner_scope': 'system',
            'is_official': False,
            'is_active': True,
        },
    )
    template_version, _ = models['RegisterTemplateVersion'].objects.get_or_create(
        template=register_template,
        version_number=1,
        defaults={
            'status': 'draft',
            'field_schema': [],
            'validation_schema': {
                'official_form_approved': False,
            },
            'terminology': {
                'event': 'Krštenje',
                'recipient': 'Krštenik',
            },
            'print_configuration': {'enabled': False},
        },
    )
    return template_version


def get_register_book(models, parish, template_version, baptism_records):
    existing_book_link = models['LegacyRecordLink'].objects.filter(
        parish=parish,
        source_collection='registryBooks',
        register_book__isnull=False,
    ).select_related('register_book').first()
    if existing_book_link:
        return existing_book_link.register_book

    existing_book = models['RegisterBook'].objects.filter(
        parish=parish,
        template_version__template__event_type='baptism',
    ).first()
    if existing_book:
        return existing_book

    legacy_book = next(
        (
            register_book
            for register_book in (parish.data or {}).get('registryBooks', [])
            if register_book.get('type') == 'krštenja'
        ),
        {},
    )
    available_years = {
        baptism_date.year
        for baptism_date in (
            parse_date(record.get('baptismDate'))
            for record in baptism_records
        )
        if baptism_date
    }
    return models['RegisterBook'].objects.create(
        parish=parish,
        template_version=template_version,
        title=legacy_book.get('title') or 'Matična knjiga krštenih',
        year_from=min(available_years) if available_years else None,
        year_until=max(available_years) if available_years else None,
        location=legacy_book.get('location') or '',
        custodian=legacy_book.get('custodian') or '',
        status='draft',
        notes=legacy_book.get('notes') or '',
    )


def create_relational_baptism(
    models,
    parish,
    baptism_record,
    template_version,
    register_book,
):
    source_identifier = str(baptism_record['id']).strip()
    baptism_date = parse_date(baptism_record.get('baptismDate'))
    parsed_name = parse_person_name(baptism_record.get('childName'))
    person = None
    if parsed_name:
        given_names, surname = parsed_name
        person = models['Person'].objects.create(
            parish=parish,
            given_names=given_names,
            surname=surname,
            date_of_birth=parse_date(baptism_record.get('birthDate')),
            normalized_given_names=given_names.casefold(),
            normalized_surname=surname.casefold(),
        )

    event = models['SacramentalEvent'].objects.create(
        parish=parish,
        public_identifier=source_identifier,
        event_type='baptism',
        event_date=baptism_date,
        celebrating_parish=parish,
        minister_name=baptism_record.get('celebrant') or '',
        liturgical_tradition=parish.default_liturgical_tradition,
        canonical_tradition=(
            parish.church_sui_iuris.canonical_tradition
            if parish.church_sui_iuris_id
            else 'unconfirmed'
        ),
        status='draft',
        source='legacy_import',
    )
    models['EventParticipant'].objects.create(
        parish=parish,
        event=event,
        person=person,
        role='recipient',
        historical_name=baptism_record.get('childName') or '',
        display_order=0,
    )
    for role, field_name, display_order in (
        ('parent', 'parents', 10),
        ('godparent', 'godparents', 20),
    ):
        historical_name = str(baptism_record.get(field_name) or '').strip()
        if historical_name:
            models['EventParticipant'].objects.create(
                parish=parish,
                event=event,
                role=role,
                historical_name=historical_name,
                display_order=display_order,
            )

    models['BaptismDetails'].objects.create(
        event=event,
        godparent_certificate_received=bool(
            baptism_record.get('godparentCertReceived', False)
        ),
        operational_status=baptism_record.get('status') or 'upis',
        stipend=decimal_amount(
            baptism_record.get('stipend', baptism_record.get('gift', 0))
        ),
        stipend_paid=bool(baptism_record.get('stipendPaid', False)),
        legacy_operational_data={},
    )

    register_entry = None
    if baptism_date:
        register_book_year, _ = models['RegisterBookYear'].objects.get_or_create(
            register_book=register_book,
            year=baptism_date.year,
        )
        entry_reference = str(baptism_record.get('registryNo') or '').strip()
        entry_number = parse_entry_number(entry_reference, baptism_date.year)
        if entry_number and models['RegisterEntry'].objects.filter(
            register_book_year=register_book_year,
            entry_number=entry_number,
        ).exists():
            entry_number = None
        register_entry = models['RegisterEntry'].objects.create(
            parish=parish,
            register_book_year=register_book_year,
            event=event,
            template_version=template_version,
            entry_number=entry_number,
            entry_reference=entry_reference,
            entry_date=baptism_date,
            status='draft',
        )

    models['LegacyRecordLink'].objects.get_or_create(
        parish=parish,
        source_collection='baptisms',
        source_identifier=source_identifier,
        defaults={
            'sacramental_event': event,
            'register_entry': register_entry,
            'person': person,
        },
    )
    return event


def cutover_baptisms(apps, schema_editor):
    model_names = (
        'BaptismDetails', 'EventParticipant', 'LegacyRecordLink', 'Parish',
        'Person', 'RegisterBook', 'RegisterBookYear', 'RegisterEntry',
        'RegisterTemplate', 'RegisterTemplateVersion', 'SacramentalEvent',
    )
    models = {
        model_name: apps.get_model('pastoral', model_name)
        for model_name in model_names
    }
    template_version = get_template_version(models)

    for parish in models['Parish'].objects.select_related(
        'church_sui_iuris', 'default_liturgical_tradition'
    ):
        parish_data = dict(parish.data or {})
        baptism_records = list(parish_data.get('baptisms') or [])
        source_identifiers = [
            str(record.get('id') or '').strip()
            for record in baptism_records
        ]
        if any(not source_identifier for source_identifier in source_identifiers):
            raise RuntimeError(
                f'Župa {parish.slug} ima krštenje bez stabilnog identifikatora.'
            )
        if len(source_identifiers) != len(set(source_identifiers)):
            raise RuntimeError(
                f'Župa {parish.slug} ima ponovljene identifikatore krštenja.'
            )

        register_book = get_register_book(
            models, parish, template_version, baptism_records
        )
        for baptism_record in baptism_records:
            source_identifier = str(baptism_record['id']).strip()
            event = models['SacramentalEvent'].objects.filter(
                parish=parish,
                event_type='baptism',
                legacy_record_links__source_collection='baptisms',
                legacy_record_links__source_identifier=source_identifier,
            ).first()
            if event is None:
                event = create_relational_baptism(
                    models,
                    parish,
                    baptism_record,
                    template_version,
                    register_book,
                )
            event.public_identifier = source_identifier
            event.save(update_fields=('public_identifier',))

            baptism_details = models['BaptismDetails'].objects.get(event=event)
            baptism_details.operational_status = (
                baptism_record.get('status') or 'upis'
            )
            baptism_details.stipend = decimal_amount(
                baptism_record.get('stipend', baptism_record.get('gift', 0))
            )
            baptism_details.stipend_paid = bool(
                baptism_record.get('stipendPaid', False)
            )
            baptism_details.save(update_fields=(
                'operational_status', 'stipend', 'stipend_paid',
            ))

        migrated_count = models['SacramentalEvent'].objects.filter(
            parish=parish,
            event_type='baptism',
            public_identifier__in=source_identifiers,
        ).exclude(status='cancelled').count()
        if migrated_count != len(baptism_records):
            raise RuntimeError(
                f'Župa {parish.slug}: očekivano {len(baptism_records)}, '
                f'migrirano {migrated_count} krštenja. JSON nije uklonjen.'
            )

        parish_data.pop('baptisms', None)
        parish.data = parish_data
        parish.save(update_fields=('data',))


class Migration(migrations.Migration):

    dependencies = [
        ('pastoral', '0009_baptismdetails_operational_status_and_more'),
    ]

    operations = [
        migrations.RunPython(cutover_baptisms, migrations.RunPython.noop),
    ]
