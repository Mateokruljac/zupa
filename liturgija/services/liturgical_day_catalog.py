"""Katalog liturgijskih dana: latinski naziv → hrvatski naziv i boja.

Runtime čita `config/liturgical_days.json`.
"""
from __future__ import annotations

import json
import logging
import unicodedata
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

JSON_PATH = Path(__file__).resolve().parent.parent / 'config' / 'liturgical_days.json'


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


@lru_cache(maxsize=1)
def _catalog() -> dict[str, dict[str, str]]:
    """Učitaj JSON jednom: latin → {croatian, color}."""
    if not JSON_PATH.exists():
        logger.warning('Nema liturgijskog kataloga (%s).', JSON_PATH.name)
        return {}
    with JSON_PATH.open(encoding='utf-8') as catalog_file:
        return json.load(catalog_file)


@lru_cache(maxsize=1)
def _normalized_catalog() -> dict[str, dict[str, str]]:
    """Isti katalog pod normaliziranim latinskim ključem (fallback lookup)."""
    return {
        _normalize_latin_key(latin_name): entry
        for latin_name, entry in _catalog().items()
    }


def localize_celebration(latin_name: str) -> tuple[str, str, bool]:
    """
    Vrati (naziv za prikaz, boja iz kataloga ili prazno, je li pronađen).

    Ako latinskog ključa nema, ostaje izvorni naziv; uvoz smije uzeti
    boju izvora kao rezervu.
    """
    original_name = (latin_name or '').strip()
    if not original_name:
        return '', '', False
    entry = _catalog().get(original_name) or _normalized_catalog().get(
        _normalize_latin_key(original_name),
    )
    if not entry:
        return original_name, '', False
    croatian_name = (entry.get('croatian') or '').strip()
    catalog_color = (entry.get('color') or '').strip().casefold()
    return croatian_name or original_name, catalog_color, True
