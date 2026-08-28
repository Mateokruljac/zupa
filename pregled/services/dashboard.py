"""Podaci i provjerljive statistike za početnu stranicu župnog ureda."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from django.utils import timezone

from liturgija.services.liturgical import LiturgicalService
from liturgija.services.mass_schedule import schedule_entry_applies_on_date

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


INACTIVE_HOUSEHOLD_STATUSES = frozenset({
    'neaktivna',
    'neaktivno',
    'inactive',
    'iseljena',
    'odseljena',
    'arhivirana',
})

CHILD_MEMBER_RELATIONS = frozenset({
    'sin',
    'kći',
    'kci',
    'dijete',
    'djete',
    'child',
    'son',
    'daughter',
})


def _is_active_household(household: dict) -> bool:
    household_status = str(household.get('status') or '').strip().casefold()
    return household_status not in INACTIVE_HOUSEHOLD_STATUSES


def _household_created_in_year(household: dict, year: int) -> bool:
    created_at = str(household.get('createdAt') or '').strip()
    return created_at.startswith(f'{year}-')


def _has_unpaid_lukno_for_year(household: dict, year: int) -> bool:
    for annual_contribution in household.get('contributions') or []:
        if annual_contribution.get('year') == year and not annual_contribution.get(
            'luknoPaid'
        ):
            return True
    return False


def _normalize_member_relation(household_member: dict) -> str:
    return str(household_member.get('relation') or '').strip().casefold()


def _count_household_children(household_members: list[dict]) -> int:
    """Broji djecu prema upisanom odnosu, ne prema dobi."""
    return sum(
        1
        for household_member in household_members
        if _normalize_member_relation(household_member) in CHILD_MEMBER_RELATIONS
    )


def calculate_parish_population_statistics(
    parish_data: dict,
    *,
    reference_date: date | None = None,
) -> dict:
    """Izračunava samo metrike koje se mogu objasniti iz postojećih zapisa.

    Dok osobe još nisu zaseban relacijski model, ``persons`` znači broj zapisa
    članova kućanstava, a ``parishioners`` članove aktivnih kućanstava.
    Djeca u sastavu kućanstva broje se prema odnosu (sin, kći, dijete).
    Novododana kućanstva broje se samo kada postoji ``createdAt``.
    """
    statistics_date = reference_date or date.today()
    current_year = statistics_date.year
    previous_year = current_year - 1
    households = list(parish_data.get('families') or [])
    streets = list(parish_data.get('streets') or [])
    parish_directory = list(parish_data.get('parishDirectory') or [])

    persons = 0
    parishioners = 0
    active_households = 0
    single_person_households = 0
    households_without_children = 0
    households_with_one_child = 0
    households_with_two_children = 0
    households_with_three_children = 0
    households_with_more_children = 0
    households_with_contact = 0
    households_missing_contact = 0
    households_without_street = 0
    empty_households = 0
    previous_year_lukno_unpaid = 0
    households_added_this_year = 0

    for household in households:
        household_members = list(household.get('members') or [])
        member_count = len(household_members)
        persons += member_count

        if _is_active_household(household):
            active_households += 1
            parishioners += member_count
            if _has_unpaid_lukno_for_year(household, previous_year):
                previous_year_lukno_unpaid += 1

        if _household_created_in_year(household, current_year):
            households_added_this_year += 1

        if member_count == 1:
            single_person_households += 1
        elif member_count > 1:
            children_count = _count_household_children(household_members)
            if children_count == 0:
                households_without_children += 1
            elif children_count == 1:
                households_with_one_child += 1
            elif children_count == 2:
                households_with_two_children += 1
            elif children_count == 3:
                households_with_three_children += 1
            else:
                households_with_more_children += 1
        if not member_count:
            empty_households += 1

        if household.get('phone') or household.get('email'):
            households_with_contact += 1
        else:
            households_missing_contact += 1
        if not household.get('streetId'):
            households_without_street += 1

    total_households = len(households)
    contact_coverage_percent = round(
        households_with_contact / total_households * 100
    ) if total_households else 0

    return {
        'streets': len(streets),
        'households': total_households,
        'active_households': active_households,
        'persons': persons,
        'parishioners': parishioners,
        'deanery_parishes': len(parish_directory),
        'households_with_contact': households_with_contact,
        'households_missing_contact': households_missing_contact,
        'contact_coverage_percent': contact_coverage_percent,
        'single_person_households': single_person_households,
        'households_without_children': households_without_children,
        'households_with_one_child': households_with_one_child,
        'households_with_two_children': households_with_two_children,
        'households_with_three_children': households_with_three_children,
        'households_with_more_children': households_with_more_children,
        'households_without_street': households_without_street,
        'empty_households': empty_households,
        'current_year': current_year,
        'previous_year': previous_year,
        'previous_year_lukno_unpaid': previous_year_lukno_unpaid,
        'households_added_this_year': households_added_this_year,
    }


def _collect_upcoming_sacraments(parish_data: dict, today: str) -> list[dict]:
    upcoming_sacraments = []
    sacrament_sources = (
        ('baptisms', 'krštenje', 'childName', 'baptismDate', 'krsenja'),
        ('weddings', 'vjenčanje', 'couple', 'weddingDate', 'vjencanja'),
        ('funerals', 'pogreb', 'deceased', 'funeralDate', 'pogrebi'),
        ('anointing', 'pomazanje', 'person', 'scheduled', 'pomazanje'),
    )

    for collection_name, type_label, name_field, date_field, page_slug in sacrament_sources:
        for sacrament_record in parish_data.get(collection_name, []):
            event_date = sacrament_record.get(date_field) or ''
            if event_date < today:
                continue
            upcoming_sacraments.append({
                'type': type_label,
                'name': sacrament_record.get(name_field),
                'date': event_date,
                'page': page_slug,
                'status': sacrament_record.get('status') or 'planirano',
            })

    for first_communion_group in parish_data.get('firstCommunion', []):
        ceremony_date = first_communion_group.get('ceremonyDate') or ''
        if ceremony_date < today:
            continue
        upcoming_sacraments.append({
            'type': 'prva pričest',
            'name': first_communion_group.get('groupName')
            or f"Prvopričesnici {first_communion_group.get('year') or ''}",
            'date': ceremony_date,
            'page': 'prva-pricest',
            'status': f"{len(first_communion_group.get('candidates') or [])} kandidata",
        })

    for confirmation_group in parish_data.get('confirmations', []):
        ceremony_date = confirmation_group.get('ceremonyDate') or ''
        if ceremony_date < today:
            continue
        upcoming_sacraments.append({
            'type': 'krizma',
            'name': f"Krizmanici {confirmation_group.get('year') or ''}",
            'date': ceremony_date,
            'page': 'krizma',
            'status': f"{len(confirmation_group.get('candidates') or [])} kandidata",
        })

    return sorted(
        upcoming_sacraments,
        key=lambda sacrament: sacrament.get('date') or '9999',
    )


def _find_group_for_year(groups: list[dict], current_year: int) -> dict:
    group_for_current_year = next(
        (group for group in groups if group.get('year') == current_year),
        None,
    )
    return group_for_current_year or (groups or [{}])[0]


def _calculate_sacrament_pipeline(parish_data: dict, current_year: int) -> list[dict]:
    confirmation_group = _find_group_for_year(
        list(parish_data.get('confirmations') or []),
        current_year,
    )
    first_communion_group = _find_group_for_year(
        list(parish_data.get('firstCommunion') or []),
        current_year,
    )
    confirmation_candidates = list(confirmation_group.get('candidates') or [])
    first_communion_candidates = list(first_communion_group.get('candidates') or [])
    baptism_records = list(parish_data.get('baptisms') or [])
    wedding_records = list(parish_data.get('weddings') or [])

    sacrament_pipeline = [
        {
            'label': 'Krštenja',
            'count': len(baptism_records),
            'ready': sum(
                1
                for baptism_record in baptism_records
                if all(
                    baptism_record.get(required_field)
                    for required_field in (
                        'childName',
                        'parents',
                        'baptismDate',
                        'godparents',
                        'celebrant',
                    )
                )
            ),
            'page': 'krsenja',
            'tone': 'blue',
        },
        {
            'label': 'Prva pričest',
            'count': len(first_communion_candidates),
            'ready': sum(
                1
                for first_communion_candidate in first_communion_candidates
                if first_communion_candidate.get('name')
                and first_communion_candidate.get('school')
                and first_communion_candidate.get('class')
                and first_communion_candidate.get('parents')
            ),
            'page': 'prva-pricest',
            'tone': 'gold',
        },
        {
            'label': 'Krizma',
            'count': len(confirmation_candidates),
            'ready': sum(
                1
                for confirmation_candidate in confirmation_candidates
                if all(
                    confirmation_candidate.get(required_field)
                    for required_field in (
                        'name',
                        'birthDate',
                        'school',
                        'class',
                        'group',
                        'baptized',
                        'sponsor',
                    )
                )
            ),
            'page': 'krizma',
            'tone': 'violet',
        },
        {
            'label': 'Vjenčanja',
            'count': len(wedding_records),
            'ready': sum(
                1
                for wedding_record in wedding_records
                if wedding_record.get('couple')
                and wedding_record.get('weddingDate')
                and wedding_record.get('documentsOk')
                and wedding_record.get('celebrant')
                and wedding_record.get('contact')
            ),
            'page': 'vjencanja',
            'tone': 'rose',
        },
    ]

    for sacrament_summary in sacrament_pipeline:
        sacrament_summary['missing'] = (
            sacrament_summary['count'] - sacrament_summary['ready']
        )
        sacrament_summary['percent'] = (
            round(sacrament_summary['ready'] / sacrament_summary['count'] * 100)
            if sacrament_summary['count']
            else 0
        )
    return sacrament_pipeline


def _normalize_mass_time(mass_time: object) -> str:
    return str(mass_time or '').strip()


def _attach_todays_intentions_to_masses(
    todays_masses: list[dict],
    todays_intentions: list[dict],
) -> None:
    """Dodaje svakoj misi popis nakana za isto vrijeme."""
    intentions_by_mass_time: dict[str, list[dict]] = {}
    for intention in todays_intentions:
        mass_time = _normalize_mass_time(intention.get('massTime'))
        intentions_by_mass_time.setdefault(mass_time, []).append(intention)

    for mass in todays_masses:
        mass_time = _normalize_mass_time(mass.get('time'))
        mass['intentions'] = list(intentions_by_mass_time.get(mass_time, []))


def _mark_todays_mass_status(
    todays_masses: list[dict],
    current_time: str,
) -> dict | None:
    """Označava prošle mise i onu koja je sljedeća u današnjem rasporedu."""
    next_mass = next(
        (
            mass
            for mass in todays_masses
            if (mass.get('time') or '') >= current_time
        ),
        None,
    )
    for mass in todays_masses:
        mass_time = mass.get('time') or ''
        mass['is_next'] = mass is next_mass
        mass['is_past'] = bool(mass_time) and mass_time < current_time
    return next_mass


def build_dashboard_context(
    parish_data_service: ParishDataService,
    parish_data: dict | None = None,
) -> dict:
    """Sastavlja kontekst početne bez skrivanja poslovnih pravila u handleru."""
    if parish_data is None:
        parish_data = parish_data_service.load()
    today = parish_data_service.today_iso()
    current_date = date.today()

    todays_intentions = sorted(
        [
            intention
            for intention in parish_data.get('intentions', [])
            if intention.get('date') == today
        ],
        key=lambda intention: (
            intention.get('massTime') or '',
            intention.get('intentionFor') or '',
        ),
    )

    weekday = current_date.isoweekday() % 7
    todays_masses = [
        dict(mass)
        for mass in parish_data.get('massSchedule', [])
        if weekday in (mass.get('weekdays') or [])
        and schedule_entry_applies_on_date(mass, current_date.isoformat())
    ]
    todays_masses.sort(key=lambda mass: mass.get('time') or '')
    _attach_todays_intentions_to_masses(todays_masses, todays_intentions)
    next_mass = _mark_todays_mass_status(
        todays_masses,
        timezone.localtime().strftime('%H:%M'),
    )

    reminders = parish_data_service.collect_reminders(parish_data)

    return {
        'population_stats': calculate_parish_population_statistics(parish_data),
        'intentions_today': todays_intentions,
        'sacraments_upcoming': _collect_upcoming_sacraments(parish_data, today)[:6],
        'sacrament_pipeline': _calculate_sacrament_pipeline(
            parish_data,
            current_date.year,
        ),
        'work_queue': reminders[:6],
        'today_masses': todays_masses,
        'next_mass': next_mass,
        'unassigned_masses': sum(
            1 for mass in todays_masses if not mass.get('celebrant')
        ),
        'today': today,
        'liturgical_day': LiturgicalService().get_day(today),
    }
