"""POST akcije za matične knjige."""
from __future__ import annotations

from typing import TYPE_CHECKING
import uuid

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction

from isprave.forms import BaptismRegistryForm, FuneralRegistryForm, MarriageRegistryForm, RegistryBookForm, RegistryRecordForm
from django_multitenant.schema import with_tenant_schema
from sakramenti.services.baptism_records import synchronize_baptism_record
from isprave.services.registry_entry_records import synchronize_registry_entry
from sakramenti.services.sacrament_mutations import (
    add_sacrament_record,
    update_sacrament_record,
)

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


def _baptism_registry_payload(cleaned_data: dict) -> dict:
    def iso_date(field_name):
        value = cleaned_data.get(field_name)
        return value.isoformat() if value else ''

    def full_name(first_name_field, last_name_field):
        return ' '.join(filter(None, (
            cleaned_data.get(first_name_field), cleaned_data.get(last_name_field)
        )))

    baptism_date = cleaned_data.get('baptism_date')
    entry_number = cleaned_data.get('entry_number')
    return {
        'entryNumber': cleaned_data.get('entry_number'),
        'registryNo': (
            f'{baptism_date.year}/{entry_number}'
            if baptism_date and entry_number else ''
        ),
        'birthDate': iso_date('birth_date'),
        'baptismDate': iso_date('baptism_date'),
        'childFirstName': cleaned_data['child_first_name'],
        'childLastName': cleaned_data['child_last_name'],
        'childName': full_name('child_first_name', 'child_last_name'),
        'childSex': cleaned_data['child_sex'],
        'baptismPlace': cleaned_data['baptism_place'],
        'identifierType': cleaned_data.get('identifier_type') or '',
        'identifierValue': cleaned_data.get('identifier_value') or '',
        'fatherFirstName': cleaned_data['father_first_name'],
        'fatherLastName': cleaned_data['father_last_name'],
        'fatherReligion': cleaned_data['father_religion'],
        'motherFirstName': cleaned_data['mother_first_name'],
        'motherLastName': cleaned_data['mother_last_name'],
        'motherReligion': cleaned_data['mother_religion'],
        'parentsCanonicallyMarried': cleaned_data['parents_canonically_married'],
        'parents': ' / '.join((
            full_name('father_first_name', 'father_last_name'),
            full_name('mother_first_name', 'mother_last_name'),
        )),
        'residenceAddress': cleaned_data['residence_address'],
        'godparentFirstName': cleaned_data['godparent_first_name'],
        'godparentLastName': cleaned_data['godparent_last_name'],
        'godparents': full_name('godparent_first_name', 'godparent_last_name'),
        'ministerFirstName': cleaned_data['minister_first_name'],
        'ministerLastName': cleaned_data['minister_last_name'],
        'ministerRole': cleaned_data['minister_role'],
        'celebrant': full_name('minister_first_name', 'minister_last_name'),
        'confirmationDate': iso_date('confirmation_date'),
        'confirmationPlace': cleaned_data.get('confirmation_place') or '',
        'confirmationParish': cleaned_data.get('confirmation_parish') or '',
        'marriageDate': iso_date('marriage_date'),
        'marriageParish': cleaned_data.get('marriage_parish') or '',
        'spouseFirstName': cleaned_data.get('spouse_first_name') or '',
        'spouseLastName': cleaned_data.get('spouse_last_name') or '',
        'notes': cleaned_data.get('notes') or '',
        'physicalPage': cleaned_data.get('physical_page') or '',
    }


def _funeral_registry_payload(cleaned_data: dict) -> dict:
    def iso_date(name):
        value = cleaned_data.get(name)
        return value.isoformat() if value else ''
    def full_name(first, last):
        return ' '.join(filter(None, (cleaned_data.get(first), cleaned_data.get(last))))
    death_date, entry_number = cleaned_data.get('death_date'), cleaned_data.get('entry_number')
    return {
        'entryNumber': entry_number,
        'registryNo': f'{death_date.year}/{entry_number}' if death_date and entry_number else '',
        'physicalPage': cleaned_data.get('physical_page') or '',
        'deathDate': iso_date('death_date'), 'deathPlace': cleaned_data['death_place'],
        'firstName': cleaned_data['first_name'], 'lastName': cleaned_data['last_name'],
        'deceased': full_name('first_name', 'last_name'), 'sex': cleaned_data['sex'],
        'birthPlace': cleaned_data['birth_place'], 'birthDate': iso_date('birth_date'),
        'identifierType': cleaned_data.get('identifier_type') or '', 'identifierValue': cleaned_data.get('identifier_value') or '',
        'spouseFirstName': cleaned_data.get('spouse_first_name') or '', 'spouseLastName': cleaned_data.get('spouse_last_name') or '',
        'fatherFirstName': cleaned_data['father_first_name'], 'fatherLastName': cleaned_data['father_last_name'],
        'motherFirstName': cleaned_data['mother_first_name'], 'motherLastName': cleaned_data['mother_last_name'],
        'residenceAddress': cleaned_data['residence_address'],
        'receivedConfession': cleaned_data.get('received_confession', False),
        'receivedAnointing': cleaned_data.get('received_anointing', False),
        'receivedCommunion': cleaned_data.get('received_communion', False),
        'burialPlace': cleaned_data['burial_place'], 'cemetery': cleaned_data['burial_place'],
        'burialDate': iso_date('burial_date'), 'funeralDate': iso_date('burial_date'),
        'ministerFirstName': cleaned_data['minister_first_name'], 'ministerLastName': cleaned_data['minister_last_name'],
        'celebrant': full_name('minister_first_name', 'minister_last_name'),
        'causeOfDeath': cleaned_data.get('cause_of_death') or '', 'notes': cleaned_data.get('notes') or '',
    }


def _marriage_registry_payload(cleaned_data: dict) -> dict:
    def camel(name):
        first, *rest = name.split('_')
        return first + ''.join(part.title() for part in rest)
    def iso_date(name):
        value = cleaned_data.get(name)
        return value.isoformat() if value else ''
    date_fields = {
        'marriage_date', 'groom_birth_date', 'groom_baptism_date',
        'bride_birth_date', 'bride_baptism_date',
    }
    payload = {
        camel(name): (iso_date(name) if name in date_fields else cleaned_data.get(name) or '')
        for name in MarriageRegistryForm.base_fields
    }
    payload.update({
        'weddingDate': payload.pop('marriageDate'),
        'church': payload['marriagePlace'],
        'groomName': ' '.join(filter(None, (cleaned_data['groom_first_name'], cleaned_data['groom_last_name']))),
        'brideName': ' '.join(filter(None, (cleaned_data['bride_first_name'], cleaned_data['bride_last_name']))),
        'couple': ' & '.join((
            ' '.join((cleaned_data['groom_first_name'], cleaned_data['groom_last_name'])),
            ' '.join((cleaned_data['bride_first_name'], cleaned_data['bride_last_name'])),
        )),
        'groomSponsor': ' '.join((cleaned_data['groom_witness_first_name'], cleaned_data['groom_witness_last_name'])),
        'brideSponsor': ' '.join((cleaned_data['bride_witness_first_name'], cleaned_data['bride_witness_last_name'])),
        'celebrant': ' '.join((cleaned_data['officiant_first_name'], cleaned_data['officiant_last_name'])),
    })
    return payload


@with_tenant_schema
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
        if registry_type == 'krštenja':
            registry_record_form = BaptismRegistryForm(
                request.POST, selected_year=registry_year
            )
        elif registry_type == 'vjenčanja':
            registry_record_form = MarriageRegistryForm(request.POST, selected_year=registry_year)
        elif registry_type == 'umrli':
            registry_record_form = FuneralRegistryForm(request.POST, selected_year=registry_year)
        else:
            registry_record_form = RegistryRecordForm(
                request.POST,
                registry_type=registry_type,
                selected_year=registry_year,
            )
        if not registry_record_form.is_valid():
            messages.error(request, 'Provjerite obvezna polja novog zapisa.')
            return True

        cleaned_data = registry_record_form.cleaned_data
        record_date = (
            cleaned_data['baptism_date']
            if registry_type == 'krštenja'
            else cleaned_data['marriage_date']
            if registry_type == 'vjenčanja'
            else cleaned_data['death_date']
            if registry_type == 'umrli'
            else cleaned_data['record_date']
        )
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
        } if registry_type != 'krštenja' else {}
        baptism_record = None
        registry_source_record = None
        if registry_type == 'krštenja':
            baptism_record = add_sacrament_record(parish_data, 'baptisms', {
                **_baptism_registry_payload(cleaned_data),
                'status': 'upisano',
                'stipend': 0,
                'stipendPaid': False,
            })
        elif registry_type == 'vjenčanja':
            registry_source_record = add_sacrament_record(parish_data, 'weddings', {
                **_marriage_registry_payload(cleaned_data),
                'status': 'upisano',
                'stipend': 0,
                'stipendPaid': False,
            })
        elif registry_type == 'umrli':
            registry_source_record = add_sacrament_record(parish_data, 'funerals', {
                **_funeral_registry_payload(cleaned_data),
                'status': 'upisano',
                'stipend': 0,
                'stipendPaid': False,
            })
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
                    baptism_event = synchronize_baptism_record(
                        parish_data_service.parish,
                        baptism_record,
                        actor=request.user,
                    )
                    register_entry = getattr(baptism_event, 'register_entry', None)
                    if register_entry:
                        baptism_record['entryNumber'] = register_entry.entry_number
                        baptism_record['registryNo'] = register_entry.entry_reference
                        parish_data_service.save(parish_data)
                elif registry_source_record and registry_type in {
                    'vjenčanja', 'umrli',
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
        if registry_type == 'krštenja':
            registry_record_form = BaptismRegistryForm(
                request.POST, selected_year=registry_year
            )
        elif registry_type == 'vjenčanja':
            registry_record_form = MarriageRegistryForm(request.POST, selected_year=registry_year)
        elif registry_type == 'umrli':
            registry_record_form = FuneralRegistryForm(request.POST, selected_year=registry_year)
        else:
            registry_record_form = RegistryRecordForm(
                request.POST,
                registry_type=registry_type,
                selected_year=registry_year,
            )
        if not registry_record_form.is_valid():
            messages.error(request, 'Provjerite unesene podatke zapisa.')
            return True
        cleaned_data = registry_record_form.cleaned_data
        record_date = (
            cleaned_data['baptism_date']
            if registry_type == 'krštenja'
            else cleaned_data['marriage_date']
            if registry_type == 'vjenčanja'
            else cleaned_data['death_date']
            if registry_type == 'umrli'
            else cleaned_data['record_date']
        )
        if record_date.year != registry_year:
            messages.error(
                request, f'Datum zapisa mora pripadati {registry_year}. godini.'
            )
            return True

        record_date_value = record_date.isoformat()
        shared_values = {
            'celebrant': cleaned_data.get('celebrant') or '',
            'status': cleaned_data.get('status') or 'upisano',
        } if registry_type != 'krštenja' else {}
        updated = False
        if registry_type == 'krštenja':
            updated = update_sacrament_record(
                parish_data, 'baptisms', source_identifier,
                _baptism_registry_payload(cleaned_data),
            )
        elif registry_type == 'vjenčanja':
            updated = update_sacrament_record(
                parish_data, 'weddings', source_identifier,
                _marriage_registry_payload(cleaned_data),
            )
        elif registry_type == 'umrli':
            updated = update_sacrament_record(
                parish_data, 'funerals', source_identifier,
                _funeral_registry_payload(cleaned_data),
            )
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
                if registry_type == 'krštenja':
                    baptism_record = next(
                        record for record in parish_data.get('baptisms', [])
                        if record.get('id') == source_identifier
                    )
                    synchronize_baptism_record(
                        parish_data_service.parish,
                        baptism_record,
                        actor=request.user,
                    )
                elif registry_type in {'vjenčanja', 'umrli'}:
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
