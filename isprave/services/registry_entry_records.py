"""Create governed register entries for existing sacramental records."""
from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.db import transaction

from sakramenti.models import SacramentalEvent
from django_multitenant.schema import with_tenant_schema
from pastoral.models import Parish
from isprave.models import (
    RegisterBook,
    RegisterBookYear,
    RegisterEntry,
)


EVENT_TYPE_BY_REGISTRY_TYPE = {
    RegisterBook.RegistryType.MARRIAGES: SacramentalEvent.EventType.MARRIAGE,
    RegisterBook.RegistryType.DECEASED: SacramentalEvent.EventType.FUNERAL,
}


def _entry_number_from_reference(entry_reference: str, registry_year: int) -> int | None:
    normalized_reference = str(entry_reference or '').strip()
    if normalized_reference.isdigit():
        return int(normalized_reference)
    reference_match = re.fullmatch(r'(\d{4})\s*/\s*(\d+)', normalized_reference)
    if reference_match and int(reference_match.group(1)) == registry_year:
        return int(reference_match.group(2))
    return None


@with_tenant_schema
def _event_for_registry_record(
    parish: Parish,
    registry_type: str,
    source_identifier: str,
    actor=None,
) -> SacramentalEvent:
    event_type = EVENT_TYPE_BY_REGISTRY_TYPE.get(registry_type)
    if event_type is None:
        raise ValidationError('Ova vrsta knjige nema sakramentalni događaj.')
    try:
        return SacramentalEvent.objects.get(
            parish=parish,
            event_type=event_type,
            public_identifier=source_identifier,
        )
    except SacramentalEvent.DoesNotExist as error:
        raise ValidationError('Sakramentalni zapis nije pronađen.') from error


@transaction.atomic
@with_tenant_schema
def synchronize_registry_entry(
    parish: Parish,
    register_book_identifier: str,
    registry_year: int,
    registry_type: str,
    source_identifier: str,
    entry_reference: str,
    actor=None,
) -> RegisterEntry:
    try:
        register_book = RegisterBook.objects.select_related(
            'template_version'
        ).get(
            parish=parish,
            public_identifier=register_book_identifier,
            registry_type=registry_type,
        )
    except RegisterBook.DoesNotExist as error:
        raise ValidationError('Matična knjiga nije pronađena.') from error
    if register_book.template_version_id is None:
        raise ValidationError('Matična knjiga nema pripremljenu verziju predloška.')

    event = _event_for_registry_record(
        parish,
        registry_type,
        source_identifier,
        actor=actor,
    )
    registry_record_date = event.event_date
    if registry_type == RegisterBook.RegistryType.DECEASED:
        funeral_details = getattr(event, 'funeral_details', None)
        registry_record_date = (
            funeral_details.death_date if funeral_details else event.event_date
        )
    if registry_record_date and registry_record_date.year != registry_year:
        raise ValidationError('Datum sakramentalnog događaja ne pripada odabranoj godini.')

    register_book_year, _ = RegisterBookYear.objects.get_or_create(
        register_book=register_book,
        year=registry_year,
    )
    normalized_reference = str(entry_reference or '').strip()
    entry_number = _entry_number_from_reference(
        normalized_reference,
        registry_year,
    )
    existing_entry = RegisterEntry.objects.filter(event=event).first()
    if not normalized_reference and existing_entry and existing_entry.entry_reference:
        normalized_reference = existing_entry.entry_reference
        entry_number = existing_entry.entry_number
    if not normalized_reference:
        entry_number = max(register_book_year.next_entry_number, 1)
        while RegisterEntry.objects.filter(
            register_book_year=register_book_year,
            entry_number=entry_number,
        ).exists():
            entry_number += 1
        normalized_reference = f'{registry_year}/{entry_number}'
    occupied_numbers = RegisterEntry.objects.filter(
        register_book_year=register_book_year,
        entry_number=entry_number,
    )
    if existing_entry:
        occupied_numbers = occupied_numbers.exclude(pk=existing_entry.pk)
    if entry_number and occupied_numbers.exists():
        raise ValidationError('Redni broj već postoji u odabranoj godini knjige.')

    authenticated_actor = actor if getattr(actor, 'is_authenticated', False) else None
    if existing_entry is None:
        register_entry = RegisterEntry.objects.create(
            parish=parish,
            register_book_year=register_book_year,
            event=event,
            template_version=register_book.template_version,
            entry_number=entry_number,
            entry_reference=normalized_reference,
            entry_date=registry_record_date,
            status=RegisterEntry.Status.DRAFT,
            created_by=authenticated_actor,
            updated_by=authenticated_actor,
        )
    else:
        register_entry = existing_entry
        register_entry.register_book_year = register_book_year
        register_entry.template_version = register_book.template_version
        register_entry.entry_number = entry_number
        register_entry.entry_reference = normalized_reference
        register_entry.entry_date = registry_record_date
        register_entry.updated_by = authenticated_actor
        register_entry.save()

    if entry_number and register_book_year.next_entry_number <= entry_number:
        register_book_year.next_entry_number = entry_number + 1
        register_book_year.save(update_fields=('next_entry_number',))
    if registry_record_date and (
        register_book.last_entry_date is None
        or registry_record_date >= register_book.last_entry_date
    ):
        register_book.last_entry_date = registry_record_date
        register_book.last_entry_reference = normalized_reference
        register_book.save(update_fields=(
            'last_entry_date', 'last_entry_reference', 'updated_at',
        ))
    return register_entry
