"""
Kućanstvo, članstvo i posjete ↔ camelCase dict stranice Obitelji.

Član kartona nije `HouseholdMember`. Identitet je `Person`; pripadnost je
`HouseholdMembership` (SCD2). Sakramenti se čitaju iz događaja, ne iz JSON-a.

`husband` / `wife` u dictu su projekcija članstava s `spouse_side`, ne stupci
kućanstva. Relatives su ista tablica s `lives_in_household=False`.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from core.models import OPEN_ENDED_VALID_TO, close_current_scd2_rows, upsert_current_scd2
from sakramenti.models import EventParticipant, SacramentalEvent
from sakramenti.services.family_card_sacraments import (
    sacrament_labels_by_person_id,
    sync_family_card_sacraments,
)
from zupa_vjernici.models import (
    Household,
    HouseholdContribution,
    HouseholdMembership,
    PastoralVisit,
)
from zupa_vjernici.services.person_identity import (
    birth_year_as_text,
    find_or_create_person,
)


def _parse_iso_date(value) -> date | None:
    raw = str(value or '').strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _iso_or_empty(value: date | None) -> str:
    return value.isoformat() if value else ''


def _decimal_amount(value) -> Decimal:
    try:
        return Decimal(str(value if value is not None else 0))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


def _string_or_empty(value) -> str:
    if value is None:
        return ''
    return str(value)


def _display_name(membership: HouseholdMembership) -> str:
    if membership.person_id:
        return str(membership.person)
    return membership.historical_name or ''


def _birth_year_value(membership: HouseholdMembership):
    raw = membership.recorded_birth_year
    if not raw and membership.person_id and membership.person.date_of_birth:
        raw = str(membership.person.date_of_birth.year)
    if raw.isdigit():
        return int(raw)
    return raw


def membership_as_member_record(membership: HouseholdMembership, sacraments) -> dict:
    return {
        'id': membership.public_identifier,
        'name': _display_name(membership),
        'birthYear': _birth_year_value(membership),
        'relation': membership.role or '',
        'sacraments': list(sacraments or []),
        'roles': list(membership.pastoral_roles or []),
        'notes': membership.notes or '',
    }


def membership_as_relative_record(membership: HouseholdMembership) -> dict:
    return {
        'id': membership.public_identifier,
        'name': _display_name(membership),
        'relation': membership.role or '',
        'birthYear': membership.recorded_birth_year or '',
        'notes': membership.notes or '',
    }


def _event_field_for_person(person, event_type: str, field_name: str) -> str:
    if person is None:
        return ''
    participant = (
        EventParticipant.objects.filter(
            person=person,
            role=EventParticipant.Role.RECIPIENT,
            event__event_type=event_type,
        )
        .exclude(event__status=SacramentalEvent.Status.CANCELLED)
        .select_related('event')
        .first()
    )
    if not participant:
        return ''
    event = participant.event
    if field_name == 'date':
        return _iso_or_empty(event.event_date)
    if field_name == 'place':
        return event.place_name or ''
    return ''


def spouse_as_legacy_record(membership: HouseholdMembership | None) -> dict | None:
    if membership is None:
        return None
    person = membership.person if membership.person_id else None
    birth_year = membership.recorded_birth_year
    if not birth_year and person and person.date_of_birth:
        birth_year = str(person.date_of_birth.year)
    return {
        'name': _display_name(membership),
        'birthYear': birth_year,
        'birthPlace': (person.place_of_birth if person else '') or '',
        'baptismDate': _event_field_for_person(
            person, SacramentalEvent.EventType.BAPTISM, 'date',
        ),
        'baptismPlace': _event_field_for_person(
            person, SacramentalEvent.EventType.BAPTISM, 'place',
        ),
        'weddingChurch': _event_field_for_person(
            person, SacramentalEvent.EventType.MARRIAGE, 'place',
        ),
        'notes': membership.notes or '',
    }


def contribution_as_legacy_record(contribution: HouseholdContribution) -> dict:
    return {
        'id': contribution.public_identifier,
        'year': contribution.year,
        'luknoPaid': bool(contribution.lukno_paid),
        'luknoAmount': float(contribution.lukno_amount or 0),
        'luknoPaidAt': _iso_or_empty(contribution.lukno_paid_at),
        'churchDonation': float(contribution.church_donation or 0),
        'donationDate': _iso_or_empty(contribution.donation_date),
        'notes': contribution.notes or '',
    }


def household_as_legacy_record(household: Household) -> dict:
    """Sastavlja UI karton obitelji samo iz otvorenih članstava.

    Zatvorene SCD2 verzije članstva namjerno se ne prikazuju.
    """
    memberships = [
        membership
        for membership in household.memberships.all()
        if membership.date_to == OPEN_ENDED_VALID_TO
    ]
    person_ids = [
        membership.person_id
        for membership in memberships
        if membership.person_id
    ]
    sacraments_by_person = sacrament_labels_by_person_id(person_ids)
    residents = [
        membership
        for membership in memberships
        if membership.lives_in_household
    ]
    relatives = [
        membership
        for membership in memberships
        if not membership.lives_in_household
    ]
    husband = next(
        (
            membership
            for membership in residents
            if membership.spouse_side == HouseholdMembership.SpouseSide.HUSBAND
        ),
        None,
    )
    wife = next(
        (
            membership
            for membership in residents
            if membership.spouse_side == HouseholdMembership.SpouseSide.WIFE
        ),
        None,
    )
    return {
        'id': household.public_identifier,
        'surname': household.surname or '',
        'streetId': household.street_public_identifier or '',
        'address': household.address or '',
        'phone': household.phone or '',
        'email': household.email or '',
        'status': household.status or 'aktivna',
        'preferredMass': household.preferred_mass or '',
        'pastoralNotes': household.pastoral_notes or '',
        'originPlace': household.origin_place or '',
        'lastVisit': _iso_or_empty(household.last_visit_on),
        'tags': list(household.tags or []),
        'husband': spouse_as_legacy_record(husband),
        'wife': spouse_as_legacy_record(wife),
        'members': [
            membership_as_member_record(
                membership,
                sacraments_by_person.get(membership.person_id, []),
            )
            for membership in residents
            if not membership.public_identifier.startswith('spouse-')
        ],
        'contributions': [
            contribution_as_legacy_record(contribution)
            for contribution in household.contributions.all()
        ],
        'relatives': [
            membership_as_relative_record(membership)
            for membership in relatives
        ],
    }


def household_field_defaults_from_legacy(record: dict, street=None) -> dict:
    return {
        'surname': str(record.get('surname') or ''),
        'street': street,
        'street_public_identifier': str(record.get('streetId') or ''),
        'address': str(record.get('address') or ''),
        'phone': str(record.get('phone') or ''),
        'email': str(record.get('email') or ''),
        'status': str(record.get('status') or 'aktivna'),
        'preferred_mass': str(record.get('preferredMass') or ''),
        'pastoral_notes': str(record.get('pastoralNotes') or ''),
        'origin_place': str(record.get('originPlace') or ''),
        'last_visit_on': _parse_iso_date(record.get('lastVisit')),
        'tags': list(record.get('tags') or [])
        if isinstance(record.get('tags'), list)
        else [],
        'payload': {},
    }


def upsert_current_household(parish, public_identifier: str, defaults: dict):
    """Verzira kućanstvo i preusmjeri djecu na novi otvoreni red.

    Članstva, lukno i posjete FK-om drže `household_id` (record_id).
    Ako `save_new` zatvori stari red, bez ovog preusmjeravanja ostala bi
    siročad na zatvorenoj verziji i karton bi izgledao prazan.
    """
    previous = Household.current.filter(
        parish=parish,
        public_identifier=public_identifier,
    ).first()
    previous_pk = previous.pk if previous else None
    household, created = upsert_current_scd2(
        Household,
        {'parish': parish, 'public_identifier': public_identifier},
        defaults,
    )
    if previous_pk and household.pk != previous_pk:
        HouseholdMembership.objects.filter(household_id=previous_pk).update(
            household=household,
        )
        HouseholdContribution.objects.filter(household_id=previous_pk).update(
            household=household,
        )
        PastoralVisit.objects.filter(household_id=previous_pk).update(
            household=household,
        )
    return household, created


def _upsert_membership(
    household: Household,
    *,
    public_identifier: str,
    full_name: str,
    relation: str,
    birth_year,
    notes: str,
    sort_order: int,
    lives_in_household: bool,
    pastoral_roles=None,
    spouse_side: str = '',
    place_of_birth: str = '',
    sacrament_labels=None,
    is_head: bool = False,
) -> HouseholdMembership:
    """Otvara ili ažurira trenutačno članstvo i veže ga na Person.

    `relation` ostaje slobodni tekst kartona (majka, sin…). `spouse_side`
    označava bračni karton. Sakramenti se sinkroniziraju samo ako je lista
    poslana — inače se stubovi ne diraju.
    """
    person = find_or_create_person(
        household.parish,
        full_name=full_name,
        fallback_surname=household.surname,
        relation=relation or spouse_side,
        birth_year=birth_year_as_text(birth_year),
        place_of_birth=place_of_birth,
    )
    membership, _created = upsert_current_scd2(
        HouseholdMembership,
        {
            'household': household,
            'public_identifier': public_identifier,
        },
        {
            'person': person,
            'historical_name': str(full_name or ''),
            'role': str(relation or ''),
            'spouse_side': spouse_side or '',
            'lives_in_household': lives_in_household,
            'is_head': is_head,
            'recorded_birth_year': birth_year_as_text(birth_year),
            'pastoral_roles': list(pastoral_roles or [])
            if isinstance(pastoral_roles, list)
            else [],
            'notes': str(notes or ''),
            'sort_order': sort_order,
        },
    )
    if sacrament_labels is not None:
        sync_family_card_sacraments(person, household.parish, sacrament_labels)
    return membership


def _apply_spouse_record(
    household: Household,
    spouse_record,
    spouse_side: str,
    keep_identifiers: set,
) -> None:
    if not isinstance(spouse_record, dict):
        return
    full_name = str(spouse_record.get('name') or '').strip()
    if not full_name:
        return
    matching = None
    for membership in HouseholdMembership.current.filter(
        household=household,
    ).select_related('person'):
        display = _display_name(membership).casefold()
        if full_name.casefold() in {display, display.split()[0] if display else ''}:
            matching = membership
            break
        if membership.person_id:
            given = membership.person.given_names.casefold()
            if full_name.casefold() == given or full_name.casefold().startswith(given):
                matching = membership
                break
    public_identifier = (
        matching.public_identifier if matching else f'spouse-{spouse_side}'
    )
    keep_identifiers.add(public_identifier)
    relation = matching.role if matching else (
        'muž' if spouse_side == HouseholdMembership.SpouseSide.HUSBAND else 'žena'
    )
    baptism_labels = ['krštenje'] if spouse_record.get('baptismDate') else None
    extra_labels = []
    if spouse_record.get('weddingChurch') or spouse_record.get('weddingCivil'):
        extra_labels.append('vjenčanje')
    sacrament_labels = None
    if baptism_labels or extra_labels:
        sacrament_labels = [*(baptism_labels or []), *extra_labels]
    membership = _upsert_membership(
        household,
        public_identifier=public_identifier,
        full_name=full_name,
        relation=relation,
        birth_year=spouse_record.get('birthYear'),
        notes=str(spouse_record.get('notes') or ''),
        sort_order=matching.sort_order if matching else 0,
        lives_in_household=True,
        pastoral_roles=matching.pastoral_roles if matching else [],
        spouse_side=spouse_side,
        place_of_birth=str(spouse_record.get('birthPlace') or ''),
        sacrament_labels=sacrament_labels,
        is_head=spouse_side == HouseholdMembership.SpouseSide.HUSBAND,
    )
    person = membership.person
    if person and spouse_record.get('baptismDate'):
        from sakramenti.services.family_card_sacraments import (
            family_card_public_identifier,
        )
        event = (
            SacramentalEvent.objects.filter(
                parish=household.parish,
                event_type=SacramentalEvent.EventType.BAPTISM,
                public_identifier=family_card_public_identifier(
                    person.pk, SacramentalEvent.EventType.BAPTISM,
                ),
            ).first()
        )
        if event:
            event.event_date = _parse_iso_date(spouse_record.get('baptismDate'))
            event.place_name = str(spouse_record.get('baptismPlace') or '')[:200]
            event.save(update_fields=['event_date', 'place_name', 'updated_at'])
    if person and (spouse_record.get('weddingChurch') or spouse_record.get('weddingCivil')):
        from sakramenti.services.family_card_sacraments import (
            family_card_public_identifier,
        )
        event = (
            SacramentalEvent.objects.filter(
                parish=household.parish,
                event_type=SacramentalEvent.EventType.MARRIAGE,
                public_identifier=family_card_public_identifier(
                    person.pk, SacramentalEvent.EventType.MARRIAGE,
                ),
            ).first()
        )
        if event:
            event.place_name = str(
                spouse_record.get('weddingChurch')
                or spouse_record.get('weddingCivil')
                or ''
            )[:200]
            event.save(update_fields=['place_name', 'updated_at'])


def sync_household_nested_records(household: Household, record: dict) -> None:
    """Sinkronizira članove, rodbinu, bračni karton i lukno s UI dictom.

    Članstva kojih više nema u dictu se zatvaraju (SCD2), ne brišu.
    Lukno ostaje FCTA i i dalje se briše ako nestane iz kartona.
    """
    keep_identifiers = set()
    members = record.get('members') if isinstance(record.get('members'), list) else []
    for index, member_record in enumerate(members):
        if not isinstance(member_record, dict):
            continue
        public_identifier = str(
            member_record.get('id') or f'm-{household.public_identifier}-{index + 1}'
        )
        keep_identifiers.add(public_identifier)
        _upsert_membership(
            household,
            public_identifier=public_identifier,
            full_name=str(member_record.get('name') or ''),
            relation=str(member_record.get('relation') or ''),
            birth_year=member_record.get('birthYear'),
            notes=str(member_record.get('notes') or ''),
            sort_order=index,
            lives_in_household=True,
            pastoral_roles=member_record.get('roles')
            if isinstance(member_record.get('roles'), list)
            else [],
            sacrament_labels=member_record.get('sacraments')
            if isinstance(member_record.get('sacraments'), list)
            else [],
        )

    relatives = (
        record.get('relatives')
        if isinstance(record.get('relatives'), list)
        else []
    )
    for index, relative_record in enumerate(relatives):
        if not isinstance(relative_record, dict):
            continue
        public_identifier = str(
            relative_record.get('id')
            or f'rel-{household.public_identifier}-{index + 1}'
        )
        keep_identifiers.add(public_identifier)
        _upsert_membership(
            household,
            public_identifier=public_identifier,
            full_name=str(relative_record.get('name') or ''),
            relation=str(relative_record.get('relation') or ''),
            birth_year=relative_record.get('birthYear'),
            notes=str(relative_record.get('notes') or ''),
            sort_order=1000 + index,
            lives_in_household=False,
        )

    _apply_spouse_record(
        household,
        record.get('husband'),
        HouseholdMembership.SpouseSide.HUSBAND,
        keep_identifiers,
    )
    _apply_spouse_record(
        household,
        record.get('wife'),
        HouseholdMembership.SpouseSide.WIFE,
        keep_identifiers,
    )

    close_current_scd2_rows(
        household.memberships.exclude(public_identifier__in=keep_identifiers),
    )

    contributions = (
        record.get('contributions')
        if isinstance(record.get('contributions'), list)
        else []
    )
    keep_contributions = set()
    for index, contribution_record in enumerate(contributions):
        if not isinstance(contribution_record, dict):
            continue
        public_identifier = str(
            contribution_record.get('id')
            or f'yc-{household.public_identifier}-{index + 1}'
        )
        keep_contributions.add(public_identifier)
        year_raw = contribution_record.get('year')
        try:
            year_value = int(year_raw) if year_raw not in (None, '') else 0
        except (TypeError, ValueError):
            year_value = 0
        HouseholdContribution.objects.update_or_create(
            household=household,
            public_identifier=public_identifier,
            defaults={
                'year': year_value,
                'lukno_paid': bool(contribution_record.get('luknoPaid')),
                'lukno_amount': _decimal_amount(
                    contribution_record.get('luknoAmount')
                ),
                'lukno_paid_at': _parse_iso_date(
                    contribution_record.get('luknoPaidAt')
                ),
                'church_donation': _decimal_amount(
                    contribution_record.get('churchDonation')
                ),
                'donation_date': _parse_iso_date(
                    contribution_record.get('donationDate')
                ),
                'notes': str(contribution_record.get('notes') or ''),
            },
        )
    household.contributions.exclude(
        public_identifier__in=keep_contributions,
    ).delete()


def visit_as_legacy_record(visit: PastoralVisit) -> dict:
    return {
        'id': visit.public_identifier,
        'scheduled': _iso_or_empty(visit.scheduled_on),
        'type': visit.visit_type or '',
        'person': visit.person_name or '',
        'familyId': visit.family_public_identifier or '',
        'address': visit.address or '',
        'priest': visit.priest or '',
        'purpose': visit.purpose or '',
        'done': bool(visit.is_done),
        'report': visit.report or '',
    }


def visit_field_defaults_from_legacy(record: dict, household=None) -> dict:
    return {
        'household': household,
        'family_public_identifier': str(record.get('familyId') or ''),
        'scheduled_on': _parse_iso_date(record.get('scheduled')),
        'is_done': bool(record.get('done')),
        'visit_type': str(record.get('type') or ''),
        'person_name': str(record.get('person') or ''),
        'address': str(record.get('address') or ''),
        'priest': str(record.get('priest') or ''),
        'purpose': str(record.get('purpose') or ''),
        'report': str(record.get('report') or ''),
        'payload': {},
    }
