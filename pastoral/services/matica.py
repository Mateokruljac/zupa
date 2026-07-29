"""Pretraga matičnih zapisa (iz matica-lookup-engine.js)."""
from __future__ import annotations

from pastoral.services.dates import fmt_hr_date


def _match(q: str, *fields: str) -> bool:
    q = q.lower()
    return any(q in (f or '').lower() for f in fields if f)


def _fmt(iso: str | None) -> str:
    if not iso:
        return ''
    return fmt_hr_date(iso)


def search_baptisms(data: dict, query: str, limit: int = 12) -> list[dict]:
    q = (query or '').strip()
    if not q:
        return []
    rows = []
    for b in data.get('baptisms') or []:
        if not _match(q, b.get('childName'), b.get('parents'), b.get('registryNo')):
            continue
        rows.append({
            'type': 'krštenja',
            'id': b.get('id'),
            'label': f"{b.get('childName', '')} — krštenje {_fmt(b.get('baptismDate'))}",
            'payload': {
                'dijete': b.get('childName', ''),
                'ime_prezime': b.get('childName', ''),
                'roditelji': b.get('parents', ''),
                'kumovi': b.get('godparents', ''),
                'datum_krstenja': _fmt(b.get('baptismDate')),
                'maticni_broj': b.get('registryNo', ''),
                'birthDate': b.get('birthDate', ''),
                'parents': b.get('parents', ''),
            },
        })
        if len(rows) >= limit:
            break
    return rows


def search_weddings(data: dict, query: str, limit: int = 12) -> list[dict]:
    q = (query or '').strip()
    if not q:
        return []
    rows = []
    for w in data.get('weddings') or []:
        if not _match(q, w.get('couple')):
            continue
        parts = [p.strip() for p in (w.get('couple') or '').split('&')]
        rows.append({
            'type': 'vjenčanja',
            'id': w.get('id'),
            'label': f"{w.get('couple', '')} — {_fmt(w.get('weddingDate'))}",
            'payload': {
                'mladenci': w.get('couple', ''),
                'mladzenja': parts[0] if parts else '',
                'mlada': parts[1] if len(parts) > 1 else '',
                'datum': _fmt(w.get('weddingDate')),
                'datum_vjencanja': _fmt(w.get('weddingDate')),
                'svjedoci': w.get('witnesses', ''),
            },
        })
        if len(rows) >= limit:
            break
    return rows


def search_funerals(data: dict, query: str, limit: int = 12) -> list[dict]:
    q = (query or '').strip()
    if not q:
        return []
    rows = []
    for f in data.get('funerals') or []:
        if not _match(q, f.get('deceased'), f.get('familyContact')):
            continue
        deceased = (f.get('deceased') or '').lstrip('+').strip()
        rows.append({
            'type': 'umrli',
            'id': f.get('id'),
            'label': f"{f.get('deceased', '')} — {_fmt(f.get('funeralDate'))}",
            'payload': {
                'pokojnik': deceased,
                'datum_smrti': _fmt(f.get('deathDate')),
                'datum_pogreba': _fmt(f.get('funeralDate')),
                'prebivaliste': f.get('cemetery', ''),
            },
        })
        if len(rows) >= limit:
            break
    return rows


def search_all(data: dict, query: str, limit: int = 12, types: list[str] | None = None) -> list[dict]:
    allowed = types or ['krštenja', 'vjenčanja', 'umrli']
    per_type = max(4, limit // max(len(allowed), 1))
    out: list[dict] = []
    if 'krštenja' in allowed:
        out.extend(search_baptisms(data, query, per_type))
    if 'vjenčanja' in allowed:
        out.extend(search_weddings(data, query, per_type))
    if 'umrli' in allowed:
        out.extend(search_funerals(data, query, per_type))
    return out[:limit]
