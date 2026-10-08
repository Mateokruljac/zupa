"""Pozadinski uvoz/brisanje liturgijskog kalendara (Celery).

Generiranje Romcala je CPU-teško; HILP čitanja su mrežno teška (po danu).
Oba idu u worker, odvojeno, da HTTP admin zahtjev ne čeka.
``schema_name`` bira PostgreSQL shemu župe.
"""
from __future__ import annotations

import logging

from celery import shared_task
from django.core.exceptions import ValidationError

from django_multitenant.schema import run_in_tenant_schema
from liturgija.models import LiturgicalCalendarEntry

logger = logging.getLogger(__name__)


@shared_task
def import_calendar_package_task(provider: str, year: int, schema_name: str | None = None) -> dict:
    """Uvezi Romcal paket za godinu, pa u pozadini pokreni HILP čitanja."""
    from liturgija.services.liturgical_imports import import_romcal_package_year

    with run_in_tenant_schema(schema_name):
        try:
            created_count, skipped_count = import_romcal_package_year(year)
        except ValidationError as validation_error:
            logger.warning('Uvoz kalendara %s %s: %s', provider, year, validation_error)
            return {
                'ok': False,
                'provider': provider,
                'year': year,
                'error': str(validation_error),
            }

    fill_calendar_readings_task.delay(year, schema_name=schema_name)
    return {
        'ok': True,
        'provider': provider,
        'year': year,
        'created': created_count,
        'skipped': skipped_count,
        'readings_task': 'queued',
    }


@shared_task(soft_time_limit=60 * 60, time_limit=60 * 60 + 120)
def fill_calendar_readings_task(year: int, schema_name: str | None = None) -> dict:
    """U pozadini upiši HILP kratice čitanja za primary zapise godine."""
    from liturgija.services.liturgical_imports import fill_year_primary_readings_from_hilp

    with run_in_tenant_schema(schema_name):
        updated = fill_year_primary_readings_from_hilp(year)
        logger.info(
            'HILP čitanja za %s: ažurirano %s primary zapisa (schema=%s)',
            year,
            updated,
            schema_name,
        )
        return {'ok': True, 'year': year, 'updated': updated}


@shared_task
def delete_calendar_entries_task(entry_ids: list[int], schema_name: str | None = None) -> dict:
    """Masovno brisanje kalendara (chunk 500) pa osvježi ``is_primary``."""
    from liturgija.services.liturgical_imports import refresh_primary_flags

    with run_in_tenant_schema(schema_name):
        entry_dates = set()
        deleted_count = 0
        chunk_size = 500
        for offset in range(0, len(entry_ids), chunk_size):
            chunk_ids = entry_ids[offset:offset + chunk_size]
            queryset = LiturgicalCalendarEntry.objects.filter(pk__in=chunk_ids)
            entry_dates.update(queryset.values_list('date', flat=True))
            chunk_deleted, _ = queryset.delete()
            deleted_count += chunk_deleted
        refresh_primary_flags(entry_dates)
        logger.info('Obrisano %s liturgijskih zapisa u pozadini', deleted_count)
        return {'ok': True, 'deleted': deleted_count}
