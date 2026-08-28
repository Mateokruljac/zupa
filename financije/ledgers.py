"""Župne knjige računa — partikularna praksa, bez neslužbenih nadimaka.

Župni saldo (pregled) računa se samo iz knjige crkvenih računa.
Misni prilozi i obveze vode se u zasebnoj knjizi.
"""
from __future__ import annotations

LEDGER_CRKVENI = 'crkveni'
LEDGER_KOLEKTE = 'kolekte'
LEDGER_GRADNJA = 'gradnja'
LEDGER_MISNE = 'misne'

PARISH_BALANCE_LEDGER = LEDGER_CRKVENI

LEDGERS = (
    {
        'id': LEDGER_CRKVENI,
        'label': 'Knjiga crkvenih računa',
        'short_label': 'Crkveni računi',
        'hint': 'Redoviti župni prihodi i rashodi: lukno, donacije, režije, pastoral, materijal.',
    },
    {
        'id': LEDGER_KOLEKTE,
        'label': 'Knjiga dijecezanskih kolekti',
        'short_label': 'Dijecezanske kolekte',
        'hint': 'Novac prikupljen za biskupiju; župa ga prima i predaje, nije župin saldo.',
    },
    {
        'id': LEDGER_GRADNJA,
        'label': 'Knjiga gradnje i posebnih akcija',
        'short_label': 'Gradnja i akcije',
        'hint': 'Namjenska sredstva za obnovu i posebne akcije, odvojeno od redovite blagajne.',
    },
    {
        'id': LEDGER_MISNE,
        'label': 'Misne obveze',
        'short_label': 'Misne obveze',
        'hint': 'Misni prilozi i obveze, odvojeno od ostale blagajne.',
    },
)

LEDGER_IDS = frozenset(book['id'] for book in LEDGERS)
LEDGER_CHOICES = [(book['id'], book['label']) for book in LEDGERS]
DONATION_PURPOSE_CHOICES = [
    (LEDGER_CRKVENI, 'Župa — knjiga crkvenih računa'),
    (LEDGER_GRADNJA, 'Gradnja i posebne akcije'),
    (LEDGER_KOLEKTE, 'Dijecezanska kolekta'),
]
LEDGER_BY_ID = {book['id']: book for book in LEDGERS}

_LEGACY_LEDGER = {
    'plavi': LEDGER_CRKVENI,
    'crveni': LEDGER_KOLEKTE,
}

_MASS_CATEGORIES = frozenset({
    'nakane',
    'stipendij',
    'misni-prilog',
    'misna-obveza',
    'milostinja',
})

CASHBOOK_CATEGORY_CHOICES = [
    ('lukno', 'Lukno'),
    ('donacija', 'Donacija'),
    ('rezije', 'Režije'),
    ('pastoral', 'Pastoral'),
    ('materijal', 'Materijal'),
    ('kolekta', 'Dijecezanska kolekta'),
    ('gradnja', 'Gradnja / obnova'),
    ('nakane', 'Misni prilog'),
    ('ostalo', 'Ostalo'),
]
CASHBOOK_CATEGORY_LABELS = dict(CASHBOOK_CATEGORY_CHOICES)


def normalize_ledger(value, category: str | None = None) -> str:
    raw = str(value or '').strip().lower()
    mapped = _LEGACY_LEDGER.get(raw, raw)
    if mapped in LEDGER_IDS:
        if mapped == LEDGER_CRKVENI and _is_mass_category(category):
            return LEDGER_MISNE
        return mapped
    if _is_mass_category(category):
        return LEDGER_MISNE
    return LEDGER_CRKVENI


def _is_mass_category(category: str | None) -> bool:
    return str(category or '').strip().lower() in _MASS_CATEGORIES


def ledger_label(value, *, short: bool = False) -> str:
    book = LEDGER_BY_ID.get(normalize_ledger(value))
    if not book:
        return 'Crkveni računi' if short else 'Knjiga crkvenih računa'
    return book['short_label'] if short else book['label']


def entry_ledger(entry: dict) -> str:
    return normalize_ledger(entry.get('ledger'), entry.get('category'))
