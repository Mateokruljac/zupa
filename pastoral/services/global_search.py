"""Globalna pretraga župnog ureda (Ctrl+K, formulari)."""
from __future__ import annotations

from pastoral.services.matica import search_all


def global_search(data: dict, query: str, limit: int = 20) -> list[dict]:
    q = (query or '').strip().lower()
    if len(q) < 2:
        return []

    results: list[dict] = []

    for fam in data.get('families', []):
        members = ' '.join(m.get('name', '') for m in fam.get('members') or [])
        blob = f"{fam.get('surname', '')} {fam.get('address', '')} {fam.get('phone', '')} {members}".lower()
        if q not in blob:
            continue
        results.append({
            'type': 'Obitelj',
            'label': fam.get('surname', ''),
            'sub': f"{fam.get('address', '')} · {members}".strip(' ·'),
            'href': f"obitelji?family={fam.get('id', '')}",
        })

    for n in data.get('intentions', []):
        blob = f"{n.get('intentionFor', '')} {n.get('requestedBy', '')} {n.get('date', '')}".lower()
        if q not in blob:
            continue
        results.append({
            'type': 'Nakana',
            'label': n.get('intentionFor', ''),
            'sub': f"{n.get('date', '')} {n.get('massTime', '')} · {n.get('requestedBy', '')}",
            'href': f"nakane?date={n.get('date', '')}",
        })

    for t in data.get('tasks', []):
        blob = f"{t.get('title', '')} {t.get('category', '')}".lower()
        if q not in blob:
            continue
        results.append({
            'type': 'Zadatak',
            'label': t.get('title', ''),
            'sub': f"{t.get('due', 'bez roka')} · {t.get('category', '')}",
            'href': 'kalendar',
        })

    for b in data.get('baptisms', []):
        blob = f"{b.get('childName', '')} {b.get('parents', '')}".lower()
        if q not in blob:
            continue
        results.append({
            'type': 'Krštenje',
            'label': b.get('childName', ''),
            'sub': b.get('baptismDate', ''),
            'href': 'krsenja',
        })

    for s in data.get('publicSubmissions', []):
        if s.get('status') != 'nova':
            continue
        name = s.get('name') or 'Prijava'
        if q not in name.lower() and q not in str(s.get('formType', '')).lower():
            continue
        results.append({
            'type': 'Prijava',
            'label': name,
            'sub': s.get('formType', ''),
            'href': 'javne-prijave',
        })

    if len(results) < limit:
        for r in search_all(data, query, limit - len(results)):
            results.append({
                'type': r.get('type', 'Matica'),
                'label': r.get('label', ''),
                'sub': 'Matična evidencija',
                'href': f"potvrde?tpl=potvrda_krsenja&record_type={r.get('type')}&record_id={r.get('id')}",
            })

    return results[:limit]
