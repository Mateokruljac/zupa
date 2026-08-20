"""Read-only analysis of legacy person and church-record JSON collections."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from django.utils.dateparse import parse_date

from pastoral.models import Parish, normalize_person_search_text


EXPECTED_OPERATIONAL_STATUSES = {
    'baptisms': {
        'planirano', 'priprema', 'upis', 'upisano', 'obavljeno',
    },
    'first_communion_candidates': {
        'priprema', 'prijavljen', 'pričešćen', 'upisano',
    },
    'confirmation_candidates': {
        'priprema', 'pristupnica', 'potvrđen', 'upisano',
    },
    'weddings': {
        'planirano', 'dogovoreno', 'priprema', 'obavljeno', 'upisano',
    },
    'funerals': {
        'planirano', 'dogovoreno', 'obavljeno', 'upisano',
    },
}


@dataclass(frozen=True)
class LegacyRecordCollection:
    name: str
    records: list[dict]
    date_fields: tuple[str, ...]


def _flatten_group_candidates(
    groups: list[dict],
) -> list[dict]:
    candidates = []
    for group in groups:
        for original_candidate in group.get('candidates') or []:
            candidate = dict(original_candidate)
            candidate['_group_year'] = group.get('year')
            candidates.append(candidate)
    return candidates


def _legacy_collections(parish_data: dict) -> tuple[LegacyRecordCollection, ...]:
    return (
        LegacyRecordCollection(
            name='families',
            records=list(parish_data.get('families') or []),
            date_fields=('lastVisit',),
        ),
        LegacyRecordCollection(
            name='baptisms',
            records=list(parish_data.get('baptisms') or []),
            date_fields=('birthDate', 'baptismDate'),
        ),
        LegacyRecordCollection(
            name='first_communion_candidates',
            records=_flatten_group_candidates(
                list(parish_data.get('firstCommunion') or []),
            ),
            date_fields=('birthDate', 'baptismDate'),
        ),
        LegacyRecordCollection(
            name='confirmation_candidates',
            records=_flatten_group_candidates(
                list(parish_data.get('confirmations') or []),
            ),
            date_fields=('birthDate', 'baptized'),
        ),
        LegacyRecordCollection(
            name='weddings',
            records=list(parish_data.get('weddings') or []),
            date_fields=('weddingDate',),
        ),
        LegacyRecordCollection(
            name='funerals',
            records=list(parish_data.get('funerals') or []),
            date_fields=('deathDate', 'funeralDate'),
        ),
    )


def _identifier_quality(records: list[dict]) -> dict:
    identifiers = [str(record.get('id') or '').strip() for record in records]
    populated_identifiers = [identifier for identifier in identifiers if identifier]
    identifier_counts = Counter(populated_identifiers)
    duplicate_record_count = sum(
        occurrence_count
        for occurrence_count in identifier_counts.values()
        if occurrence_count > 1
    )
    return {
        'missing_identifier_count': len(identifiers) - len(populated_identifiers),
        'duplicate_identifier_group_count': sum(
            1 for occurrence_count in identifier_counts.values()
            if occurrence_count > 1
        ),
        'duplicate_identifier_record_count': duplicate_record_count,
    }


def _date_quality(
    records: list[dict],
    date_fields: tuple[str, ...],
) -> dict:
    invalid_by_field = Counter()
    populated_by_field = Counter()
    for record in records:
        for field_name in date_fields:
            raw_value = record.get(field_name)
            if raw_value in (None, ''):
                continue
            populated_by_field[field_name] += 1
            if parse_date(str(raw_value)) is None:
                invalid_by_field[field_name] += 1
    return {
        'populated_date_count_by_field': dict(sorted(populated_by_field.items())),
        'invalid_date_count_by_field': dict(sorted(invalid_by_field.items())),
        'invalid_date_count': sum(invalid_by_field.values()),
    }


def _status_quality(collection_name: str, records: list[dict]) -> dict:
    status_counts = Counter(
        str(record.get('status') or '').strip()
        for record in records
        if str(record.get('status') or '').strip()
    )
    expected_statuses = EXPECTED_OPERATIONAL_STATUSES.get(collection_name)
    unrecognized_statuses = (
        sorted(set(status_counts) - expected_statuses)
        if expected_statuses is not None
        else []
    )
    return {
        'status_counts': dict(sorted(status_counts.items())),
        'missing_status_count': sum(
            1 for record in records if not str(record.get('status') or '').strip()
        ),
        'unrecognized_statuses': unrecognized_statuses,
        'unrecognized_status_record_count': sum(
            status_counts[status] for status in unrecognized_statuses
        ),
    }


def is_valid_croatian_personal_identifier(value: str) -> bool:
    normalized_value = ''.join(character for character in value if character.isdigit())
    if len(normalized_value) != 11:
        return False

    calculation_value = 10
    for character in normalized_value[:10]:
        calculation_value = (calculation_value + int(character)) % 10
        if calculation_value == 0:
            calculation_value = 10
        calculation_value = (calculation_value * 2) % 11
    control_digit = 11 - calculation_value
    if control_digit == 10:
        control_digit = 0
    return control_digit == int(normalized_value[-1])


def _personal_identifier_quality(collections: tuple[LegacyRecordCollection, ...]) -> dict:
    populated_count = 0
    invalid_count = 0
    identifier_fingerprints = Counter()

    for collection in collections:
        for record in collection.records:
            raw_identifier = str(record.get('oib') or '').strip()
            if not raw_identifier:
                continue
            populated_count += 1
            normalized_identifier = ''.join(
                character for character in raw_identifier if character.isdigit()
            )
            if not is_valid_croatian_personal_identifier(raw_identifier):
                invalid_count += 1
            if normalized_identifier:
                identifier_fingerprints[normalized_identifier] += 1

    return {
        'populated_count': populated_count,
        'invalid_count': invalid_count,
        'duplicate_group_count': sum(
            1 for count in identifier_fingerprints.values() if count > 1
        ),
        'duplicate_record_count': sum(
            count for count in identifier_fingerprints.values() if count > 1
        ),
    }


def _identity_candidates(
    parish_data: dict,
) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []

    for baptism in parish_data.get('baptisms') or []:
        candidates.append((
            str(baptism.get('childName') or ''),
            str(baptism.get('birthDate') or ''),
        ))

    for confirmation_group in parish_data.get('confirmations') or []:
        for candidate in confirmation_group.get('candidates') or []:
            candidates.append((
                str(candidate.get('name') or ''),
                str(candidate.get('birthDate') or ''),
            ))

    for communion_group in parish_data.get('firstCommunion') or []:
        for candidate in communion_group.get('candidates') or []:
            candidates.append((
                str(candidate.get('name') or ''),
                str(candidate.get('birthDate') or ''),
            ))

    for family in parish_data.get('families') or []:
        family_surname = str(family.get('surname') or '')
        for member in family.get('members') or []:
            member_name = str(member.get('name') or '')
            full_name = (
                member_name
                if family_surname.casefold() in member_name.casefold()
                else f'{member_name} {family_surname}'.strip()
            )
            birth_year = str(member.get('birthYear') or '')
            candidates.append((full_name, birth_year))

    return candidates


def _potential_duplicate_identity_quality(parish_data: dict) -> dict:
    identity_groups: dict[tuple[str, str], int] = defaultdict(int)
    incomplete_identity_count = 0
    for full_name, birth_value in _identity_candidates(parish_data):
        normalized_name = normalize_person_search_text(full_name)
        normalized_birth_value = birth_value.strip()
        if len(normalized_birth_value) >= 4 and normalized_birth_value[:4].isdigit():
            normalized_birth_value = normalized_birth_value[:4]
        if not normalized_name or not normalized_birth_value:
            incomplete_identity_count += 1
            continue
        identity_groups[(normalized_name, normalized_birth_value)] += 1

    duplicate_counts = [
        count for count in identity_groups.values() if count > 1
    ]
    return {
        'candidate_count': sum(identity_groups.values()),
        'incomplete_identity_count': incomplete_identity_count,
        'potential_duplicate_group_count': len(duplicate_counts),
        'potential_duplicate_record_count': sum(duplicate_counts),
        'requires_human_review': bool(duplicate_counts),
    }


def analyze_legacy_parish_records(parish: Parish) -> dict:
    parish_data = parish.data or {}
    collections = _legacy_collections(parish_data)
    collection_results = {}

    for collection in collections:
        collection_results[collection.name] = {
            'record_count': len(collection.records),
            **_identifier_quality(collection.records),
            **_date_quality(collection.records, collection.date_fields),
            **_status_quality(collection.name, collection.records),
        }

    return {
        'parish_slug': parish.slug,
        'tenant_id': str(parish.tenant_id),
        'read_only_analysis': True,
        'collections': collection_results,
        'personal_identifiers': _personal_identifier_quality(collections),
        'potential_duplicate_identities': (
            _potential_duplicate_identity_quality(parish_data)
        ),
    }
