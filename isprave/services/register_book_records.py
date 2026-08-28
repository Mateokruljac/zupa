"""Relational persistence and stable UI projection for register books."""
from __future__ import annotations

from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction

from pastoral.models import Parish
from isprave.models import (
    RegisterBook,
    RegisterBookYear,
    RegisterTemplate,
    RegisterTemplateVersion,
)
from sakramenti.models import SacramentalEvent


EVENT_TYPE_BY_REGISTRY_TYPE = {
    RegisterBook.RegistryType.BAPTISMS: SacramentalEvent.EventType.BAPTISM,
    RegisterBook.RegistryType.MARRIAGES: SacramentalEvent.EventType.MARRIAGE,
    RegisterBook.RegistryType.DECEASED: SacramentalEvent.EventType.FUNERAL,
    RegisterBook.RegistryType.CONFIRMATIONS: SacramentalEvent.EventType.CONFIRMATION,
}


def _date_as_text(calendar_date: date | None) -> str:
    return calendar_date.isoformat() if calendar_date else ''


def _parse_optional_date(raw_value) -> date | None:
    if not raw_value:
        return None
    if isinstance(raw_value, date):
        return raw_value
    try:
        return date.fromisoformat(str(raw_value))
    except (TypeError, ValueError) as error:
        raise ValidationError({'lastEntry': 'Unesite ispravan datum.'}) from error


def _template_version_for_registry_type(
    registry_type: str,
) -> RegisterTemplateVersion | None:
    event_type = EVENT_TYPE_BY_REGISTRY_TYPE.get(registry_type)
    if event_type is None:
        return None
    register_template, _ = RegisterTemplate.objects.get_or_create(
        code=f'{event_type}-register-compatibility',
        defaults={
            'event_type': event_type,
            'name': f'Kompatibilni predložak: {registry_type}',
            'owner_scope': RegisterTemplate.OwnerScope.SYSTEM,
            'is_official': False,
            'is_active': True,
        },
    )
    template_version, _ = RegisterTemplateVersion.objects.get_or_create(
        template=register_template,
        version_number=1,
        defaults={
            'status': RegisterTemplateVersion.Status.DRAFT,
            'field_schema': [],
            'validation_schema': {'official_form_approved': False},
            'terminology': {},
            'print_configuration': {'enabled': False},
        },
    )
    return template_version


def relational_register_books_as_dictionaries(parish: Parish) -> list[dict]:
    register_books = RegisterBook.objects.filter(parish=parish).exclude(
        status=RegisterBook.Status.ARCHIVED
    ).prefetch_related('years')
    return [
        {
            'id': register_book.public_identifier,
            'title': register_book.title,
            'type': register_book.registry_type,
            'location': register_book.location,
            'lastEntry': _date_as_text(register_book.last_entry_date),
            'lastNo': register_book.last_entry_reference,
            'custodian': register_book.custodian,
            'status': register_book.operational_status,
            'notes': register_book.notes,
            'years': [
                register_book_year.year
                for register_book_year in register_book.years.all()
            ],
        }
        for register_book in register_books
    ]


@transaction.atomic
def reconcile_register_books(parish: Parish, register_book_records: list[dict]) -> None:
    retained_register_book_ids = []
    seen_identifiers = set()
    for register_book_record in register_book_records:
        public_identifier = str(register_book_record.get('id') or '').strip()
        if not public_identifier:
            raise ValidationError('Matična knjiga nema stabilni identifikator.')
        if public_identifier in seen_identifiers:
            raise ValidationError('Identifikator matične knjige se ponavlja.')
        seen_identifiers.add(public_identifier)

        registry_type = str(
            register_book_record.get('type') or RegisterBook.RegistryType.OTHER
        ).strip()
        valid_registry_types = {choice[0] for choice in RegisterBook.RegistryType.choices}
        if registry_type not in valid_registry_types:
            registry_type = RegisterBook.RegistryType.OTHER

        register_book = RegisterBook.objects.filter(
            parish=parish,
            public_identifier=public_identifier,
        ).first()
        template_version = _template_version_for_registry_type(registry_type)
        if register_book is None:
            register_book = RegisterBook(
                parish=parish,
                public_identifier=public_identifier,
            )
        elif (
            register_book.template_version_id
            and register_book.registry_type == registry_type
        ):
            template_version = register_book.template_version

        register_book.template_version = template_version
        register_book.registry_type = registry_type
        register_book.title = str(
            register_book_record.get('title') or 'Matična knjiga'
        ).strip()
        register_book.location = str(
            register_book_record.get('location') or ''
        ).strip()
        register_book.custodian = str(
            register_book_record.get('custodian') or ''
        ).strip()
        register_book.status = RegisterBook.Status.ACTIVE
        register_book.operational_status = str(
            register_book_record.get('status') or ''
        ).strip()
        register_book.last_entry_date = _parse_optional_date(
            register_book_record.get('lastEntry')
        )
        register_book.last_entry_reference = str(
            register_book_record.get('lastNo') or ''
        ).strip()
        register_book.notes = str(register_book_record.get('notes') or '').strip()
        register_book.save()
        retained_register_book_ids.append(register_book.id)

        configured_years = {
            int(configured_year)
            for configured_year in register_book_record.get('years') or []
            if str(configured_year).isdigit()
        }
        if register_book.last_entry_date:
            configured_years.add(register_book.last_entry_date.year)
        for registry_year in configured_years:
            RegisterBookYear.objects.get_or_create(
                register_book=register_book,
                year=registry_year,
            )
        all_years = list(
            register_book.years.values_list('year', flat=True)
        )
        register_book.year_from = min(all_years) if all_years else None
        register_book.year_until = max(all_years) if all_years else None
        register_book.save(update_fields=('year_from', 'year_until', 'updated_at'))

    RegisterBook.objects.filter(parish=parish).exclude(
        id__in=retained_register_book_ids
    ).update(status=RegisterBook.Status.ARCHIVED)
