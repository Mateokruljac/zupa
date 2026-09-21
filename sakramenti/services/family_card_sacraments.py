"""
Sakramenti na obiteljskom kartonu — čitanje i stubovi, ne matica.

UI i dalje šalje listu oznaka (`krštenje`, `pričest`…). Izvor istine je
`SacramentalEvent` + `EventParticipant` (uloga primatelja).

Ako karton označi sakrament kojeg još nema u službenoj evidenciji, ovaj
modul stvara uvozni stub (`family-card:…`). Stub nema *Details red i
ne smije se pojaviti na stranici krštenja/vjenčanja.

Zaključane i potvrđene matice se ovdje ne brišu.
"""
from __future__ import annotations

from collections import defaultdict

from sakramenti.models import EventParticipant, SacramentalEvent

FAMILY_CARD_EVENT_PREFIX = 'family-card'

SACRAMENT_LABEL_TO_TYPE = {
    'krštenje': SacramentalEvent.EventType.BAPTISM,
    'krstenje': SacramentalEvent.EventType.BAPTISM,
    'baptism': SacramentalEvent.EventType.BAPTISM,
    'pričest': SacramentalEvent.EventType.FIRST_COMMUNION,
    'pricest': SacramentalEvent.EventType.FIRST_COMMUNION,
    'prva pričest': SacramentalEvent.EventType.FIRST_COMMUNION,
    'first_communion': SacramentalEvent.EventType.FIRST_COMMUNION,
    'krizma': SacramentalEvent.EventType.CONFIRMATION,
    'confirmation': SacramentalEvent.EventType.CONFIRMATION,
    'vjenčanje': SacramentalEvent.EventType.MARRIAGE,
    'vjencanje': SacramentalEvent.EventType.MARRIAGE,
    'marriage': SacramentalEvent.EventType.MARRIAGE,
    'pomazanje': SacramentalEvent.EventType.ANOINTING,
    'anointing': SacramentalEvent.EventType.ANOINTING,
}

EVENT_TYPE_TO_LABEL = {
    SacramentalEvent.EventType.BAPTISM: 'krštenje',
    SacramentalEvent.EventType.FIRST_COMMUNION: 'pričest',
    SacramentalEvent.EventType.CONFIRMATION: 'krizma',
    SacramentalEvent.EventType.MARRIAGE: 'vjenčanje',
    SacramentalEvent.EventType.ANOINTING: 'pomazanje',
}


def sacrament_types_from_labels(labels) -> set[str]:
    """Pretvara UI oznake s kartona u `SacramentalEvent.EventType` kodove."""
    types = set()
    for label in labels or []:
        event_type = SACRAMENT_LABEL_TO_TYPE.get(str(label).strip().casefold())
        if event_type:
            types.add(event_type)
    return types


def labels_from_event_types(event_types) -> list[str]:
    """Vraća UI oznake u fiksnom redoslijedu (krštenje → pomazanje)."""
    ordered = []
    for event_type, label in EVENT_TYPE_TO_LABEL.items():
        if event_type in event_types:
            ordered.append(label)
    return ordered


def family_card_public_identifier(person_id, event_type: str) -> str:
    """Stabilni id stuba da ga možemo razlikovati od službenog događaja."""
    return f'{FAMILY_CARD_EVENT_PREFIX}:{person_id}:{event_type}'


def exclude_family_card_events(queryset):
    """Izbacuje kartonske stubove iz službene evidencije sakramenata.

    Stub nije matica i nema *Details, pa bi dashboard pao na
    `event.baptism_details` ako bi se stub učitao kao krštenje.
    """
    return queryset.exclude(
        public_identifier__startswith=f'{FAMILY_CARD_EVENT_PREFIX}:',
    )


def sacrament_labels_by_person_id(person_ids) -> dict:
    """Za svaku osobu vraća UI oznake sakramenata u kojima je primatelj.

    Uključuje i službene događaje i kartonske stubove. Poništeni statusi
    se ne prikazuju.
    """
    mapping = defaultdict(set)
    if not person_ids:
        return {}
    participants = (
        EventParticipant.objects.filter(
            person_id__in=person_ids,
            role=EventParticipant.Role.RECIPIENT,
        )
        .exclude(event__status=SacramentalEvent.Status.CANCELLED)
        .select_related('event')
    )
    for participant in participants:
        mapping[participant.person_id].add(participant.event.event_type)
    return {
        person_id: labels_from_event_types(event_types)
        for person_id, event_types in mapping.items()
    }


def sync_family_card_sacraments(person, parish, labels) -> None:
    """Usklađuje stubove s checkboxima kartona; službene matice ne dira.

    Nova oznaka bez postojećeg događaja → uvozni stub.
    Skidanje oznake briše samo `family-card:` stubove koji nisu locked/confirmed.
    """
    if person is None:
        return
    wanted_types = sacrament_types_from_labels(labels)
    existing = {
        participant.event.event_type: participant.event
        for participant in EventParticipant.objects.filter(
            person=person,
            role=EventParticipant.Role.RECIPIENT,
        )
        .exclude(event__status=SacramentalEvent.Status.CANCELLED)
        .select_related('event')
    }
    for event_type in wanted_types:
        if event_type in existing:
            continue
        event = SacramentalEvent.objects.create(
            parish=parish,
            event_type=event_type,
            public_identifier=family_card_public_identifier(person.pk, event_type),
            status=SacramentalEvent.Status.LEGACY_IMPORTED,
            source=SacramentalEvent.Source.LEGACY_IMPORT,
        )
        EventParticipant.objects.create(
            parish=parish,
            event=event,
            person=person,
            role=EventParticipant.Role.RECIPIENT,
            historical_name=str(person),
        )
    for event_type, event in existing.items():
        if event_type in wanted_types:
            continue
        if not str(event.public_identifier or '').startswith(
            f'{FAMILY_CARD_EVENT_PREFIX}:'
        ):
            continue
        if event.status in {
            SacramentalEvent.Status.LOCKED,
            SacramentalEvent.Status.CONFIRMED,
        }:
            continue
        EventParticipant.objects.filter(event=event).delete()
        event.delete()
