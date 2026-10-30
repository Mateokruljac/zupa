"""Zajedničke pretvorbe vrijednosti između legacy UI dicta i ORM polja.

Domenske aplikacije još razmjenjuju datume i iznose kroz camelCase dictove.
Ovaj modul drži tolerantna pravila pretvorbe na jednom mjestu kako financije,
liturgija, ured i evidencija kućanstava ne bi različito tumačili isti unos.
"""
from datetime import date
from decimal import Decimal, InvalidOperation


def decimal_amount(value) -> Decimal:
    """Pretvara UI iznos u ``Decimal``; prazan ili neispravan unos postaje 0.

    Legacy spremanje dobiva stringove i prazne vrijednosti iz više sučelja.
    Tolerantno pravilo je postojeći ugovor tih adaptera; validirani obrasci
    moraju zasebno odbiti poslovno neispravan iznos prije ove pretvorbe.
    """
    try:
        return Decimal(str(value if value is not None else 0))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


def parse_iso_date(value) -> date | None:
    """Čita prvih deset znakova kao ISO datum; prazno ili smeće daje ``None``."""
    raw = str(value or '').strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def iso_or_empty(value: date | None) -> str:
    """Pretvara datum u ISO string za UI, odnosno vraća prazni string."""
    return value.isoformat() if value else ''


# Kompatibilni nazivi ostaju stabilni tijekom prijelaza grana i deploymenta.
# Javna imena su kanonski API, a postojeći pozivatelji mogu se prebaciti tek
# kada je cijela promjena sigurno isporučena kao jedna serija.
_decimal_amount = decimal_amount
_parse_iso_date = parse_iso_date
_iso_or_empty = iso_or_empty
