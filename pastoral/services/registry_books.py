"""Presentation context for browsing parish registry books and their records."""

from __future__ import annotations


REGISTRY_TYPE_PRESENTATION = {
    'krštenja': {
        'label': 'Matica krštenih',
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
    'krizma': {
        'label': 'Matica krizmanih',
        'icon': '◆',
        'person_label': 'Krizmanik',
        'related_people_label': 'Kum/ka',
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
        records.append({
            'id': baptism.get('id', ''),
            'year': _year_from_date(baptism_date),
            'registry_number': baptism.get('registryNo', ''),
            'date': baptism_date,
            'person': baptism.get('childName', ''),
            'related_people': baptism.get('parents', ''),
            'status': baptism.get('status', ''),
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
                _detail('Krštenik', baptism.get('childName')),
                _detail('Datum rođenja', baptism.get('birthDate'), is_date=True),
                _detail('Datum krštenja', baptism_date, is_date=True),
                _detail('Roditelji', baptism.get('parents')),
                _detail('Kumovi', baptism.get('godparents')),
                _detail('Slavitelj', baptism.get('celebrant')),
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
            'edit_fields': [
                _edit_field('subject_name', 'Mladenci', wedding.get('couple')),
                _edit_field('record_date', 'Datum vjenčanja', wedding_date, field_type='date'),
                _edit_field('place', 'Crkva', wedding.get('church')),
                _edit_field('related_people', 'Svjedoci', wedding.get('witnesses')),
                _edit_field('celebrant', 'Slavitelj', wedding.get('celebrant')),
                _edit_field('status', 'Status', wedding.get('status')),
            ],
            'details': [
                _detail('Mladenci', wedding.get('couple')),
                _detail('Datum vjenčanja', wedding_date, is_date=True),
                _detail('Crkva', wedding.get('church')),
                _detail('Svjedoci', wedding.get('witnesses')),
                _detail('Slavitelj', wedding.get('celebrant')),
                _detail('Matični broj', wedding.get('registryNo')),
                _detail('Status', wedding.get('status')),
            ],
        })
    return records


def _funeral_records(parish_data: dict) -> list[dict]:
    records = []
    for funeral in parish_data.get('funerals', []):
        funeral_date = funeral.get('funeralDate', '')
        records.append({
            'id': funeral.get('id', ''),
            'year': _year_from_date(funeral_date),
            'registry_number': funeral.get('registryNo', ''),
            'date': funeral_date,
            'person': funeral.get('deceased', ''),
            'related_people': funeral.get('cemetery', ''),
            'status': funeral.get('status', ''),
            'edit_fields': [
                _edit_field('subject_name', 'Pokojnik', funeral.get('deceased')),
                _edit_field('record_date', 'Datum sprovoda', funeral_date, field_type='date'),
                _edit_field('birth_date', 'Datum smrti', funeral.get('deathDate'), field_type='date'),
                _edit_field('place', 'Groblje', funeral.get('cemetery')),
                _edit_field('celebrant', 'Slavitelj', funeral.get('celebrant')),
                _edit_field('status', 'Status', funeral.get('status')),
            ],
            'details': [
                _detail('Pokojnik', funeral.get('deceased')),
                _detail('Datum smrti', funeral.get('deathDate'), is_date=True),
                _detail('Datum sprovoda', funeral_date, is_date=True),
                _detail('Groblje', funeral.get('cemetery')),
                _detail('Slavitelj', funeral.get('celebrant')),
                _detail('Matični broj', funeral.get('registryNo')),
                _detail('Status', funeral.get('status')),
            ],
        })
    return records


def _confirmation_records(parish_data: dict) -> list[dict]:
    records = []
    for confirmation_group in parish_data.get('confirmations', []):
        ceremony_date = confirmation_group.get('ceremonyDate', '')
        confirmation_year = (
            _year_from_date(ceremony_date) or confirmation_group.get('year')
        )
        for candidate in confirmation_group.get('candidates', []):
            records.append({
                'id': candidate.get('id', ''),
                'year': confirmation_year,
                'registry_number': candidate.get('registryNo', ''),
                'date': ceremony_date,
                'person': candidate.get('name', ''),
                'related_people': candidate.get('sponsor', ''),
                'status': candidate.get('status', ''),
                'edit_fields': [
                    _edit_field('subject_name', 'Krizmanik', candidate.get('name')),
                    _edit_field('record_date', 'Datum krizme', ceremony_date, field_type='date'),
                    _edit_field('birth_date', 'Datum rođenja', candidate.get('birthDate'), field_type='date'),
                    _edit_field('baptism_date', 'Datum krštenja', candidate.get('baptized'), field_type='date'),
                    _edit_field('sponsors', 'Kum/ka', candidate.get('sponsor')),
                    _edit_field('celebrant', 'Biskup / slavitelj', confirmation_group.get('bishop')),
                    _edit_field('status', 'Status', candidate.get('status')),
                ],
                'details': [
                    _detail('Krizmanik', candidate.get('name')),
                    _detail('Datum rođenja', candidate.get('birthDate'), is_date=True),
                    _detail('Datum krizme', ceremony_date, is_date=True),
                    _detail('Datum krštenja', candidate.get('baptized'), is_date=True),
                    _detail('Kum/ka', candidate.get('sponsor')),
                    _detail('Skupina', candidate.get('group')),
                    _detail('Biskup / slavitelj', confirmation_group.get('bishop')),
                    _detail('Matični broj', candidate.get('registryNo')),
                    _detail('Status', candidate.get('status')),
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
        'krizma': _confirmation_records,
    }
    record_builder = record_builders.get(registry_type)
    if record_builder:
        return record_builder(parish_data)
    return _generic_registry_records(parish_data, registry_book_id)


def registry_books_page_context(parish_data: dict, request) -> dict:
    registry_books = parish_data.get('registryBooks', [])
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
