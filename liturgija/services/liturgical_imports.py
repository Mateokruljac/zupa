"""Uvoz i čitanje liturgijskog kalendara po retcima.

Uvoz Romcala i ručni unos pune istu tablicu. Isti datum može imati više
slavlja. Ako red za izvor + datum + naziv već postoji, preskače se.
"""
from __future__ import annotations

import logging
from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction

from liturgija.models import LiturgicalCalendarEntry
from liturgija.services.liturgical_day_catalog import localize_celebration
from liturgija.services.liturgical_hilp import hilp_url
from django_multitenant.schema import with_tenant_schema

logger = logging.getLogger(__name__)

# Brojčani rang izvora → natpis ako red nema `priority_label`.
GRADE_HR = {
    0: 'Radni dan',
    1: 'Izborni spomen',
    2: 'Spomen',
    3: 'Spomen',
    4: 'Blagdan',
    5: 'Blagdan',
    6: 'Svetkovina',
    7: 'Svetkovina',
}

# Sve varijante boje (EN/HR/latinski) → token koji ide u bazu.
LITURGICAL_COLOR_ALIASES = {
    'white': LiturgicalCalendarEntry.LiturgicalColor.WHITE,
    'bijela': LiturgicalCalendarEntry.LiturgicalColor.WHITE,
    'albus': LiturgicalCalendarEntry.LiturgicalColor.WHITE,
    'gold': LiturgicalCalendarEntry.LiturgicalColor.WHITE,
    'aureus': LiturgicalCalendarEntry.LiturgicalColor.WHITE,
    'red': LiturgicalCalendarEntry.LiturgicalColor.RED,
    'crvena': LiturgicalCalendarEntry.LiturgicalColor.RED,
    'ruber': LiturgicalCalendarEntry.LiturgicalColor.RED,
    'green': LiturgicalCalendarEntry.LiturgicalColor.GREEN,
    'zelena': LiturgicalCalendarEntry.LiturgicalColor.GREEN,
    'viridis': LiturgicalCalendarEntry.LiturgicalColor.GREEN,
    'purple': LiturgicalCalendarEntry.LiturgicalColor.PURPLE,
    'violet': LiturgicalCalendarEntry.LiturgicalColor.PURPLE,
    'purpura': LiturgicalCalendarEntry.LiturgicalColor.PURPLE,
    'violaceus': LiturgicalCalendarEntry.LiturgicalColor.PURPLE,
    'ljubičasta': LiturgicalCalendarEntry.LiturgicalColor.PURPLE,
    'rose': LiturgicalCalendarEntry.LiturgicalColor.ROSE,
    'roseus': LiturgicalCalendarEntry.LiturgicalColor.ROSE,
    'ružičasta': LiturgicalCalendarEntry.LiturgicalColor.ROSE,
    'black': LiturgicalCalendarEntry.LiturgicalColor.BLACK,
    'crna': LiturgicalCalendarEntry.LiturgicalColor.BLACK,
    'niger': LiturgicalCalendarEntry.LiturgicalColor.BLACK,
}


def _source_color_tokens(source_value) -> list[str]:
    """Izvuci listu boja iz stringa ili liste (Romcal šalje listu)."""
    if isinstance(source_value, list):
        return [str(token).casefold() for token in source_value if token]
    if source_value in (None, ''):
        return []
    return [str(source_value).casefold()]


def _map_color_token(color_token: str) -> str:
    """Jedan token → enum baze, ili ``other`` ako nije poznat."""
    Color = LiturgicalCalendarEntry.LiturgicalColor
    alias = LITURGICAL_COLOR_ALIASES.get((color_token or '').casefold())
    return alias or Color.OTHER


def _latin_event_name(calendar_event: dict) -> str:
    """Latinski naziv za katalog: ``title`` (Romcal fullname) pa ``name``."""
    return str(
        calendar_event.get('title')
        or calendar_event.get('name')
        or ''
    ).strip()


def _mapped_source_colors(calendar_event: dict) -> list[str]:
    """Boje izvora, već mapirane na enum, bez duplikata (rezerva kad nema kataloga)."""
    mapped_colors = []
    for token in _source_color_tokens(
        calendar_event.get('color') or calendar_event.get('color_lcl')
    ):
        alias = LITURGICAL_COLOR_ALIASES.get(token)
        if alias and alias not in mapped_colors:
            mapped_colors.append(alias)
    return mapped_colors


def _normalized_liturgical_color(calendar_event: dict) -> str:
    """Boja iz kataloga (latinski ključ); inače prva boja izvora."""
    Color = LiturgicalCalendarEntry.LiturgicalColor
    _, catalog_color, found_in_catalog = localize_celebration(
        _latin_event_name(calendar_event),
    )
    if found_in_catalog and catalog_color:
        return _map_color_token(catalog_color)
    mapped_colors = _mapped_source_colors(calendar_event)
    return mapped_colors[0] if mapped_colors else Color.OTHER


def liturgical_color_for_entry(calendar_entry: LiturgicalCalendarEntry) -> str:
    """Boja retka iz stupca tablice."""
    return (
        calendar_entry.liturgical_color
        or LiturgicalCalendarEntry.LiturgicalColor.OTHER
    )


def color_view(color: str) -> dict:
    """Par token + hrvatski natpis za JSON frontenda."""
    lookup = dict(LiturgicalCalendarEntry.LiturgicalColor.choices)
    resolved_color = color or LiturgicalCalendarEntry.LiturgicalColor.OTHER
    return {
        'color': resolved_color,
        'colorLabel': lookup.get(resolved_color, resolved_color),
    }


def _event_priority(calendar_event: dict) -> int:
    """Rang slavlja (veći = važnije). Nevaljan ``grade`` = 0."""
    try:
        return max(0, int(calendar_event.get('grade') or 0))
    except (TypeError, ValueError):
        return 0


def _event_date(calendar_event: dict) -> date:
    """ISO string iz događaja → ``date`` (prvih 10 znakova)."""
    return date.fromisoformat(str(calendar_event.get('date'))[:10])


def _celebration_key(calendar_entry: LiturgicalCalendarEntry) -> tuple:
    """Ključ preskoka uvoza: isti izvor, datum i prikazani naziv."""
    return (calendar_entry.date, calendar_entry.name)


def _display_names(calendar_event: dict) -> tuple[str, str]:
    """(hrvatski naziv iz kataloga, latinski izvornik)."""
    original_name = _latin_event_name(calendar_event) or 'Liturgijsko slavlje'
    display_name, _, _ = localize_celebration(original_name)
    return display_name or original_name, original_name


def _entry_from_event(provider: str, calendar_event: dict) -> LiturgicalCalendarEntry:
    """Sastavi ORM instancu (još nije spremljena). ``is_primary`` kasnije."""
    name, original_name = _display_names(calendar_event)
    resolved_color = _normalized_liturgical_color(calendar_event)
    return LiturgicalCalendarEntry(
        provider=provider,
        date=_event_date(calendar_event),
        name=name,
        original_name=original_name,
        liturgical_color=resolved_color,
        priority=_event_priority(calendar_event),
        priority_label=str(
            calendar_event.get('grade_lcl')
            or calendar_event.get('grade_display')
            or ''
        ),
        is_primary=False,
    )


@with_tenant_schema
def refresh_primary_flags(entry_dates) -> None:
    """Na datumu je glavno slavlje red s najvišim prioritetom.

    Jedan SELECT i ``bulk_update`` umjesto UPDATE-a po retku.
    """
    unique_dates = {entry_date for entry_date in entry_dates if entry_date}
    if not unique_dates:
        return
    calendar_entries_by_date: dict[date, list[LiturgicalCalendarEntry]] = {}
    for calendar_entry in LiturgicalCalendarEntry.objects.filter(date__in=unique_dates):
        calendar_entries_by_date.setdefault(calendar_entry.date, []).append(
            calendar_entry,
        )
    entries_to_update = []
    for calendar_entries in calendar_entries_by_date.values():
        # Isti prioritet: veći ``id`` pobjeđuje (stabilan izbor).
        primary_entry = max(
            calendar_entries,
            key=lambda calendar_entry: (calendar_entry.priority, calendar_entry.id),
        )
        for calendar_entry in calendar_entries:
            is_primary = calendar_entry.id == primary_entry.id
            if calendar_entry.is_primary != is_primary:
                calendar_entry.is_primary = is_primary
                entries_to_update.append(calendar_entry)
    if entries_to_update:
        LiturgicalCalendarEntry.objects.bulk_update(
            entries_to_update,
            ['is_primary'],
            batch_size=500,
        )


@with_tenant_schema
def insert_calendar_entries(
    *,
    provider: str,
    calendar_events: list[dict],
    date_from: date,
    date_to: date,
) -> tuple[int, int]:
    """Unesi slavlja u rasponu. Postojeći izvor+datum+naziv se preskače.

    Returns:
        (broj unesenih, broj preskočenih).
    """
    prepared_entries = []
    seen_in_batch = set()  # duplikat unutar istog uvoza
    skipped_count = 0
    missing_catalog_names = set()
    for calendar_event in calendar_events:
        event_date = _event_date(calendar_event)
        if event_date < date_from or event_date > date_to:
            continue
        calendar_entry = _entry_from_event(provider, calendar_event)
        _, _, found_in_catalog = localize_celebration(calendar_entry.original_name)
        if not found_in_catalog and calendar_entry.original_name:
            missing_catalog_names.add(calendar_entry.original_name)
        celebration_key = _celebration_key(calendar_entry)
        if celebration_key in seen_in_batch:
            skipped_count += 1
            continue
        seen_in_batch.add(celebration_key)
        prepared_entries.append(calendar_entry)

    if missing_catalog_names:
        logger.warning(
            'Liturgijski katalog nema %s latinskih naziva; ostavljen je izvornik.',
            len(missing_catalog_names),
        )

    if not prepared_entries:
        return 0, skipped_count

    with transaction.atomic():
        existing_identities = set(
            LiturgicalCalendarEntry.objects.filter(
                provider=provider,
                date__gte=date_from,
                date__lte=date_to,
            ).values_list('date', 'name')
        )
        entries_to_create = []
        for calendar_entry in prepared_entries:
            celebration_key = _celebration_key(calendar_entry)
            if celebration_key in existing_identities:
                skipped_count += 1
                continue
            entries_to_create.append(calendar_entry)
        if entries_to_create:
            LiturgicalCalendarEntry.objects.bulk_create(
                entries_to_create,
                batch_size=500,
            )

    if entries_to_create:
        refresh_primary_flags(entry.date for entry in entries_to_create)
    return len(entries_to_create), skipped_count


def import_romcal_package_year(year: int) -> tuple[int, int]:
    """Uvezi lokalni Romcal kalendar za Hrvatsku za kalendarsku godinu."""
    from liturgija.services.liturgical_romcal import romcal_calendar_events_for_year

    calendar_events = romcal_calendar_events_for_year(year)
    if not calendar_events:
        raise ValidationError(
            f'Romcal nije vratio slavlja za godinu {year}.'
        )
    created_count, skipped_count = insert_calendar_entries(
        provider=LiturgicalCalendarEntry.Provider.ROMCAL_CROATIA,
        calendar_events=calendar_events,
        date_from=date(year, 1, 1),
        date_to=date(year, 12, 31),
    )
    return created_count, skipped_count


def empty_stored_calendar_day(iso: str) -> dict:
    """Dan bez redaka — frontend vidi poruku umjesto praznog ekrana."""
    return {
        'source': 'offline',
        'date': iso,
        'title': 'Nema unosa',
        'subtitle': 'Uvezite kalendar u tehničkoj administraciji.',
        'color': '',
        'colorLabel': '',
        'rank': '',
        'rankLabel': '',
        'observances': [],
        'celebrations': [],
        'readings': [],
        'hilpUrl': hilp_url(iso),
        'translated': True,
        'empty': True,
    }


def map_stored_calendar_day(
    iso: str,
    calendar_entries: list[LiturgicalCalendarEntry],
) -> dict:
    """Jedan dan za frontend iz retaka tablice (glavno + ostala slavlja)."""
    if not calendar_entries:
        return empty_stored_calendar_day(iso)
    primary_entry = next(
        (
            calendar_entry
            for calendar_entry in calendar_entries
            if calendar_entry.is_primary
        ),
        calendar_entries[0],  # stari redovi možda još nemaju zastavicu
    )
    observances = []
    celebrations = []  # naslovi sporednih slavlja (kratki popis)
    for calendar_entry in calendar_entries:
        rank_label = (
            calendar_entry.priority_label
            or GRADE_HR.get(calendar_entry.priority, '')
        )
        observances.append({
            'title': calendar_entry.name,
            'titleOriginal': calendar_entry.original_name,
            'rank': calendar_entry.priority,
            'rankLabel': rank_label,
            **color_view(liturgical_color_for_entry(calendar_entry)),
            'primary': calendar_entry.id == primary_entry.id,
            'provider': calendar_entry.provider,
            'translated': True,
        })
        if calendar_entry.id != primary_entry.id:
            celebrations.append(calendar_entry.name)
    return {
        'source': 'database',
        'providers': sorted({
            calendar_entry.provider for calendar_entry in calendar_entries
        }),
        'date': iso,
        'title': primary_entry.name,
        'titleOriginal': primary_entry.original_name,
        'subtitle': '',
        **color_view(liturgical_color_for_entry(primary_entry)),
        'rank': primary_entry.priority,
        'rankLabel': (
            primary_entry.priority_label
            or GRADE_HR.get(primary_entry.priority, '')
        ),
        'observances': observances,
        'celebrations': celebrations,
        'readings': [],
        'hilpUrl': hilp_url(iso),
        'translated': True,
        'empty': False,
    }


@with_tenant_schema
def stored_calendar_days(date_from: date, date_to: date) -> dict[str, dict]:
    """Dani u rasponu koji imaju barem jedan red. Ključ = ISO datum."""
    entries_by_date: dict[date, list[LiturgicalCalendarEntry]] = {}
    for calendar_entry in (
        LiturgicalCalendarEntry.objects
        .filter(date__gte=date_from, date__lte=date_to)
        .order_by('date', '-priority', 'name')
    ):
        entries_by_date.setdefault(calendar_entry.date, []).append(calendar_entry)
    return {
        entry_date.isoformat(): map_stored_calendar_day(
            entry_date.isoformat(),
            day_entries,
        )
        for entry_date, day_entries in entries_by_date.items()
    }


@with_tenant_schema
def stored_calendar_day(iso: str) -> dict:
    """Jedan ISO dan iz tablice (prazan dict-dan ako nema redaka)."""
    entry_date = date.fromisoformat(iso)
    calendar_entries = list(
        LiturgicalCalendarEntry.objects
        .filter(date=entry_date)
        .order_by('-priority', 'name')
    )
    return map_stored_calendar_day(iso, calendar_entries)
