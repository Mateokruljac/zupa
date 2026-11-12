"""Presentation context for browsing parish registry books and their records."""

from __future__ import annotations

from isprave.forms import (
    BaptismRegistryForm,
    FuneralRegistryForm,
    MarriageRegistryForm,
    baptism_registry_initial,
    funeral_registry_initial,
    marriage_registry_initial,
)


REGISTRY_TYPE_PRESENTATION = {
    'krštenja': {
        'label': 'Matica rođenih i krštenih',
        'icon': '✦',
        'person_label': 'Krštenik',
        'related_people_label': 'Roditelji',
    },
    'vjenčanja': {
        'label': 'Matica vjenčanih',
        'icon': '♥',
        'person_label': 'Mladenci',
        'related_people_label': 'Svjedoci',
    },
    'umrli': {
        'label': 'Matica umrlih',
        'icon': '✝',
        'person_label': 'Pokojnik',
        'related_people_label': 'Groblje',
    },
    'ostalo': {
        'label': 'Ostala matična knjiga',
        'icon': '▤',
        'person_label': 'Zapis',
        'related_people_label': 'Napomena',
    },
}


def _year_from_date(date_value: str) -> int | None:
    try:
        return int(str(date_value)[:4])
    except (TypeError, ValueError):
        return None


def _detail(label: str, value, *, is_date: bool = False) -> dict:
    return {'label': label, 'value': value or '—', 'is_date': is_date}


def _edit_field(name: str, label: str, value, *, field_type: str = 'text') -> dict:
    return {
        'name': name,
        'label': label,
        'value': value or '',
        'type': field_type,
    }


def _baptism_records(parish_data: dict) -> list[dict]:
    records = []
    for baptism in parish_data.get('baptisms', []):
        baptism_date = baptism.get('baptismDate', '')
        baptism_year = _year_from_date(baptism_date)
        records.append({
            'id': baptism.get('id', ''),
            'year': baptism_year,
            'registry_number': baptism.get('registryNo', ''),
            'date': baptism_date,
            'person': baptism.get('childName', ''),
            'related_people': baptism.get('parents', ''),
            'status': baptism.get('status', ''),
            'edit_form': BaptismRegistryForm(
                initial=baptism_registry_initial(baptism),
                selected_year=baptism_year or 1900,
                auto_id=f"registry_{baptism.get('id', 'record')}_%s",
            ),
            'edit_fields': [
                _edit_field('subject_name', 'Krštenik', baptism.get('childName')),
                _edit_field('record_date', 'Datum krštenja', baptism_date, field_type='date'),
                _edit_field('birth_date', 'Datum rođenja', baptism.get('birthDate'), field_type='date'),
                _edit_field('related_people', 'Roditelji', baptism.get('parents')),
                _edit_field('sponsors', 'Kumovi', baptism.get('godparents')),
                _edit_field('celebrant', 'Slavitelj', baptism.get('celebrant')),
                _edit_field('status', 'Status', baptism.get('status')),
            ],
            'details': [
                _detail('Ime djeteta', baptism.get('childFirstName')),
                _detail('Prezime djeteta', baptism.get('childLastName')),
                _detail(
                    'Sin ili kći',
                    {'son': 'Sin', 'daughter': 'Kći'}.get(baptism.get('childSex')),
                ),
                _detail('Datum rođenja', baptism.get('birthDate'), is_date=True),
                _detail('Datum krštenja', baptism_date, is_date=True),
                _detail('Mjesto krštenja', baptism.get('baptismPlace')),
                _detail('JMBG / OIB', baptism.get('identifierValue')),
                _detail('Otac', ' '.join(filter(None, (baptism.get('fatherFirstName'), baptism.get('fatherLastName'))))),
                _detail('Vjera oca', baptism.get('fatherReligion')),
                _detail('Majka', ' '.join(filter(None, (baptism.get('motherFirstName'), baptism.get('motherLastName'))))),
                _detail('Vjera majke', baptism.get('motherReligion')),
                _detail('Roditelji kanonski vjenčani', 'Da' if baptism.get('parentsCanonicallyMarried', True) else 'Ne'),
                _detail('Adresa prebivališta', baptism.get('residenceAddress')),
                _detail('Kum / kuma', baptism.get('godparents')),
                _detail('Krstitelj', baptism.get('celebrant')),
                _detail('Služba krstitelja', baptism.get('ministerRole')),
                _detail('Datum potvrde', baptism.get('confirmationDate'), is_date=True),
                _detail('Mjesto potvrde', baptism.get('confirmationPlace')),
                _detail('Župa potvrde', baptism.get('confirmationParish')),
                _detail('Datum ženidbe', baptism.get('marriageDate'), is_date=True),
                _detail('Župa ženidbe', baptism.get('marriageParish')),
                _detail('Supružnik', ' '.join(filter(None, (baptism.get('spouseFirstName'), baptism.get('spouseLastName'))))),
                _detail('Naknadni upisi i bilješke', baptism.get('notes')),
                _detail('Stranica u fizičkoj matici', baptism.get('physicalPage')),
                _detail('Matični broj', baptism.get('registryNo')),
                _detail('Status', baptism.get('status')),
            ],
        })
    return records


def _wedding_records(parish_data: dict) -> list[dict]:
    records = []
    for wedding in parish_data.get('weddings', []):
        wedding_date = wedding.get('weddingDate', '')
        records.append({
            'id': wedding.get('id', ''),
            'year': _year_from_date(wedding_date),
            'registry_number': wedding.get('registryNo', ''),
            'date': wedding_date,
            'person': wedding.get('couple', ''),
            'related_people': wedding.get('witnesses', ''),
            'status': wedding.get('status', ''),
            'edit_form': MarriageRegistryForm(
                initial=marriage_registry_initial(wedding),
                selected_year=_year_from_date(wedding_date) or 1900,
                auto_id=f"marriage_{wedding.get('id', 'record')}_%s",
            ),
            'edit_fields': [
                _edit_field('subject_name', 'Mladenci', wedding.get('couple')),
                _edit_field('record_date', 'Datum vjenčanja', wedding_date, field_type='date'),
                _edit_field('place', 'Crkva', wedding.get('church')),
                _edit_field('related_people', 'Svjedoci', wedding.get('witnesses')),
                _edit_field('celebrant', 'Slavitelj', wedding.get('celebrant')),
                _edit_field('status', 'Status', wedding.get('status')),
            ],
            'details': [
                _detail('Zaručnik', wedding.get('groomName')),
                _detail('Zaručnica', wedding.get('brideName')),
                _detail('Datum vjenčanja', wedding_date, is_date=True),
                _detail('Mjesto vjenčanja', wedding.get('marriagePlace') or wedding.get('church')),
                _detail('Svjedok zaručnika', wedding.get('groomSponsor')),
                _detail('Svjedok zaručnice', wedding.get('brideSponsor')),
                _detail('Vjenčatelj', wedding.get('celebrant')),
                _detail('Služba vjenčatelja', wedding.get('officiantRole')),
                _detail('Napomene', wedding.get('notes')),
                _detail('Stranica u fizičkoj knjizi', wedding.get('physicalPage')),
                _detail('Matični broj', wedding.get('registryNo')),
                _detail('Status', wedding.get('status')),
            ],
        })
    return records


def _funeral_records(parish_data: dict) -> list[dict]:
    records = []
    for funeral in parish_data.get('funerals', []):
        funeral_date = funeral.get('funeralDate', '')
        death_date = funeral.get('deathDate', '')
        record_year = _year_from_date(death_date) or _year_from_date(funeral_date)
        records.append({
            'id': funeral.get('id', ''),
            'year': record_year,
            'registry_number': funeral.get('registryNo', ''),
            'date': funeral_date,
            'person': funeral.get('deceased', ''),
            'related_people': funeral.get('cemetery', ''),
            'status': funeral.get('status', ''),
            'edit_form': FuneralRegistryForm(
                initial=funeral_registry_initial(funeral),
                selected_year=record_year or 1900,
                auto_id=f"funeral_{funeral.get('id', 'record')}_%s",
            ),
            'edit_fields': [
                _edit_field('subject_name', 'Pokojnik', funeral.get('deceased')),
                _edit_field('record_date', 'Datum sprovoda', funeral_date, field_type='date'),
                _edit_field('birth_date', 'Datum smrti', funeral.get('deathDate'), field_type='date'),
                _edit_field('place', 'Groblje', funeral.get('cemetery')),
                _edit_field('celebrant', 'Slavitelj', funeral.get('celebrant')),
                _edit_field('status', 'Status', funeral.get('status')),
            ],
            'details': [
                _detail('Ime', funeral.get('firstName')),
                _detail('Prezime', funeral.get('lastName')),
                _detail('Spol', {'male': 'Muško', 'female': 'Žensko'}.get(funeral.get('sex'))),
                _detail('Datum smrti', death_date, is_date=True),
                _detail('Mjesto smrti', funeral.get('deathPlace')),
                _detail('Datum rođenja', funeral.get('birthDate'), is_date=True),
                _detail('Mjesto rođenja', funeral.get('birthPlace')),
                _detail('JMBG / OIB', funeral.get('identifierValue')),
                _detail('Adresa', funeral.get('residenceAddress')),
                _detail('Supružnik', ' '.join(filter(None, (funeral.get('spouseFirstName'), funeral.get('spouseLastName'))))),
                _detail('Otac', ' '.join(filter(None, (funeral.get('fatherFirstName'), funeral.get('fatherLastName'))))),
                _detail('Majka', ' '.join(filter(None, (funeral.get('motherFirstName'), funeral.get('motherLastName'))))),
                _detail('Ispovijed', 'Da' if funeral.get('receivedConfession') else 'Ne'),
                _detail('Bolesničko pomazanje', 'Da' if funeral.get('receivedAnointing') else 'Ne'),
                _detail('Pričest', 'Da' if funeral.get('receivedCommunion') else 'Ne'),
                _detail('Mjesto pokopa', funeral.get('burialPlace') or funeral.get('cemetery')),
                _detail('Datum pokopa', funeral.get('burialDate') or funeral_date, is_date=True),
                _detail('Crkveni službenik', funeral.get('celebrant')),
                _detail('Uzrok smrti', funeral.get('causeOfDeath')),
                _detail('Bilješke', funeral.get('notes')),
                _detail('Stranica u fizičkoj knjizi', funeral.get('physicalPage')),
                _detail('Matični broj', funeral.get('registryNo')),
                _detail('Status', funeral.get('status')),
            ],
        })
    return records


def _generic_registry_records(
    parish_data: dict,
    registry_book_id: str,
) -> list[dict]:
    records = []
    for registry_entry in parish_data.get('registryEntries', []):
        if registry_entry.get('bookId') != registry_book_id:
            continue
        record_date = registry_entry.get('recordDate', '')
        records.append({
            'id': registry_entry.get('id', ''),
            'year': _year_from_date(record_date) or registry_entry.get('year'),
            'registry_number': registry_entry.get('registryNo', ''),
            'date': record_date,
            'person': registry_entry.get('subjectName', ''),
            'related_people': registry_entry.get('place', ''),
            'status': registry_entry.get('status', ''),
            'edit_fields': [
                _edit_field('subject_name', 'Naziv zapisa / osoba', registry_entry.get('subjectName')),
                _edit_field('record_date', 'Datum zapisa', record_date, field_type='date'),
                _edit_field('place', 'Mjesto / napomena', registry_entry.get('place')),
                _edit_field('celebrant', 'Odgovorna osoba', registry_entry.get('celebrant')),
                _edit_field('status', 'Status', registry_entry.get('status')),
            ],
            'details': [
                _detail('Naziv zapisa / osoba', registry_entry.get('subjectName')),
                _detail('Datum zapisa', record_date, is_date=True),
                _detail('Mjesto / napomena', registry_entry.get('place')),
                _detail('Slavitelj / odgovorna osoba', registry_entry.get('celebrant')),
                _detail('Matični broj', registry_entry.get('registryNo')),
                _detail('Status', registry_entry.get('status')),
            ],
        })
    return records


def _records_for_type(
    parish_data: dict,
    registry_type: str,
    registry_book_id: str = '',
) -> list[dict]:
    record_builders = {
        'krštenja': _baptism_records,
        'vjenčanja': _wedding_records,
        'umrli': _funeral_records,
    }
    record_builder = record_builders.get(registry_type)
    if record_builder:
        return record_builder(parish_data)
    return _generic_registry_records(parish_data, registry_book_id)


def registry_books_page_context(parish_data: dict, request) -> dict:
    registry_books = [
        registry_book
        for registry_book in parish_data.get('registryBooks', [])
        if registry_book.get('type', 'ostalo') in REGISTRY_TYPE_PRESENTATION
    ]
    selected_registry_book_id = request.GET.get('registry', '')
    selected_registry_book = next(
        (
            registry_book
            for registry_book in registry_books
            if registry_book.get('id') == selected_registry_book_id
        ),
        None,
    )

    book_cards = []
    for registry_book in registry_books:
        registry_type = registry_book.get('type', 'ostalo')
        presentation = REGISTRY_TYPE_PRESENTATION.get(
            registry_type,
            REGISTRY_TYPE_PRESENTATION['ostalo'],
        )
        type_records = _records_for_type(
            parish_data,
            registry_type,
            registry_book.get('id', ''),
        )
        record_years = {
            record.get('year')
            for record in type_records
            if record.get('year')
        }
        record_years.update(
            int(configured_year)
            for configured_year in registry_book.get('years', [])
            if str(configured_year).isdigit()
        )
        last_entry_year = _year_from_date(registry_book.get('lastEntry', ''))
        if last_entry_year:
            record_years.add(last_entry_year)
        book_cards.append(
            {
                **registry_book,
                'type_label': presentation['label'],
                'icon': presentation['icon'],
                'record_count': len(type_records),
                'year_count': len(record_years),
            }
        )

    context = {
        'registry_books': registry_books,
        'registry_book_cards': book_cards,
        'selected_registry_book_view': selected_registry_book,
    }
    if not selected_registry_book:
        return context

    selected_registry_type = selected_registry_book.get('type', 'ostalo')
    selected_presentation = REGISTRY_TYPE_PRESENTATION.get(
        selected_registry_type,
        REGISTRY_TYPE_PRESENTATION['ostalo'],
    )
    registry_records = _records_for_type(
        parish_data,
        selected_registry_type,
        selected_registry_book.get('id', ''),
    )
    year_counts = {}
    for registry_record in registry_records:
        record_year = registry_record.get('year')
        if record_year:
            year_counts[record_year] = year_counts.get(record_year, 0) + 1

    for configured_year in selected_registry_book.get('years', []):
        if str(configured_year).isdigit():
            year_counts.setdefault(int(configured_year), 0)

    last_entry_year = _year_from_date(selected_registry_book.get('lastEntry', ''))
    if last_entry_year and last_entry_year not in year_counts:
        year_counts[last_entry_year] = 0

    available_years = [
        {'year': registry_year, 'record_count': year_counts[registry_year]}
        for registry_year in sorted(year_counts, reverse=True)
    ]
    requested_year = request.GET.get('year', '')
    try:
        selected_year = int(requested_year) if requested_year else None
    except ValueError:
        selected_year = None

    context.update(
        {
            'registry_type_presentation': selected_presentation,
            'registry_years': available_years,
            'selected_registry_year': selected_year,
            'registry_records': [
                record
                for record in registry_records
                if record.get('year') == selected_year
            ],
        }
    )
    return context
