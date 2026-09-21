from datetime import date
from decimal import Decimal, InvalidOperation


def _decimal_amount(value) -> Decimal:
    """Stipendij u Decimal; smeće iz JSON-a postaje 0.
        Pretvara UI iznos u Decimal za ORM.

        Neispravan unos postaje 0, ne iznimka — spremanje ne smije pasti
        zbog praznog polja dok forma još šalje stringove.
        """
    try:
        return Decimal(str(value if value is not None else 0))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


def _parse_iso_date(value) -> date | None:
    """``YYYY-MM-DD`` ili prazno; neispravan string → None."""
    raw = str(value or '').strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _iso_or_empty(value: date | None) -> str:
    """Date polje → string za JSON (prazno ako nema datuma)."""
    return value.isoformat() if value else ''