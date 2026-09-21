"""Create governed register entries for existing sacramental records."""
from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.db import transaction

from sakramenti.models import (
    EventParticipant,
    FormationCandidate,
    SacramentalEvent,
)
from pastoral.models import Parish
from isprave.models import (
    RegisterBook,
    RegisterBookYear,
    RegisterEntry,
)


EVENT_TYPE_BY_REGISTRY_TYPE = {
    RegisterBook.RegistryType.MARRIAGES: SacramentalEvent.EventType.MARRIAGE,
    RegisterBook.RegistryType.DECEASED: SacramentalEvent.EventType.FUNERAL,
    RegisterBook.RegistryType.CONFIRMATIONS: SacramentalEvent.EventType.CONFIRMATION,
}


def _entry_number_from_reference(entry_reference: str, registry_year: int) -> int | None:
    normalized_reference = str(entry_reference or '').strip()
    if normalized_reference.isdigit():
        return int(normalized_reference)
    reference_match = re.fullmatch(r'(\d{4})\s*/\s*(\d+)', normalized_reference)
    if reference_match and int(reference_match.group(1)) == registry_year:
        return int(reference_match.group(2))
    return None


def _confirmation_event(
    parish: Parish,
    candidate_identifier: str,
    actor=None,
) -> SacramentalEvent:
    candidate = FormationCandidate.objects.select_related(
        'program_year', 'sacramental_event'
    ).get(
        program_year__parish=parish,
        program_year__program_type='confirmation',
        public_identifier=candidate_identifier,
    )
    program_year = candidate.program_year
    event = candidate.sacramental_event
    authenticated_actor = actor if getattr(actor, 'is_authenticated', False) else None
    if event is None:
        event = SacramentalEvent.objects.create(
            parish=parish,
            public_identifier=candidate.public_identifier,
            event_type=SacramentalEvent.EventType.CONFIRMATION,
            event_date=program_year.ceremony_date,
            celebrating_parish=parish,
            minister_name=program_year.celebrant_name,
            liturgical_tradition=parish.default_liturgical_tradition,
            canonical_tradition=parish.canonical_tradition_for_events(),
            status=SacramentalEvent.Status.DRAFT,
            source=SacramentalEvent.Source.MANUAL,
            created_by=authenticated_actor,
            updated_by=authenticated_actor,
        )
        EventParticipant.objects.create(
            parish=parish,
            event=event,
            person=candidate.person,
            role=EventParticipant.Role.RECIPIENT,
            historical_name=candidate.historical_name,
            display_order=0,
        )
        if candidate.sponsor_name:
            EventParticipant.objects.create(
                parish=parish,
                event=event,
                role=EventParticipant.Role.GODPARENT,
                historical_name=candidate.sponsor_name,
                display_order=10,
            )
        candidate.sacramental_event = event
        candidate.save(update_fields=('sacramental_event', 'updated_at'))
    else:
        event.event_date = program_year.ceremony_date
        event.minister_name = program_year.celebrant_name
        event.updated_by = authenticated_actor
        event.save(update_fields=(
            'event_date', 'minister_name', 'updated_by', 'updated_at',
        ))
    return event


def _event_for_registry_record(
    parish: Parish,
    registry_type: str,
    source_identifier: str,
    actor=None,
) -> SacramentalEvent:
    if registry_type == RegisterBook.RegistryType.CONFIRMATIONS:
        return _confirmation_event(parish, source_identifier, actor=actor)
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
    if event.event_date and event.event_date.year != registry_year:
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
            entry_date=event.event_date,
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
        register_entry.entry_date = event.event_date
        register_entry.updated_by = authenticated_actor
        register_entry.save()

    if entry_number and register_book_year.next_entry_number <= entry_number:
        register_book_year.next_entry_number = entry_number + 1
        register_book_year.save(update_fields=('next_entry_number',))
    if event.event_date and (
        register_book.last_entry_date is None
        or event.event_date >= register_book.last_entry_date
    ):
        register_book.last_entry_date = event.event_date
        register_book.last_entry_reference = normalized_reference
        register_book.save(update_fields=(
            'last_entry_date', 'last_entry_reference', 'updated_at',
        ))
    return register_entry
