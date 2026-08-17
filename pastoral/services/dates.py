"""Zajedničke datumske pomoćne funkcije (izvor istine umjesto JS duplikata)."""
from __future__ import annotations

from datetime import date, timedelta


def parse_iso_date(value) -> date | None:
    """Pretvori ISO datum ili datetime u ``date``; za nevaljan unos vrati ``None``."""
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def today_iso() -> str:
    return date.today().isoformat()


def week_start_from(iso: str | None = None) -> str:
    d = date.fromisoformat(iso or today_iso())
    d -= timedelta(days=d.weekday())
    return d.isoformat()


def week_end_from(start: str) -> str:
    return (date.fromisoformat(start) + timedelta(days=6)).isoformat()


def add_days_iso(n: int, from_iso: str | None = None) -> str:
    base = date.fromisoformat(from_iso or today_iso())
    return (base + timedelta(days=n)).isoformat()


def days_since(iso: str | None) -> int:
    if not iso:
        return 999
    start = date.fromisoformat(iso)
    return (date.today() - start).days


def month_key(d: date | str | None = None) -> str:
    if d is None:
        d = date.today()
    elif isinstance(d, str):
        d = date.fromisoformat(d[:10])
    return f'{d.year}-{d.month:02d}'


def fmt_hr_short(iso: str) -> str:
    d = date.fromisoformat(iso[:10])
    names = ['pon', 'uto', 'sri', 'čet', 'pet', 'sub', 'ned']
    months = ['sij', 'velj', 'ožu', 'tra', 'svi', 'lip', 'srp', 'kol', 'ruj', 'lis', 'stu', 'pro']
    return f'{names[d.weekday()]} {d.day}. {months[d.month - 1]}.'


def fmt_hr_date(iso: str | None) -> str:
    if not iso:
        return '—'
    d = date.fromisoformat(iso[:10])
    return d.strftime('%d.%m.%Y.')
