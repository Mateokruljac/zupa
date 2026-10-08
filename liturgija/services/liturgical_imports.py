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
    0: 'Svagdan',
    1: 'Spomendan',
    2: 'Spomendan',
    3: 'Spomendan',
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
    return LITURGICAL_COLOR_ALIASES.get(
        (color_token or '').casefold(),
        LiturgicalCalendarEntry.LiturgicalColor.OTHER,
    )


def _latin_event_name(calendar_event: dict) -> str:
    """Latinski naziv za katalog: ``title`` (Romcal fullname) pa ``name``."""
    return str(
        calendar_event.get('title')
        or calendar_event.get('name')
        or ''
    ).strip()


def _fallback_source_color(calendar_event: dict) -> str:
    """Prva poznata boja izvora, ili ``other``."""
    for token in _source_color_tokens(
        calendar_event.get('color') or calendar_event.get('color_lcl')
    ):
        alias = LITURGICAL_COLOR_ALIASES.get(token)
        if alias:
            return alias
    return LiturgicalCalendarEntry.LiturgicalColor.OTHER


def _localized_event(calendar_event: dict) -> tuple[str, str, str, bool]:
    """(hrvatski naziv, latinski izvornik, boja enum, je li u katalogu)."""
    original_name = _latin_event_name(calendar_event) or 'Liturgijsko slavlje'
    display_name, catalog_color, found_in_catalog = localize_celebration(original_name)
    if found_in_catalog and catalog_color:
        color = _map_color_token(catalog_color)
    else:
        color = _fallback_source_color(calendar_event)
    return display_name or original_name, original_name, color, found_in_catalog


def _color_view(color: str) -> dict:
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
    """Ključ preskoka uvoza: isti datum i prikazani naziv."""
    return (calendar_entry.date, calendar_entry.name)


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
def set_as_primary(calendar_entry: LiturgicalCalendarEntry) -> None:
    """Označi red kao glavno slavlje; ostale na istom datumu demotiraj."""
    LiturgicalCalendarEntry.objects.filter(date=calendar_entry.date).exclude(
        pk=calendar_entry.pk,
    ).update(is_primary=False)
    if not calendar_entry.is_primary:
        calendar_entry.is_primary = True
        calendar_entry.save(update_fields=['is_primary', 'updated_at'])


def readings_refs_from_hilp(hilp: dict | None) -> list[dict]:
    """HILP scrape → lista ``{label, value}`` (samo kratice, bez punog teksta)."""
    if not hilp:
        return []
    refs: list[dict] = []
    for item in hilp.get('readings') or []:
        label = str(item.get('label') or '').strip()
        value = str(item.get('reference') or '').strip()
        if label and value:
            refs.append({'label': label, 'value': value})
    return refs


@with_tenant_schema
def fill_primary_readings_from_hilp(entry_dates) -> int:
    """Na primary zapisima bez čitanja upiši kratice s HILP-a.

    Returns:
        Broj ažuriranih zapisa.
    """
    from liturgija.services.liturgical_hilp import fetch_hilp_day

    unique_dates = {entry_date for entry_date in entry_dates if entry_date}
    if not unique_dates:
        return 0
    primary_entries = list(
        LiturgicalCalendarEntry.objects.filter(
            date__in=unique_dates,
            is_primary=True,
        )
    )
    entries_to_update = []
    for primary_entry in primary_entries:
        if primary_entry.readings:
            continue
        hilp = fetch_hilp_day(primary_entry.date.isoformat())
        refs = readings_refs_from_hilp(hilp)
        if not refs:
            continue
        primary_entry.readings = refs
        entries_to_update.append(primary_entry)
    if entries_to_update:
        LiturgicalCalendarEntry.objects.bulk_update(
            entries_to_update,
            ['readings'],
            batch_size=100,
        )
    return len(entries_to_update)


@with_tenant_schema
def fill_year_primary_readings_from_hilp(year: int) -> int:
    """Upiši HILP kratice za sva primary slavlja godine bez čitanja."""
    primary_dates = (
        LiturgicalCalendarEntry.objects
        .filter(date__year=year, is_primary=True)
        .values_list('date', flat=True)
    )
    return fill_primary_readings_from_hilp(primary_dates)


@with_tenant_schema
def _insert_calendar_entries(
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
    seen_in_batch = set()
    skipped_count = 0
    missing_catalog_names = set()
    for calendar_event in calendar_events:
        event_date = _event_date(calendar_event)
        if event_date < date_from or event_date > date_to:
            continue
        name, original_name, liturgical_color, found_in_catalog = _localized_event(
            calendar_event,
        )
        calendar_entry = LiturgicalCalendarEntry(
            provider=provider,
            date=event_date,
            name=name,
            original_name=original_name,
            liturgical_color=liturgical_color,
            priority=_event_priority(calendar_event),
            priority_label=str(
                calendar_event.get('grade_lcl')
                or calendar_event.get('grade_display')
                or ''
            ),
            is_primary=False,
        )
        if not found_in_catalog and original_name:
            missing_catalog_names.add(original_name)
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
            if _celebration_key(calendar_entry) in existing_identities:
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
    return _insert_calendar_entries(
        provider=LiturgicalCalendarEntry.Provider.ROMCAL_CROATIA,
        calendar_events=calendar_events,
        date_from=date(year, 1, 1),
        date_to=date(year, 12, 31),
    )


def _empty_stored_calendar_day(iso: str) -> dict:
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
        'empty': True,
    }


def _map_stored_calendar_day(
    iso: str,
    calendar_entries: list[LiturgicalCalendarEntry],
) -> dict:
    """Jedan dan za frontend iz retaka tablice (glavno + ostala slavlja)."""
    if not calendar_entries:
        return _empty_stored_calendar_day(iso)
    primary_entry = next(
        (
            calendar_entry
            for calendar_entry in calendar_entries
            if calendar_entry.is_primary
        ),
        calendar_entries[0],
    )
    observances = []
    celebrations = []
    for calendar_entry in calendar_entries:
        rank_label = (
            calendar_entry.priority_label
            or GRADE_HR.get(calendar_entry.priority, '')
        )
        observances.append({
            'title': calendar_entry.name,
            'rank': calendar_entry.priority,
            'rankLabel': rank_label,
            **_color_view(calendar_entry.liturgical_color),
            'primary': calendar_entry.id == primary_entry.id,
        })
        if calendar_entry.id != primary_entry.id:
            celebrations.append(calendar_entry.name)
    return {
        'source': 'database',
        'date': iso,
        'title': primary_entry.name,
        'subtitle': '',
        **_color_view(primary_entry.liturgical_color),
        'rank': primary_entry.priority,
        'rankLabel': (
            primary_entry.priority_label
            or GRADE_HR.get(primary_entry.priority, '')
        ),
        'observances': observances,
        'celebrations': celebrations,
        'readings': list(primary_entry.readings or []),
        'hilpUrl': hilp_url(iso),
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
        entry_date.isoformat(): _map_stored_calendar_day(
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
    return _map_stored_calendar_day(iso, calendar_entries)
