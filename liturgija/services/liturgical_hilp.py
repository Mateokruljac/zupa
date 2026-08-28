"""HILP liturgija dana — hrvatska čitanja za svaki dan."""
from __future__ import annotations

import html as html_lib
import re
import urllib.error
import urllib.request

from django.core.cache import cache

HILP_BASE = 'https://hilp.hr/liturgija-dana/'

READING_KEYS = (
    ('prvo čitanje', 'Prvo čitanje'),
    ('otpjevni psalam', 'Otpjevni psalam'),
    ('drugo čitanje', 'Drugo čitanje'),
    ('aleluja', 'Aleluja'),
    ('evanđelje', 'Evanđelje'),
)


def hilp_url(iso: str) -> str:
    y, m, d = iso.split('-')
    return f'{HILP_BASE}?god={y}&mj={int(m)}&dan={int(d)}'


def _strip_html(fragment: str) -> str:
    text = re.sub(r'<br\s*/?>', '\n', fragment or '', flags=re.I)
    text = re.sub(r'<[^>]+>', '', text)
    return html_lib.unescape(text).strip()


def _parse_blurbs(html: str) -> list[tuple[str, str]]:
    pattern = re.compile(
        r'<h4 class="et_pb_module_header"><span>(.*?)</span></h4>\s*'
        r'<div class="et_pb_blurb_description">(.*?)</div>',
        re.S | re.I,
    )
    return [(_strip_html(h), _strip_html(d)) for h, d in pattern.findall(html)]


def _is_reading_header(header: str) -> str | None:
    low = header.lower().rstrip(':').strip()
    for key, label in READING_KEYS:
        if low == key or low.startswith(key):
            return label
    return None


def _is_section_boundary(header: str) -> bool:
    low = header.lower()
    if _is_reading_header(header):
        return True
    return any(
        token in low
        for token in (
            'misna čitanja',
            'boja liturgijskog',
            'imendani',
            'misao iz evanđelja',
            'ponedjeljak',
            'utorak',
            'srijeda',
            'četvrtak',
            'petak',
            'subota',
            'nedjelja',
            'svagdan',
            'tjedan kroz godinu',
            'tjedan psaltira',
        )
    )


def parse_hilp_html(html: str) -> dict:
    blurbs = _parse_blurbs(html)
    readings: list[dict] = []
    gospel_thought = ''
    reading_refs = ''
    liturgical_week = ''
    psalter_week = ''
    color_hr = ''

    i = 0
    while i < len(blurbs):
        header, desc = blurbs[i]
        low = header.lower()

        if 'misao iz evanđelja' in low:
            gospel_thought = desc or header
            i += 1
            continue
        if low.startswith('misna čitanja'):
            reading_refs = desc.split('\n')[0].strip()
            i += 1
            continue
        if 'tjedan kroz godinu' in low:
            liturgical_week = desc or header
            i += 1
            continue
        if 'tjedan psaltira' in low:
            psalter_week = desc or header
            i += 1
            continue
        if 'boja liturgijskog' in low:
            color_hr = desc.split('\n')[0].strip()
            i += 1
            continue

        label = _is_reading_header(header)
        if label:
            ref = desc.split('\n')[0].strip()
            body_parts: list[str] = []
            j = i + 1
            while j < len(blurbs):
                nh, nd = blurbs[j]
                if _is_reading_header(nh) or _is_section_boundary(nh):
                    break
                if nd:
                    body_parts.append(nd)
                j += 1
            body = '\n\n'.join(body_parts).strip()
            text = body if body else ref
            if ref and body and ref not in body[:40]:
                text = f'{ref}\n\n{body}'
            if text:
                readings.append({'label': label, 'text': text, 'reference': ref})
            i = j
            continue

        i += 1

    return {
        'gospelThought': gospel_thought,
        'readingRefs': reading_refs,
        'liturgicalWeekHr': liturgical_week,
        'psalterWeekHr': psalter_week,
        'colorHr': color_hr,
        'readings': readings,
    }


def fetch_hilp_day(iso: str) -> dict | None:
    cache_key = f'hilp_day_v1_{iso}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    url = hilp_url(iso)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Pastoral/1.0 (+zupa)'})
        with urllib.request.urlopen(req, timeout=25) as resp:
            html = resp.read().decode('utf-8', errors='replace')
    except (urllib.error.URLError, TimeoutError, OSError):
        return None

    parsed = parse_hilp_html(html)
    if not parsed.get('readings') and not parsed.get('gospelThought'):
        return None

    parsed['source'] = 'hilp'
    parsed['hilpUrl'] = url
    cache.set(cache_key, parsed, 60 * 60 * 24)
    return parsed
