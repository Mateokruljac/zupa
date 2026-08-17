"""Podaci i provjerljive statistike za početnu stranicu župnog ureda."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from pastoral.services.liturgical import LiturgicalService

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


def _extract_birth_year(household_member: dict) -> int | None:
    birth_year_value = household_member.get('birthYear')
    try:
        birth_year = int(birth_year_value)
    except (TypeError, ValueError):
        return None
    return birth_year if 1800 <= birth_year <= date.today().year else None


def _is_active_household(household: dict) -> bool:
    household_status = str(household.get('status') or '').strip().casefold()
    return household_status not in INACTIVE_HOUSEHOLD_STATUSES


def calculate_parish_population_statistics(
    parish_data: dict,
    *,
    reference_date: date | None = None,
) -> dict:
    """Izračunava samo metrike koje se mogu objasniti iz postojećih zapisa.

    Dok osobe još nisu zaseban relacijski model, ``persons`` znači broj zapisa
    članova kućanstava, a ``parishioners`` članove aktivnih kućanstava.
    Maloljetnost se računa isključivo iz poznate godine rođenja.
    """
    statistics_date = reference_date or date.today()
    households = list(parish_data.get('families') or [])
    streets = list(parish_data.get('streets') or [])
    parish_directory = list(parish_data.get('parishDirectory') or [])

    persons = 0
    parishioners = 0
    minors = 0
    active_households = 0
    single_person_households = 0
    households_with_minors = 0
    households_without_minors = 0
    households_with_contact = 0
    households_missing_contact = 0
    households_without_street = 0
    empty_households = 0

    for household in households:
        household_members = list(household.get('members') or [])
        member_count = len(household_members)
        persons += member_count

        if _is_active_household(household):
            active_households += 1
            parishioners += member_count

        if member_count == 1:
            single_person_households += 1
        if not member_count:
            empty_households += 1

        household_minor_count = 0
        for household_member in household_members:
            birth_year = _extract_birth_year(household_member)
            if birth_year is not None and 0 <= statistics_date.year - birth_year < 18:
                household_minor_count += 1
        minors += household_minor_count
        if household_minor_count:
            households_with_minors += 1
        elif member_count:
            households_without_minors += 1

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
        'households_with_minors': households_with_minors,
        'households_without_minors': households_without_minors,
        'minors': minors,
        'households_without_street': households_without_street,
        'empty_households': empty_households,
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


def build_dashboard_context(parish_data_service: ParishDataService) -> dict:
    """Sastavlja kontekst početne bez skrivanja poslovnih pravila u handleru."""
    parish_data = parish_data_service.load()
    today = parish_data_service.today_iso()
    current_date = date.today()
    current_month_prefix = today[:7]

    todays_intentions = [
        intention
        for intention in parish_data.get('intentions', [])
        if intention.get('date') == today
    ]
    intentions_this_month = sum(
        1
        for intention in parish_data.get('intentions', [])
        if (intention.get('date') or '').startswith(current_month_prefix)
    )
    open_tasks = sorted(
        [task for task in parish_data.get('tasks', []) if not task.get('done')],
        key=lambda task: task.get('due') or '9999',
    )[:6]

    weekday = current_date.isoweekday() % 7
    todays_masses = [
        mass
        for mass in parish_data.get('massSchedule', [])
        if weekday in (mass.get('weekdays') or [])
    ]
    todays_masses.sort(key=lambda mass: mass.get('time') or '')

    reminders = parish_data_service.collect_reminders(parish_data)
    high_priority_count = sum(
        1 for reminder in reminders if reminder.get('priority') == 'visoka'
    )

    return {
        'stats': parish_data_service.office_statistics(parish_data),
        'population_stats': calculate_parish_population_statistics(parish_data),
        'intentions_today': todays_intentions,
        'intentions_this_month': intentions_this_month,
        'open_tasks': open_tasks,
        'sacraments_upcoming': _collect_upcoming_sacraments(parish_data, today)[:6],
        'sacrament_pipeline': _calculate_sacrament_pipeline(
            parish_data,
            current_date.year,
        ),
        'work_queue': reminders[:6],
        'high_priority_count': high_priority_count,
        'today_masses': todays_masses,
        'unassigned_masses': sum(
            1 for mass in todays_masses if not mass.get('celebrant')
        ),
        'today': today,
        'liturgical_day': LiturgicalService().get_day(today),
    }
