"""Validacija i pohrana godišnjih liturgijskih kalendara."""
from __future__ import annotations

import hashlib
import json
from datetime import date

from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from pastoral.models import LiturgicalCalendarEntry, LiturgicalCalendarImport
from pastoral.services.liturgical_translate import translate_liturgical_name


LITURGICAL_COLOR_ALIASES = {
    'white': LiturgicalCalendarEntry.LiturgicalColor.WHITE,
    'bijela': LiturgicalCalendarEntry.LiturgicalColor.WHITE,
    'red': LiturgicalCalendarEntry.LiturgicalColor.RED,
    'crvena': LiturgicalCalendarEntry.LiturgicalColor.RED,
    'green': LiturgicalCalendarEntry.LiturgicalColor.GREEN,
    'zelena': LiturgicalCalendarEntry.LiturgicalColor.GREEN,
    'purple': LiturgicalCalendarEntry.LiturgicalColor.PURPLE,
    'violet': LiturgicalCalendarEntry.LiturgicalColor.PURPLE,
    'purpura': LiturgicalCalendarEntry.LiturgicalColor.PURPLE,
    'ljubičasta': LiturgicalCalendarEntry.LiturgicalColor.PURPLE,
    'rose': LiturgicalCalendarEntry.LiturgicalColor.ROSE,
    'ružičasta': LiturgicalCalendarEntry.LiturgicalColor.ROSE,
    'black': LiturgicalCalendarEntry.LiturgicalColor.BLACK,
    'crna': LiturgicalCalendarEntry.LiturgicalColor.BLACK,
}


def extract_calendar_events(payload, expected_year: int) -> list[dict]:
    """Vraća provjerene LitCal događaje iz podržanog JSON omotača."""
    if isinstance(payload, dict):
        calendar_events = payload.get('litcal') or payload.get('Litcal')
    elif isinstance(payload, list):
        calendar_events = payload
    else:
        calendar_events = None

    if not isinstance(calendar_events, list) or not calendar_events:
        raise ValidationError(
            'Datoteka mora sadržavati neprazan popis događaja u ključu '
            '„litcal” ili „Litcal”.'
        )
    if len(calendar_events) > 5000:
        raise ValidationError(
            'Datoteka sadrži više od dopuštenih 5000 događaja za jednu godinu.'
        )

    validated_events = []
    invalid_event_numbers = []
    matching_year_event_count = 0
    for event_number, calendar_event in enumerate(calendar_events, start=1):
        if not isinstance(calendar_event, dict):
            invalid_event_numbers.append(event_number)
            continue
        event_date_text = str(calendar_event.get('date') or '')[:10]
        try:
            event_date = date.fromisoformat(event_date_text)
        except ValueError:
            invalid_event_numbers.append(event_number)
            continue
        if event_date.year == expected_year:
            matching_year_event_count += 1
        validated_events.append(calendar_event)

    if invalid_event_numbers:
        shown_event_numbers = ', '.join(
            str(event_number) for event_number in invalid_event_numbers[:10]
        )
        raise ValidationError(
            f'Neispravan datum ili zapis kod događaja: {shown_event_numbers}.'
        )
    if matching_year_event_count == 0:
        raise ValidationError(
            f'Datoteka ne sadrži nijedan događaj za godinu {expected_year}.'
        )
    return validated_events


def calendar_events_checksum(calendar_events: list[dict]) -> str:
    serialized_events = json.dumps(
        calendar_events,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')
    return hashlib.sha256(serialized_events).hexdigest()


def prepare_calendar_import(
    calendar_import: LiturgicalCalendarImport,
    *,
    calendar_events: list[dict],
    source_file_name: str,
    imported_by,
) -> LiturgicalCalendarImport:
    """Popunjava provjerene metapodatke prije spremanja modela."""
    calendar_import.events = calendar_events
    calendar_import.event_count = len(calendar_events)
    calendar_import.source_file_name = source_file_name
    calendar_import.checksum = calendar_events_checksum(calendar_events)
    calendar_import.imported_by = imported_by
    calendar_import.imported_at = timezone.now()
    return calendar_import


def _first_source_value(source_value) -> str:
    if isinstance(source_value, list):
        return str(source_value[0]) if source_value else ''
    return str(source_value or '')


def _normalized_liturgical_color(calendar_event: dict) -> str:
    source_color = _first_source_value(
        calendar_event.get('color') or calendar_event.get('color_lcl')
    ).casefold()
    return LITURGICAL_COLOR_ALIASES.get(
        source_color,
        LiturgicalCalendarEntry.LiturgicalColor.OTHER,
    )


def _event_priority(calendar_event: dict) -> int:
    try:
        return max(0, int(calendar_event.get('grade') or 0))
    except (TypeError, ValueError):
        return 0


def _primary_source_positions(calendar_events: list[dict]) -> set[int]:
    primary_event_by_date: dict[str, tuple[int, int]] = {}
    for source_position, calendar_event in enumerate(calendar_events):
        if calendar_event.get('is_vigil_mass'):
            continue
        event_date = str(calendar_event.get('date') or '')[:10]
        priority = _event_priority(calendar_event)
        selected_event = primary_event_by_date.get(event_date)
        if not selected_event or priority > selected_event[0]:
            primary_event_by_date[event_date] = (priority, source_position)
    return {
        source_position
        for _, source_position in primary_event_by_date.values()
    }


def build_calendar_entries(
    calendar_import: LiturgicalCalendarImport,
    calendar_events: list[dict],
) -> list[LiturgicalCalendarEntry]:
    """Pretvara LitCal događaje u globalne zapise pogodne za pretragu."""
    primary_source_positions = _primary_source_positions(calendar_events)
    calendar_entries = []
    for source_position, calendar_event in enumerate(calendar_events):
        original_name = str(
            calendar_event.get('name')
            or calendar_event.get('title')
            or 'Liturgijsko slavlje'
        ).strip()
        translated_name, _ = translate_liturgical_name(original_name)
        external_identifier = str(
            calendar_event.get('event_key')
            or calendar_event.get('event_idx')
            or ''
        )
        calendar_entries.append(LiturgicalCalendarEntry(
            calendar_import=calendar_import,
            date=date.fromisoformat(str(calendar_event.get('date'))[:10]),
            name=translated_name or original_name,
            original_name=original_name,
            liturgical_color=_normalized_liturgical_color(calendar_event),
            priority=_event_priority(calendar_event),
            priority_label=str(
                calendar_event.get('grade_lcl')
                or calendar_event.get('grade_display')
                or ''
            ),
            is_primary=source_position in primary_source_positions,
            external_identifier=external_identifier,
            source_position=source_position,
            raw_data=calendar_event,
        ))
    return calendar_entries


@transaction.atomic
def replace_calendar_entries(
    calendar_import: LiturgicalCalendarImport,
    calendar_events: list[dict],
) -> int:
    """Atomski zamjenjuje izvedeni globalni kalendar jedne godine."""
    calendar_import.calendar_entries.all().delete()
    calendar_entries = build_calendar_entries(
        calendar_import,
        calendar_events,
    )
    LiturgicalCalendarEntry.objects.bulk_create(
        calendar_entries,
        batch_size=500,
    )
    return len(calendar_entries)


def load_imported_calendar_events(
    year: int,
    provider: str = LiturgicalCalendarImport.Provider.LITCAL_VATICAN,
) -> list[dict] | None:
    """Učitava zadnji valjani adminski import za godinu i izvor."""
    calendar_import = (
        LiturgicalCalendarImport.objects
        .filter(year=year, provider=provider, event_count__gt=0)
        .only('events')
        .first()
    )
    if not calendar_import or not isinstance(calendar_import.events, list):
        return None
    return calendar_import.events


def clear_imported_calendar_cache(year: int) -> None:
    """Uklanja izvedene LitCal rezultate na koje utječe novi godišnji import."""
    cache_keys = [f'litcal_va_raw_{year}']
    for affected_year in (year - 1, year, year + 1):
        cache_keys.extend([
            f'litcal_va_hr_v4_days_{affected_year}_hilp_0',
            f'litcal_va_hr_v4_days_{affected_year}_hilp_1',
        ])
        for month_number in range(1, 13):
            cache_keys.append(
                f'litcal_va_hr_v4_month_{affected_year}_{month_number:02d}'
            )
    cache.delete_many(cache_keys)
