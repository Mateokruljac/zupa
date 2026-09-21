"""Relational persistence for non-sacramental register-book entries."""
from __future__ import annotations

from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction

from isprave.models import (
    GeneralRegisterEntry,
    RegisterBook,
    RegisterBookYear,
)
from django_multitenant.schema import with_tenant_schema
from pastoral.models import Parish


def _parse_required_date(raw_value) -> date:
    if isinstance(raw_value, date):
        return raw_value
    try:
        return date.fromisoformat(str(raw_value))
    except (TypeError, ValueError) as error:
        raise ValidationError({'recordDate': 'Unesite ispravan datum.'}) from error


@with_tenant_schema
def relational_general_entries_as_dictionaries(parish: Parish) -> list[dict]:
    entries = GeneralRegisterEntry.objects.filter(
        register_book_year__register_book__parish=parish,
    ).select_related('register_book_year__register_book')
    return [
        {
            'id': entry.public_identifier,
            'bookId': entry.register_book_year.register_book.public_identifier,
            'year': entry.register_book_year.year,
            'registryNo': entry.registry_reference,
            'subjectName': entry.subject_name,
            'recordDate': entry.record_date.isoformat(),
            'place': entry.place,
            'celebrant': entry.responsible_name,
            'status': entry.operational_status,
        }
        for entry in entries
    ]


@transaction.atomic
@with_tenant_schema
def reconcile_general_register_entries(
    parish: Parish,
    entry_records: list[dict],
) -> None:
    retained_entry_ids = []
    seen_identifiers = set()
    for entry_record in entry_records:
        public_identifier = str(entry_record.get('id') or '').strip()
        if not public_identifier:
            raise ValidationError('Opći matični zapis nema stabilni identifikator.')
        if public_identifier in seen_identifiers:
            raise ValidationError('Identifikator općeg matičnog zapisa se ponavlja.')
        seen_identifiers.add(public_identifier)

        book_identifier = str(entry_record.get('bookId') or '').strip()
        try:
            register_book = RegisterBook.objects.get(
                parish=parish,
                public_identifier=book_identifier,
            )
        except RegisterBook.DoesNotExist as error:
            raise ValidationError('Matična knjiga općeg zapisa nije pronađena.') from error
        record_date = _parse_required_date(entry_record.get('recordDate'))
        registry_year = int(entry_record.get('year') or record_date.year)
        if record_date.year != registry_year:
            raise ValidationError('Datum zapisa ne pripada odabranoj godini knjige.')
        register_book_year, _ = RegisterBookYear.objects.get_or_create(
            register_book=register_book,
            year=registry_year,
        )
        existing_entry = GeneralRegisterEntry.objects.filter(
            register_book_year=register_book_year,
            public_identifier=public_identifier,
        ).first()
        registry_reference = str(entry_record.get('registryNo') or '').strip()
        if not registry_reference and existing_entry:
            registry_reference = existing_entry.registry_reference
        if not registry_reference:
            next_entry_number = max(register_book_year.next_entry_number, 1)
            registry_reference = f'{registry_year}/{next_entry_number}'
            register_book_year.next_entry_number = next_entry_number + 1
            register_book_year.save(update_fields=('next_entry_number',))
        entry, _ = GeneralRegisterEntry.objects.update_or_create(
            register_book_year=register_book_year,
            public_identifier=public_identifier,
            defaults={
                'registry_reference': registry_reference,
                'subject_name': str(
                    entry_record.get('subjectName') or ''
                ).strip(),
                'record_date': record_date,
                'place': str(entry_record.get('place') or '').strip(),
                'responsible_name': str(
                    entry_record.get('celebrant') or ''
                ).strip(),
                'operational_status': str(
                    entry_record.get('status') or 'upisano'
                ).strip(),
            },
        )
        retained_entry_ids.append(entry.id)

    GeneralRegisterEntry.objects.filter(
        register_book_year__register_book__parish=parish,
    ).exclude(id__in=retained_entry_ids).delete()
