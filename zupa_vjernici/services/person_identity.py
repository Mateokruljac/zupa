"""Pronalaženje i kreiranje Person zapisa iz slobodnog teksta kartona."""
from __future__ import annotations

from datetime import date

from zupa_vjernici.models import Person, normalize_person_search_text

FEMALE_RELATIONS = frozenset({
    'majka', 'žena', 'zena', 'kći', 'kci', 'kcer', 'wife', 'mother', 'daughter',
})
MALE_RELATIONS = frozenset({
    'otac', 'muž', 'muz', 'sin', 'husband', 'father', 'son',
})


def split_person_name(full_name: str, fallback_surname: str = '') -> tuple[str, str]:
    """Rastavlja 'Ime Prezime' na given_names i surname."""
    parts = [part for part in str(full_name or '').split() if part]
    if not parts:
        return '', (fallback_surname or '').strip()
    if len(parts) == 1:
        return parts[0], (fallback_surname or '').strip()
    return ' '.join(parts[:-1]), parts[-1]


def sex_from_relation(relation: str) -> str:
    normalized = str(relation or '').strip().casefold()
    if normalized in FEMALE_RELATIONS:
        return Person.Sex.FEMALE
    if normalized in MALE_RELATIONS:
        return Person.Sex.MALE
    return Person.Sex.UNKNOWN


def birth_year_as_text(value) -> str:
    if value in (None, ''):
        return ''
    return str(value).strip()[:20]


def find_or_create_person(
    parish,
    *,
    full_name: str,
    fallback_surname: str = '',
    relation: str = '',
    birth_year: str = '',
    place_of_birth: str = '',
) -> Person | None:
    """Vraća Person u župi; stvara novu ako ime postoji a poklapanja nema."""
    given_names, surname = split_person_name(full_name, fallback_surname)
    if not given_names and not surname:
        return None
    if not given_names:
        given_names = surname
    if not surname:
        surname = fallback_surname or given_names

    normalized_given = normalize_person_search_text(given_names)
    normalized_surname = normalize_person_search_text(surname)
    queryset = Person.objects.filter(
        parish=parish,
        status=Person.Status.ACTIVE,
        normalized_given_names=normalized_given,
        normalized_surname=normalized_surname,
    )
    year_text = birth_year_as_text(birth_year)
    if year_text.isdigit():
        year_value = int(year_text)
        year_match = queryset.filter(date_of_birth__year=year_value).first()
        if year_match:
            person = year_match
        else:
            person = queryset.filter(date_of_birth__isnull=True).first() or queryset.first()
    else:
        person = queryset.first()

    if person is None:
        person = Person(
            parish=parish,
            given_names=given_names[:160],
            surname=surname[:160],
            sex=sex_from_relation(relation),
            place_of_birth=str(place_of_birth or '')[:180],
        )
        if year_text.isdigit():
            year_value = int(year_text)
            if 1800 <= year_value <= 2200:
                person.date_of_birth = date(year_value, 1, 1)
        person.save()
        return person

    updates = []
    inferred_sex = sex_from_relation(relation)
    if person.sex == Person.Sex.UNKNOWN and inferred_sex != Person.Sex.UNKNOWN:
        person.sex = inferred_sex
        updates.append('sex')
    if place_of_birth and not person.place_of_birth:
        person.place_of_birth = str(place_of_birth)[:180]
        updates.append('place_of_birth')
    if year_text.isdigit() and person.date_of_birth is None:
        year_value = int(year_text)
        if 1800 <= year_value <= 2200:
            person.date_of_birth = date(year_value, 1, 1)
            updates.append('date_of_birth')
    if updates:
        person.save(update_fields=updates)
    return person
