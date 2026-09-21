"""Katalog liturgijskih dana: latinski naziv → hrvatski naziv i boja.

Runtime čita JSON. Ako JSON još ne postoji, jednom se izgradi iz CSV-a
(`zupa_csv_liturijski_dani.csv`) u istom folderu.
"""
from __future__ import annotations

import csv
import json
import logging
import unicodedata
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).resolve().parent.parent / 'config'
JSON_PATH = CONFIG_DIR / 'liturgical_days.json'
CSV_PATH = CONFIG_DIR / 'zupa_csv_liturijski_dani.csv'


def _normalize_latin_key(latin_name: str) -> str:
    """Ujednači latinski ključ (æ/oe, razmaci) kad točan match padne."""
    folded = unicodedata.normalize('NFC', latin_name or '')
    folded = (
        folded.replace('æ', 'ae')
        .replace('Æ', 'ae')
        .replace('œ', 'oe')
        .replace('Œ', 'oe')
        .replace('«', '')
        .replace('»', '')
    )
    return ' '.join(folded.split()).casefold()


def _catalog_from_csv_rows(rows) -> dict[str, dict[str, str]]:
    catalog = {}
    for row in rows:
        fields = [field.strip() for field in row if str(field).strip() != '']
        if len(fields) < 3:
            continue
        latin_name, croatian_name, color = fields[0], fields[1], fields[2]
        if latin_name in {'original_name', 'latin'}:
            continue
        catalog[latin_name] = {
            'croatian': croatian_name.strip(),
            'color': color.strip().casefold(),
        }
    return catalog


def _load_catalog_from_csv() -> dict[str, dict[str, str]]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(encoding='utf-8', newline='') as handle:
        return _catalog_from_csv_rows(
            csv.reader(handle, delimiter='"', quotechar="'"),
        )


def _write_json_catalog(catalog: dict[str, dict[str, str]]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )


@lru_cache(maxsize=1)
def liturgical_day_catalog() -> dict[str, dict[str, str]]:
    """Učitaj JSON jednom: latin → {croatian, color}."""
    if JSON_PATH.exists():
        with JSON_PATH.open(encoding='utf-8') as catalog_file:
            return json.load(catalog_file)
    catalog = _load_catalog_from_csv()
    if catalog:
        _write_json_catalog(catalog)
        return catalog
    logger.warning(
        'Nema liturgijskog kataloga (%s niti %s).',
        JSON_PATH.name,
        CSV_PATH.name,
    )
    return {}


@lru_cache(maxsize=1)
def _normalized_catalog() -> dict[str, dict[str, str]]:
    return {
        _normalize_latin_key(latin_name): entry
        for latin_name, entry in liturgical_day_catalog().items()
    }


def lookup_liturgical_day(latin_name: str) -> dict[str, str] | None:
    """Pronađi hrvatski naziv i boju prema latinskom nazivu iz izvora."""
    key = (latin_name or '').strip()
    if not key:
        return None
    entry = liturgical_day_catalog().get(key)
    if entry is not None:
        return entry
    return _normalized_catalog().get(_normalize_latin_key(key))


def localize_celebration(latin_name: str) -> tuple[str, str, bool]:
    """
    Vrati (naziv za prikaz, boja iz kataloga ili prazno, je li pronađen).

    Ako latinskog ključa nema, ostaje izvorni naziv; uvoz smije uzeti
    boju izvora kao rezervu.
    """
    original_name = (latin_name or '').strip()
    entry = lookup_liturgical_day(original_name)
    if not entry:
        return original_name, '', False
    croatian_name = (entry.get('croatian') or '').strip()
    catalog_color = (entry.get('color') or '').strip().casefold()
    return croatian_name or original_name, catalog_color, True
