"""Prijevod liturgijskih tekstova na hrvatski — deep-translator (Google)."""
from __future__ import annotations

import logging
import re

from django.core.cache import cache

logger = logging.getLogger(__name__)

_CACHE_TTL = 60 * 60 * 24 * 60  # 60 dana

_LATIN_HINT = re.compile(
    r'[æœ]|Hebdomadæ|Temporis|Feria|Dominica|Sanctæ|Beatæ|Quadragesimæ|Paschæ',
    re.I,
)


def _looks_latin(text: str) -> bool:
    if not text:
        return False
    if _LATIN_HINT.search(text):
        return True
    return bool(re.search(r'\b(et|in|de|per|ad)\b', text, re.I))


def _cache_key(text: str, source: str) -> str:
    return f'deep_hr_v1_{source}_{hash(text)}'


def translate_to_hr(text: str, *, source: str = 'auto') -> str:
    """Prijevod jednog stringa na hrvatski; kešira rezultat."""
    raw = (text or '').strip()
    if not raw or len(raw) < 2:
        return raw

    src = source
    if src == 'auto':
        src = 'la' if _looks_latin(raw) else 'en'

    key = _cache_key(raw, src)
    cached = cache.get(key)
    if cached is not None:
        return cached

    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        logger.warning('deep-translator nije instaliran')
        return raw

    for attempt_src in (src, 'en', 'auto'):
        try:
            out = GoogleTranslator(source=attempt_src, target='hr').translate(raw)
            if out and out.strip():
                cache.set(key, out.strip(), _CACHE_TTL)
                return out.strip()
        except Exception as exc:
            logger.debug('deep-translator (%s): %s', attempt_src, exc)
            continue

    return raw


def translate_reading_ref(text: str) -> str:
    """Kratka referenca čitanja (npr. Lucam 2:16-21)."""
    return translate_to_hr(text, source='la' if _looks_latin(text) else 'en')
