"""POST akcije za matične knjige."""
from __future__ import annotations

from typing import TYPE_CHECKING
import uuid

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction

from isprave.forms import RegistryBookForm, RegistryRecordForm
from sakramenti.services.api_action_handlers.formation import (
    upsert_confirmation_candidate,
)
from sakramenti.services.baptism_records import synchronize_baptism_record
from isprave.services.registry_entry_records import synchronize_registry_entry
from sakramenti.services.sacrament_mutations import (
    add_sacrament_record,
    update_sacrament_record,
)

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


def handle_registry_books_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:

    if action_name == 'upsert_registry_book' and page_slug == 'maticne-knjige':
        registry_book_form = RegistryBookForm(request.POST)
        if registry_book_form.is_valid():
            cleaned_data = registry_book_form.cleaned_data
            registry_book_id = request.POST.get('book_id')
            registry_book_payload = {
                'title': cleaned_data['title'],
                'type': cleaned_data['book_type'],
                'location': cleaned_data.get('location') or '',
                'lastEntry': (
                    cleaned_data['last_entry'].isoformat()
                    if cleaned_data.get('last_entry')
                    else ''
                ),
                'lastNo': cleaned_data.get('last_no') or '',
                'custodian': cleaned_data.get('custodian') or '',
                'status': cleaned_data.get('status') or 'u župi',
                'notes': cleaned_data.get('notes') or '',
            }
            registry_books = parish_data.setdefault('registryBooks', [])
            if registry_book_id:
                registry_book = next(
                    (
                        existing_book
                        for existing_book in registry_books
                        if existing_book.get('id') == registry_book_id
                    ),
                    None,
                )
                if registry_book:
                    registry_book.update(registry_book_payload)
            else:
                registry_books.append({
                    'id': f"rk_{uuid.uuid4().hex[:8]}",
                    **registry_book_payload,
                })
            parish_data_service.save(parish_data)
            messages.success(request, 'Matična knjiga spremljena.')
        else:
            messages.error(request, 'Provjerite unos.')
        return True

    if action_name == 'add_registry_year' and page_slug == 'maticne-knjige':
        registry_book_id = request.POST.get('book_id', '')
        registry_year_value = request.POST.get('registry_year', '').strip()
        try:
            registry_year = int(registry_year_value)
        except ValueError:
            registry_year = None

        if registry_year is None or registry_year < 1000 or registry_year > 9999:
            messages.error(request, 'Upišite valjanu godinu s četiri znamenke.')
            return True

        registry_book = next(
            (
                existing_book
                for existing_book in parish_data.get('registryBooks', [])
                if existing_book.get('id') == registry_book_id
            ),
            None,
        )
        if not registry_book:
            messages.error(request, 'Matična knjiga nije pronađena.')
            return True

        configured_years = registry_book.setdefault('years', [])
        normalized_years = {
            int(existing_year)
            for existing_year in configured_years
            if str(existing_year).isdigit()
        }
        if registry_year in normalized_years:
            messages.info(request, f'{registry_year}. godina već postoji u knjizi.')
            return True

        normalized_years.add(registry_year)
        registry_book['years'] = sorted(normalized_years, reverse=True)
        parish_data_service.save(parish_data)
        messages.success(request, f'{registry_year}. godina dodana je u matičnu knjigu.')
        return True

    if action_name == 'add_registry_record' and page_slug == 'maticne-knjige':
        registry_book_id = request.POST.get('book_id', '')
        try:
            registry_year = int(request.POST.get('registry_year', ''))
        except ValueError:
            registry_year = None

        registry_book = next(
            (
                existing_book
                for existing_book in parish_data.get('registryBooks', [])
                if existing_book.get('id') == registry_book_id
            ),
            None,
        )
        if not registry_book or registry_year is None:
            messages.error(request, 'Matična knjiga ili godina nije pronađena.')
            return True

        registry_type = registry_book.get('type', 'ostalo')
        registry_record_form = RegistryRecordForm(
            request.POST,
            registry_type=registry_type,
            selected_year=registry_year,
        )
        if not registry_record_form.is_valid():
            messages.error(request, 'Provjerite obvezna polja novog zapisa.')
            return True

        cleaned_data = registry_record_form.cleaned_data
        record_date = cleaned_data['record_date']
        if record_date.year != registry_year:
            messages.error(
                request,
                f'Datum zapisa mora pripadati {registry_year}. godini.',
            )
            return True

        record_date_value = record_date.isoformat()
        shared_record_values = {
            'registryNo': cleaned_data.get('registry_number') or '',
            'celebrant': cleaned_data.get('celebrant') or '',
            'status': cleaned_data.get('status') or 'upisano',
        }
        baptism_record = None
        registry_source_record = None
        if registry_type == 'krštenja':
            baptism_record = add_sacrament_record(parish_data, 'baptisms', {
                **shared_record_values,
                'childName': cleaned_data['subject_name'],
                'baptismDate': record_date_value,
                'birthDate': (
                    cleaned_data['birth_date'].isoformat()
                    if cleaned_data.get('birth_date')
                    else ''
                ),
                'parents': cleaned_data.get('related_people') or '',
                'godparents': cleaned_data.get('sponsors') or '',
                'stipend': 0,
                'stipendPaid': False,
            })
        elif registry_type == 'vjenčanja':
            registry_source_record = add_sacrament_record(parish_data, 'weddings', {
                **shared_record_values,
                'couple': cleaned_data['subject_name'],
                'weddingDate': record_date_value,
                'church': cleaned_data.get('place') or '',
                'witnesses': cleaned_data.get('related_people') or '',
                'stipend': 0,
                'stipendPaid': False,
            })
        elif registry_type == 'umrli':
            registry_source_record = add_sacrament_record(parish_data, 'funerals', {
                **shared_record_values,
                'deceased': cleaned_data['subject_name'],
                'funeralDate': record_date_value,
                'deathDate': (
                    cleaned_data['birth_date'].isoformat()
                    if cleaned_data.get('birth_date')
                    else ''
                ),
                'cemetery': cleaned_data.get('place') or '',
                'stipend': 0,
                'stipendPaid': False,
            })
        elif registry_type == 'krizma':
            operation_result = upsert_confirmation_candidate(parish_data, {
                'year': registry_year,
                'name': cleaned_data['subject_name'],
                'birthDate': (
                    cleaned_data['birth_date'].isoformat()
                    if cleaned_data.get('birth_date')
                    else ''
                ),
                'baptized': (
                    cleaned_data['baptism_date'].isoformat()
                    if cleaned_data.get('baptism_date')
                    else ''
                ),
                'sponsor': cleaned_data.get('sponsors') or '',
                'status': cleaned_data.get('status') or 'upisano',
            })
            confirmation_candidate = operation_result.get('item', {})
            registry_source_record = confirmation_candidate
            confirmation_candidate['registryNo'] = (
                cleaned_data.get('registry_number') or ''
            )
            confirmation_group = next(
                (
                    existing_group
                    for existing_group in parish_data.get('confirmations', [])
                    if existing_group.get('year') == registry_year
                ),
                None,
            )
            if confirmation_group:
                confirmation_group['ceremonyDate'] = record_date_value
                if cleaned_data.get('celebrant'):
                    confirmation_group['bishop'] = cleaned_data['celebrant']
        else:
            add_sacrament_record(parish_data, 'registryEntries', {
                'bookId': registry_book_id,
                'year': registry_year,
                'registryNo': cleaned_data.get('registry_number') or '',
                'subjectName': cleaned_data['subject_name'],
                'recordDate': record_date_value,
                'place': cleaned_data.get('place') or '',
                'celebrant': cleaned_data.get('celebrant') or '',
                'status': cleaned_data.get('status') or 'upisano',
            })

        if record_date_value >= registry_book.get('lastEntry', ''):
            registry_book['lastEntry'] = record_date_value
            if cleaned_data.get('registry_number'):
                registry_book['lastNo'] = cleaned_data['registry_number']
        try:
            with transaction.atomic():
                parish_data_service.save(parish_data)
                if baptism_record:
                    synchronize_baptism_record(
                        parish_data_service.parish,
                        baptism_record,
                        actor=request.user,
                    )
                elif registry_source_record and registry_type in {
                    'vjenčanja', 'umrli', 'krizma',
                }:
                    synchronize_registry_entry(
                        parish_data_service.parish,
                        registry_book_id,
                        registry_year,
                        registry_type,
                        registry_source_record['id'],
                        cleaned_data.get('registry_number') or '',
                        actor=request.user,
                    )
        except ValidationError as validation_error:
            messages.error(request, ' '.join(validation_error.messages))
            return True
        messages.success(request, 'Novi matični zapis je spremljen.')
        return True

    if action_name == 'update_registry_record' and page_slug == 'maticne-knjige':
        registry_book_id = request.POST.get('book_id', '')
        source_identifier = request.POST.get('record_id', '')
        try:
            registry_year = int(request.POST.get('registry_year', ''))
        except ValueError:
            registry_year = None
        registry_book = next((
            existing_book
            for existing_book in parish_data.get('registryBooks', [])
            if existing_book.get('id') == registry_book_id
        ), None)
        if not registry_book or registry_year is None or not source_identifier:
            messages.error(request, 'Matični zapis nije pronađen.')
            return True

        registry_type = registry_book.get('type', 'ostalo')
        registry_record_form = RegistryRecordForm(
            request.POST,
            registry_type=registry_type,
            selected_year=registry_year,
        )
        if not registry_record_form.is_valid():
            messages.error(request, 'Provjerite unesene podatke zapisa.')
            return True
        cleaned_data = registry_record_form.cleaned_data
        record_date = cleaned_data['record_date']
        if record_date.year != registry_year:
            messages.error(
                request, f'Datum zapisa mora pripadati {registry_year}. godini.'
            )
            return True

        record_date_value = record_date.isoformat()
        shared_values = {
            'celebrant': cleaned_data.get('celebrant') or '',
            'status': cleaned_data.get('status') or 'upisano',
        }
        updated = False
        if registry_type == 'krštenja':
            updated = update_sacrament_record(
                parish_data, 'baptisms', source_identifier, {
                    **shared_values,
                    'childName': cleaned_data['subject_name'],
                    'baptismDate': record_date_value,
                    'birthDate': (
                        cleaned_data['birth_date'].isoformat()
                        if cleaned_data.get('birth_date') else ''
                    ),
                    'parents': cleaned_data.get('related_people') or '',
                    'godparents': cleaned_data.get('sponsors') or '',
                },
            )
        elif registry_type == 'vjenčanja':
            updated = update_sacrament_record(
                parish_data, 'weddings', source_identifier, {
                    **shared_values,
                    'couple': cleaned_data['subject_name'],
                    'weddingDate': record_date_value,
                    'church': cleaned_data.get('place') or '',
                    'witnesses': cleaned_data.get('related_people') or '',
                },
            )
        elif registry_type == 'umrli':
            updated = update_sacrament_record(
                parish_data, 'funerals', source_identifier, {
                    **shared_values,
                    'deceased': cleaned_data['subject_name'],
                    'funeralDate': record_date_value,
                    'deathDate': (
                        cleaned_data['birth_date'].isoformat()
                        if cleaned_data.get('birth_date') else ''
                    ),
                    'cemetery': cleaned_data.get('place') or '',
                },
            )
        elif registry_type == 'krizma':
            operation_result = upsert_confirmation_candidate(parish_data, {
                'id': source_identifier,
                'year': registry_year,
                'name': cleaned_data['subject_name'],
                'birthDate': (
                    cleaned_data['birth_date'].isoformat()
                    if cleaned_data.get('birth_date') else ''
                ),
                'baptized': (
                    cleaned_data['baptism_date'].isoformat()
                    if cleaned_data.get('baptism_date') else ''
                ),
                'sponsor': cleaned_data.get('sponsors') or '',
                'status': cleaned_data.get('status') or 'upisano',
            })
            updated = operation_result.get('ok', False)
            confirmation_group = next((
                existing_group
                for existing_group in parish_data.get('confirmations', [])
                if existing_group.get('year') == registry_year
            ), None)
            if confirmation_group:
                confirmation_group['ceremonyDate'] = record_date_value
                confirmation_group['bishop'] = cleaned_data.get('celebrant') or ''
        else:
            updated = update_sacrament_record(
                parish_data, 'registryEntries', source_identifier, {
                    **shared_values,
                    'subjectName': cleaned_data['subject_name'],
                    'recordDate': record_date_value,
                    'place': cleaned_data.get('place') or '',
                },
            )

        if not updated:
            messages.error(request, 'Matični zapis nije pronađen.')
            return True
        try:
            with transaction.atomic():
                parish_data_service.save(parish_data)
                if registry_type in {'vjenčanja', 'umrli', 'krizma'}:
                    synchronize_registry_entry(
                        parish_data_service.parish,
                        registry_book_id,
                        registry_year,
                        registry_type,
                        source_identifier,
                        '',
                        actor=request.user,
                    )
        except ValidationError as validation_error:
            messages.error(request, ' '.join(validation_error.messages))
            return True
        messages.success(request, 'Promjene su spremljene.')
        return True

    if action_name == 'delete_registry_book' and page_slug == 'maticne-knjige':
        messages.error(
            request,
            'Matična knjiga se ne briše. Promijenite status i evidentirajte '
            'lokaciju, skrbnika te razlog promjene.',
        )
        return True

    return False
