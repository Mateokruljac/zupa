"""Sve CRUD mutacije parish podataka — poziva se iz /api/action/."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from django.utils.dateparse import parse_date

DEFAULT_LUKNO = 150


def _today_iso() -> str:
    return date.today().isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _parse_date(value) -> str:
    if not value:
        return ''
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    d = parse_date(str(value))
    return d.isoformat() if d else str(value)


def sync_parishioners(data: dict) -> None:
    rows = []
    for fam in data.get('families', []):
        for m in fam.get('members') or []:
            rows.append({
                'id': m.get('id'),
                'family': fam.get('surname', ''),
                'name': m.get('name', ''),
                'phone': fam.get('phone', ''),
                'email': fam.get('email', ''),
                'status': 'aktivan' if fam.get('status') == 'aktivna' else fam.get('status', ''),
                'roles': m.get('roles') or [],
            })
    data['parishioners'] = rows


def migrate_family(fam: dict) -> None:
    if not isinstance(fam.get('contributions'), list):
        fam['contributions'] = []
    if not fam['contributions']:
        y = date.today().year
        for yr in (y - 2, y - 1, y):
            fam['contributions'].append({
                'id': _new_id('yc'),
                'year': yr,
                'luknoPaid': False,
                'luknoAmount': DEFAULT_LUKNO,
                'luknoPaidAt': '',
                'churchDonation': 0,
                'donationDate': '',
                'notes': '',
            })
    fam['contributions'].sort(key=lambda c: c.get('year', 0), reverse=True)


def normalize_data(data: dict) -> dict:
    for fam in data.get('families', []):
        migrate_family(fam)
    sync_parishioners(data)
    from pastoral.services.data_normalize import migrate_all
    migrate_all(data)
    return data


def _find_family(data: dict, fam_id: str):
    return next((f for f in data.get('families', []) if f.get('id') == fam_id), None)


def _confirmation_group(data: dict, year: int):
    return next((g for g in data.get('confirmations', []) if g.get('year') == year), None)


def _fc_group(data: dict, year: int):
    return next((g for g in data.get('firstCommunion', []) if g.get('year') == year), None)


def _payment_ref() -> str:
    return f"PAY-{uuid.uuid4().hex[:8].upper()}"


# --- Intentions ---

def create_intention(data: dict, p: dict) -> dict:
    paid = bool(p.get('paid'))
    item = {
        'id': _new_id('n'),
        'date': _parse_date(p.get('date')),
        'massTime': p.get('mass_time') or p.get('massTime') or '',
        'requestedBy': p.get('requested_by') or p.get('requestedBy') or '',
        'intentionFor': p.get('intention_for') or p.get('intentionFor') or '',
        'stipend': float(p.get('stipend') or 0),
        'paid': paid,
        'notes': p.get('notes') or '',
        'paymentId': p.get('payment_id') or p.get('paymentId') or ('' if not paid else _payment_ref()),
        'paidAt': p.get('paid_at') or p.get('paidAt') or (datetime.now(timezone.utc).isoformat() if paid else ''),
    }
    data.setdefault('intentions', []).append(item)
    return {'ok': True, 'item': item}


def update_intention(data: dict, p: dict) -> dict:
    row = next((n for n in data.get('intentions', []) if n.get('id') == p.get('id')), None)
    if not row:
        return {'ok': False, 'error': 'not_found'}
    for src, dst in (
        ('date', 'date'), ('mass_time', 'massTime'), ('massTime', 'massTime'),
        ('intention_for', 'intentionFor'), ('intentionFor', 'intentionFor'),
        ('requested_by', 'requestedBy'), ('requestedBy', 'requestedBy'),
        ('notes', 'notes'),
    ):
        if src in p:
            row[dst] = p[src] if dst != 'date' else _parse_date(p[src])
    if 'stipend' in p:
        row['stipend'] = float(p['stipend'] or 0)
    return {'ok': True, 'item': row}


def delete_intention(data: dict, p: dict) -> dict:
    iid = p.get('id') or p.get('intention_id')
    before = len(data.get('intentions', []))
    data['intentions'] = [n for n in data.get('intentions', []) if n.get('id') != iid]
    return {'ok': len(data['intentions']) < before}


def mark_intention_paid(data: dict, p: dict) -> dict:
    row = next((n for n in data.get('intentions', []) if n.get('id') == p.get('id')), None)
    if not row:
        return {'ok': False, 'error': 'not_found'}
    row['paid'] = True
    row['paymentId'] = p.get('payment_id') or p.get('paymentId') or _payment_ref()
    row['paidAt'] = p.get('paid_at') or p.get('paidAt') or datetime.now(timezone.utc).isoformat()
    return {'ok': True, 'item': row}


def toggle_intention_paid(data: dict, p: dict) -> dict:
    row = next((n for n in data.get('intentions', []) if n.get('id') == p.get('id')), None)
    if not row:
        return {'ok': False, 'error': 'not_found'}
    row['paid'] = not row.get('paid')
    if row['paid']:
        row['paymentId'] = row.get('paymentId') or _payment_ref()
        row['paidAt'] = datetime.now(timezone.utc).isoformat()
    return {'ok': True, 'item': row}


# --- Families ---

def create_family(data: dict, p: dict) -> dict:
    y = date.today().year
    fam = {
        'id': _new_id('fam'),
        'surname': (p.get('surname') or '').strip(),
        'streetId': p.get('street_id') or p.get('streetId') or '',
        'address': (p.get('address') or '').strip(),
        'phone': (p.get('phone') or '').strip(),
        'email': (p.get('email') or '').strip(),
        'status': 'aktivna',
        'preferredMass': '',
        'pastoralNotes': '',
        'originPlace': (p.get('origin_place') or p.get('originPlace') or '').strip(),
        'tags': p.get('tags') or [],
        'relatives': [],
        'husband': None,
        'wife': None,
        'members': [],
        'contributions': [],
    }
    if not fam['surname']:
        return {'ok': False, 'error': 'surname_required'}
    row = {
        'id': _new_id('yc'),
        'year': y,
        'luknoPaid': bool(p.get('lukno_paid') or p.get('luknoPaid')),
        'luknoAmount': float(p.get('lukno_amount') or p.get('luknoAmount') or DEFAULT_LUKNO),
        'luknoPaidAt': _today_iso() if p.get('lukno_paid') or p.get('luknoPaid') else '',
        'churchDonation': float(p.get('church_donation') or p.get('churchDonation') or 0),
        'donationDate': '',
        'notes': '',
    }
    fam['contributions'].append(row)
    data.setdefault('families', []).append(fam)
    sync_parishioners(data)
    return {'ok': True, 'item': fam}


def update_family(data: dict, p: dict) -> dict:
    fam = _find_family(data, p.get('id'))
    if not fam:
        return {'ok': False, 'error': 'not_found'}
    for key, src in (
        ('surname', 'surname'), ('streetId', 'street_id'), ('streetId', 'streetId'),
        ('address', 'address'), ('phone', 'phone'), ('email', 'email'),
        ('status', 'status'), ('preferredMass', 'preferred_mass'),
        ('preferredMass', 'preferredMass'), ('pastoralNotes', 'pastoral_notes'),
        ('pastoralNotes', 'pastoralNotes'), ('originPlace', 'origin_place'),
        ('originPlace', 'originPlace'),
    ):
        if src in p:
            fam[key] = p[src]
    if 'tags' in p:
        fam['tags'] = p['tags'] if isinstance(p['tags'], list) else [
            t.strip() for t in str(p['tags']).split(',') if t.strip()
        ]
    sync_parishioners(data)
    return {'ok': True, 'item': fam}


def delete_family(data: dict, p: dict) -> dict:
    fid = p.get('id') or p.get('family_id')
    data['families'] = [f for f in data.get('families', []) if f.get('id') != fid]
    sync_parishioners(data)
    return {'ok': True}


def upsert_family_member(data: dict, p: dict) -> dict:
    fam = _find_family(data, p.get('family_id') or p.get('fam_id'))
    if not fam:
        return {'ok': False, 'error': 'not_found'}
    payload = {
        'name': (p.get('name') or '').strip(),
        'relation': (p.get('relation') or '').strip(),
        'birthYear': p.get('birth_year') or p.get('birthYear') or '',
        'roles': p.get('roles') or [],
        'notes': (p.get('notes') or '').strip(),
    }
    mid = p.get('id') or p.get('member_id')
    if mid:
        m = next((x for x in fam.get('members') or [] if x.get('id') == mid), None)
        if not m:
            return {'ok': False, 'error': 'not_found'}
        m.update(payload)
        item = m
    else:
        item = {'id': _new_id('m'), 'sacraments': [], **payload}
        fam.setdefault('members', []).append(item)
    sync_parishioners(data)
    return {'ok': True, 'item': item}


def delete_family_member(data: dict, p: dict) -> dict:
    fam = _find_family(data, p.get('family_id') or p.get('fam_id'))
    if not fam:
        return {'ok': False, 'error': 'not_found'}
    mid = p.get('id') or p.get('member_id')
    fam['members'] = [m for m in fam.get('members') or [] if m.get('id') != mid]
    sync_parishioners(data)
    return {'ok': True}


def upsert_contribution(data: dict, p: dict) -> dict:
    fam = _find_family(data, p.get('family_id') or p.get('fam_id'))
    if not fam:
        return {'ok': False, 'error': 'not_found'}
    yr = int(p.get('year') or date.today().year)
    row = next((c for c in fam.get('contributions') or [] if c.get('year') == yr), None)
    if not row:
        row = {'id': _new_id('yc'), 'year': yr}
        fam.setdefault('contributions', []).append(row)
    row['luknoPaid'] = bool(p.get('lukno_paid') or p.get('luknoPaid'))
    row['luknoAmount'] = float(p.get('lukno_amount') or p.get('luknoAmount') or DEFAULT_LUKNO)
    row['luknoPaidAt'] = _parse_date(p.get('lukno_paid_at') or p.get('luknoPaidAt'))
    if row['luknoPaid'] and not row['luknoPaidAt']:
        row['luknoPaidAt'] = _today_iso()
    row['churchDonation'] = float(p.get('church_donation') or p.get('churchDonation') or 0)
    row['donationDate'] = _parse_date(p.get('donation_date') or p.get('donationDate'))
    row['notes'] = (p.get('notes') or '').strip()
    return {'ok': True, 'item': row}


def delete_contribution(data: dict, p: dict) -> dict:
    fam = _find_family(data, p.get('family_id') or p.get('fam_id'))
    if not fam:
        return {'ok': False, 'error': 'not_found'}
    yr = int(p.get('year'))
    fam['contributions'] = [c for c in fam.get('contributions') or [] if c.get('year') != yr]
    return {'ok': True}


def update_spouse(data: dict, p: dict) -> dict:
    fam = _find_family(data, p.get('family_id') or p.get('fam_id'))
    if not fam:
        return {'ok': False, 'error': 'not_found'}
    which = p.get('which') or p.get('spouse') or 'husband'
    payload = {k: p.get(k, '') for k in (
        'name', 'birthYear', 'birthPlace', 'baptismDate', 'baptismPlace', 'weddingChurch', 'notes'
    )}
    fam[which] = payload
    return {'ok': True}


def upsert_relative(data: dict, p: dict) -> dict:
    fam = _find_family(data, p.get('family_id') or p.get('fam_id'))
    if not fam:
        return {'ok': False, 'error': 'not_found'}
    payload = {
        'name': (p.get('name') or '').strip(),
        'relation': (p.get('relation') or '').strip(),
        'birthYear': p.get('birth_year') or p.get('birthYear') or '',
        'notes': (p.get('notes') or '').strip(),
    }
    rid = p.get('id')
    if rid:
        r = next((x for x in fam.get('relatives') or [] if x.get('id') == rid), None)
        if not r:
            return {'ok': False, 'error': 'not_found'}
        r.update(payload)
        item = r
    else:
        item = {'id': _new_id('rel'), **payload}
        fam.setdefault('relatives', []).append(item)
    return {'ok': True, 'item': item}


def delete_relative(data: dict, p: dict) -> dict:
    fam = _find_family(data, p.get('family_id') or p.get('fam_id'))
    if not fam:
        return {'ok': False, 'error': 'not_found'}
    rid = p.get('id')
    fam['relatives'] = [r for r in fam.get('relatives') or [] if r.get('id') != rid]
    return {'ok': True}


def update_family_notes(data: dict, p: dict) -> dict:
    fam = _find_family(data, p.get('family_id') or p.get('fam_id'))
    if not fam:
        return {'ok': False, 'error': 'not_found'}
    fam['pastoralNotes'] = (p.get('pastoral_notes') or p.get('pastoralNotes') or '').strip()
    return {'ok': True}


# --- Streets ---

def upsert_street(data: dict, p: dict) -> dict:
    sid = p.get('id')
    payload = {
        'name': (p.get('name') or '').strip(),
        'zone': (p.get('zone') or '').strip(),
        'notes': (p.get('notes') or '').strip(),
    }
    if not payload['name']:
        return {'ok': False, 'error': 'name_required'}
    if sid:
        st = next((s for s in data.get('streets', []) if s.get('id') == sid), None)
        if not st:
            return {'ok': False, 'error': 'not_found'}
        st.update(payload)
        return {'ok': True, 'item': st}
    item = {
        'id': _new_id('st'),
        'sortOrder': len(data.get('streets', [])) + 1,
        **payload,
    }
    data.setdefault('streets', []).append(item)
    return {'ok': True, 'item': item}


def delete_street(data: dict, p: dict) -> dict:
    sid = p.get('id')
    data['streets'] = [s for s in data.get('streets', []) if s.get('id') != sid]
    return {'ok': True}


# --- Sacraments (generic upsert) ---

def upsert_sacrament(data: dict, p: dict) -> dict:
    key = p.get('array_key') or p.get('arrayKey')
    if not key:
        return {'ok': False, 'error': 'array_key_required'}
    fields = dict(p.get('fields') or {})
    rid = p.get('id')
    arr = data.setdefault(key, [])
    if rid:
        row = next((x for x in arr if x.get('id') == rid), None)
        if not row:
            return {'ok': False, 'error': 'not_found'}
        row.update(fields)
        return {'ok': True, 'item': row}
    prefix = {'baptisms': 'b', 'weddings': 'w', 'funerals': 'f', 'anointing': 'a'}.get(key, 's')
    item = {'id': _new_id(prefix), **fields}
    if key == 'anointing':
        arr.insert(0, item)
    else:
        arr.append(item)
    return {'ok': True, 'item': item}


def delete_sacrament_record(data: dict, p: dict) -> dict:
    key = p.get('array_key') or p.get('arrayKey')
    rid = p.get('id')
    before = len(data.get(key, []))
    data[key] = [r for r in data.get(key, []) if r.get('id') != rid]
    return {'ok': len(data.get(key, [])) < before}


# --- Tasks ---

def upsert_task(data: dict, p: dict) -> dict:
    tid = p.get('id')
    payload = {
        'title': (p.get('title') or '').strip(),
        'due': _parse_date(p.get('due')),
        'category': (p.get('category') or 'ŽPV').strip(),
        'priority': p.get('priority') or 'srednja',
        'done': bool(p.get('done')),
    }
    if not payload['title']:
        return {'ok': False, 'error': 'title_required'}
    if tid:
        row = next((t for t in data.get('tasks', []) if t.get('id') == tid), None)
        if not row:
            return {'ok': False, 'error': 'not_found'}
        row.update(payload)
        return {'ok': True, 'item': row}
    item = {'id': _new_id('t'), **payload}
    data.setdefault('tasks', []).append(item)
    return {'ok': True, 'item': item}


def delete_task(data: dict, p: dict) -> dict:
    tid = p.get('id')
    data['tasks'] = [t for t in data.get('tasks', []) if t.get('id') != tid]
    return {'ok': True}


def toggle_task(data: dict, p: dict) -> dict:
    row = next((t for t in data.get('tasks', []) if t.get('id') == p.get('id')), None)
    if not row:
        return {'ok': False, 'error': 'not_found'}
    row['done'] = not row.get('done')
    return {'ok': True, 'item': row}


# --- Krizma ---

def create_krizma_year(data: dict, p: dict) -> dict:
    y = int(p.get('year'))
    if _confirmation_group(data, y):
        return {'ok': False, 'error': 'year_exists'}
    item = {
        'id': _new_id('conf'),
        'year': y,
        'bishop': (p.get('bishop') or '').strip(),
        'ceremonyDate': _parse_date(p.get('ceremony_date') or p.get('ceremonyDate')),
        'groupFee': float(p.get('group_fee') or p.get('groupFee') or 0),
        'groupFeePaid': False,
        'candidates': [],
    }
    data.setdefault('confirmations', []).insert(0, item)
    return {'ok': True, 'item': item}


def update_krizma_group(data: dict, p: dict) -> dict:
    grp = _confirmation_group(data, int(p.get('year')))
    if not grp:
        return {'ok': False, 'error': 'not_found'}
    grp['ceremonyDate'] = _parse_date(p.get('ceremony_date') or p.get('ceremonyDate'))
    grp['bishop'] = (p.get('bishop') or '').strip()
    grp['groupFee'] = float(p.get('group_fee') or p.get('groupFee') or 0)
    grp['groupFeePaid'] = bool(p.get('group_fee_paid') or p.get('groupFeePaid'))
    if grp['groupFeePaid'] and not grp.get('groupFeePaidAt'):
        grp['groupFeePaidAt'] = _today_iso()
    return {'ok': True, 'item': grp}


def upsert_krizmanik(data: dict, p: dict) -> dict:
    year = int(p.get('year'))
    grp = _confirmation_group(data, year)
    if not grp:
        grp = create_krizma_year(data, {'year': year})['item']
    payload = {k: p.get(k, '') for k in (
        'name', 'birthDate', 'school', 'class', 'group', 'baptized', 'sponsor', 'status', 'oib'
    )}
    cid = p.get('id')
    if cid:
        c = next((x for x in grp.get('candidates') or [] if x.get('id') == cid), None)
        if not c:
            return {'ok': False, 'error': 'not_found'}
        c.update(payload)
        return {'ok': True, 'item': c}
    item = {'id': _new_id('cr'), **payload}
    grp.setdefault('candidates', []).append(item)
    return {'ok': True, 'item': item}


def delete_krizmanik(data: dict, p: dict) -> dict:
    year = int(p.get('year'))
    grp = _confirmation_group(data, year)
    if not grp:
        return {'ok': False, 'error': 'not_found'}
    cid = p.get('id')
    grp['candidates'] = [c for c in grp.get('candidates') or [] if c.get('id') != cid]
    return {'ok': True}


# --- Prva pričest ---

def create_fc_year(data: dict, p: dict) -> dict:
    y = int(p.get('year'))
    if _fc_group(data, y):
        return {'ok': False, 'error': 'year_exists'}
    item = {
        'id': _new_id('fc'),
        'year': y,
        'groupName': (p.get('group_name') or p.get('groupName') or f'Skupina {y}').strip(),
        'celebrant': (p.get('celebrant') or '').strip(),
        'ceremonyDate': _parse_date(p.get('ceremony_date') or p.get('ceremonyDate')),
        'groupFee': 0,
        'groupFeePaid': False,
        'candidates': [],
    }
    data.setdefault('firstCommunion', []).insert(0, item)
    return {'ok': True, 'item': item}


def upsert_prvopricestnik(data: dict, p: dict) -> dict:
    year = int(p.get('year'))
    grp = _fc_group(data, year)
    if not grp:
        grp = create_fc_year(data, {'year': year})['item']
    payload = dict(p.get('fields') or p)
    cid = p.get('id')
    if cid:
        c = next((x for x in grp.get('candidates') or [] if x.get('id') == cid), None)
        if not c:
            return {'ok': False, 'error': 'not_found'}
        c.update(payload)
        return {'ok': True, 'item': c}
    item = {'id': _new_id('c'), **payload}
    grp.setdefault('candidates', []).append(item)
    return {'ok': True, 'item': item}


def delete_prvopricestnik(data: dict, p: dict) -> dict:
    year = int(p.get('year'))
    grp = _fc_group(data, year)
    if not grp:
        return {'ok': False, 'error': 'not_found'}
    cid = p.get('id')
    grp['candidates'] = [c for c in grp.get('candidates') or [] if c.get('id') != cid]
    return {'ok': True}


# --- Parish debts ---

def upsert_parish_debt(data: dict, p: dict) -> dict:
    payload = {
        'direction': p.get('direction') or 'payable',
        'label': (p.get('label') or '').strip(),
        'category': p.get('category') or 'ostalo',
        'year': int(p.get('year') or date.today().year),
        'amount': float(p.get('amount') or 0),
        'dueDate': _parse_date(p.get('due_date') or p.get('dueDate')),
        'contact': (p.get('contact') or '').strip(),
        'notes': (p.get('notes') or '').strip(),
        'paid': bool(p.get('paid')),
        'paidAt': _parse_date(p.get('paid_at') or p.get('paidAt')),
    }
    if not payload['label']:
        return {'ok': False, 'error': 'label_required'}
    if payload['paid'] and not payload['paidAt']:
        payload['paidAt'] = _today_iso()
    did = p.get('id')
    if did:
        row = next((d for d in data.get('parishDebts', []) if d.get('id') == did), None)
        if not row:
            return {'ok': False, 'error': 'not_found'}
        row.update(payload)
        return {'ok': True, 'item': row}
    item = {'id': _new_id('pd'), **payload}
    data.setdefault('parishDebts', []).insert(0, item)
    return {'ok': True, 'item': item}


def delete_parish_debt(data: dict, p: dict) -> dict:
    did = p.get('id')
    data['parishDebts'] = [d for d in data.get('parishDebts', []) if d.get('id') != did]
    return {'ok': True}


def mark_debt_paid(data: dict, p: dict) -> dict:
    from pastoral.services.mutations import mark_debt_paid as _mark
    source = p.get('source') or {}
    if not _mark(data, source):
        return {'ok': False, 'error': 'not_found'}
    return {'ok': True}


# --- Mass schedule ---

def _log_mass_change(data: dict, msg: str) -> None:
    data.setdefault('massScheduleLog', []).insert(0, {
        'id': _new_id('msl'),
        'at': datetime.now(timezone.utc).isoformat(),
        'message': msg,
    })


def upsert_mass_schedule(data: dict, p: dict) -> dict:
    fields = dict(p.get('fields') or p)
    rid = p.get('id')
    if rid:
        row = next((x for x in data.get('massSchedule', []) if x.get('id') == rid), None)
        if not row:
            return {'ok': False, 'error': 'not_found'}
        row.update(fields)
        _log_mass_change(data, f"Uređen termin {fields.get('time', '')} ({fields.get('day', '')})")
        return {'ok': True, 'item': row}
    item = {'id': _new_id('ms'), **fields}
    data.setdefault('massSchedule', []).append(item)
    _log_mass_change(data, f"Dodan termin {fields.get('time', '')} ({fields.get('day', '')})")
    return {'ok': True, 'item': item}


def delete_mass_schedule(data: dict, p: dict) -> dict:
    rid = p.get('id')
    row = next((x for x in data.get('massSchedule', []) if x.get('id') == rid), None)
    data['massSchedule'] = [x for x in data.get('massSchedule', []) if x.get('id') != rid]
    _log_mass_change(data, f"Obrisan termin {row.get('time', '') if row else ''}")
    return {'ok': True}


def upsert_mass_exception(data: dict, p: dict) -> dict:
    fields = dict(p.get('fields') or p)
    rid = p.get('id')
    if rid:
        row = next((x for x in data.get('massExceptions', []) if x.get('id') == rid), None)
        if not row:
            return {'ok': False, 'error': 'not_found'}
        row.update(fields)
        _log_mass_change(data, f"Uređena iznimka {fields.get('date', '')}")
        return {'ok': True, 'item': row}
    item = {'id': _new_id('mexc'), **fields}
    data.setdefault('massExceptions', []).append(item)
    _log_mass_change(data, f"Dodana iznimka {fields.get('date', '')}")
    return {'ok': True, 'item': item}


def delete_mass_exception(data: dict, p: dict) -> dict:
    rid = p.get('id')
    data['massExceptions'] = [x for x in data.get('massExceptions', []) if x.get('id') != rid]
    return {'ok': True}


# --- Župni listić ---

def save_listic_layout(data: dict, p: dict) -> dict:
    layout = p.get('layout') or p.get('zupniListicLayout')
    if layout:
        data['zupniListicLayout'] = layout
    return {'ok': True}


def reset_listic_layout(data: dict, p: dict) -> dict:
    layout = p.get('layout')
    if layout:
        data['zupniListicLayout'] = layout
    return {'ok': True}


def upsert_listic_issue(data: dict, p: dict, settings: dict | None = None) -> dict:
    from pastoral.services.zupni_listic import prepare_issue
    issue = prepare_issue(data, settings or {}, dict(p.get('issue') or p))
    iid = issue.get('id')
    arr = data.setdefault('zupniListicIssues', [])
    if iid:
        row = next((x for x in arr if x.get('id') == iid), None)
        if row:
            row.update(issue)
            return {'ok': True, 'item': row}
    arr.insert(0, issue)
    return {'ok': True, 'item': issue}


def render_listic_preview(data: dict, p: dict, settings: dict | None = None) -> dict:
    from pastoral.services.zupni_listic import render_preview
    return render_preview(data, settings or {}, p)


def get_analytics_stats(data: dict, p: dict, settings: dict | None = None) -> dict:
    from pastoral.services.analytics import compute_stats
    return {'ok': True, 'stats': compute_stats(data)}


def get_reminders(data: dict, p: dict, settings: dict | None = None) -> dict:
    from pastoral.services.reminders import collect_reminders
    return {'ok': True, 'items': collect_reminders(data)}


def build_bulletin_html(data: dict, p: dict, settings: dict | None = None) -> dict:
    from pastoral.services.bulletin import build_bulletin_html as build_html
    start = p.get('weekStart')
    return {'ok': True, 'html': build_html(data, settings or {}, start)}


def list_document_templates(data: dict, p: dict, settings: dict | None = None) -> dict:
    from pastoral.services.documents import list_templates
    return {'ok': True, 'templates': list_templates()}


def load_document_templates(data: dict, p: dict, settings: dict | None = None) -> dict:
    from pastoral.services.documents import load_templates
    return {'ok': True, 'templates': load_templates()}


def merge_document_template(data: dict, p: dict, settings: dict | None = None) -> dict:
    from pastoral.services.documents import merge_template, render_template
    tid = p.get('templateId')
    values = p.get('values') or {}
    if tid:
        html = render_template(tid, values)
    else:
        html = merge_template(p.get('html') or '', values)
    return {'ok': True, 'html': html}


def search_matica(data: dict, p: dict, settings: dict | None = None) -> dict:
    from pastoral.services.matica import search_all
    q = p.get('q') or p.get('query') or ''
    types = p.get('types')
    return {
        'ok': True,
        'results': search_all(data, q, int(p.get('limit') or 12), types=types),
    }


def get_masses_for_date(data: dict, p: dict, settings: dict | None = None) -> dict:
    from pastoral.services.mass_schedule import get_masses_for_date as masses
    iso = p.get('date') or p.get('iso') or _today_iso()
    return {'ok': True, 'slots': masses(data, iso)}


def delete_listic_issue(data: dict, p: dict) -> dict:
    iid = p.get('id')
    data['zupniListicIssues'] = [x for x in data.get('zupniListicIssues', []) if x.get('id') != iid]
    return {'ok': True}


# --- Visits ---

def upsert_visit(data: dict, p: dict) -> dict:
    payload = dict(p.get('fields') or p)
    vid = p.get('id')
    if vid:
        row = next((v for v in data.get('visits', []) if v.get('id') == vid), None)
        if not row:
            return {'ok': False, 'error': 'not_found'}
        row.update(payload)
        if row.get('done') and row.get('familyId'):
            fam = _find_family(data, row['familyId'])
            if fam:
                fam['lastVisit'] = _today_iso()
        return {'ok': True, 'item': row}
    item = {'id': _new_id('v'), 'done': False, **payload}
    data.setdefault('visits', []).append(item)
    return {'ok': True, 'item': item}


def toggle_visit_done(data: dict, p: dict) -> dict:
    row = next((v for v in data.get('visits', []) if v.get('id') == p.get('id')), None)
    if not row:
        return {'ok': False, 'error': 'not_found'}
    row['done'] = not row.get('done')
    if row['done'] and row.get('familyId'):
        fam = _find_family(data, row['familyId'])
        if fam:
            fam['lastVisit'] = _today_iso()
    return {'ok': True, 'item': row}


# --- Invoices ---

def upsert_invoice(data: dict, p: dict) -> dict:
    fields = dict(p.get('fields') or p)
    iid = p.get('id')
    if iid:
        row = next((x for x in data.get('invoices', []) if x.get('id') == iid), None)
        if not row:
            return {'ok': False, 'error': 'not_found'}
        row.update(fields)
        return {'ok': True, 'item': row}
    item = {'id': _new_id('inv'), 'direction': 'incoming', **fields}
    data.setdefault('invoices', []).append(item)
    return {'ok': True, 'item': item}


def mark_invoice_paid(data: dict, p: dict) -> dict:
    row = next((x for x in data.get('invoices', []) if x.get('id') == p.get('id')), None)
    if not row:
        return {'ok': False, 'error': 'not_found'}
    row['paidAmount'] = row.get('total') or row.get('amount')
    row['paidAt'] = _today_iso()
    row['status'] = 'placen'
    return {'ok': True, 'item': row}


# --- Cashbook ---

def create_cashbook_entry(data: dict, p: dict) -> dict:
    fields = dict(p.get('fields') or p)
    item = {'id': _new_id('cb'), **fields}
    data.setdefault('cashbook', []).insert(0, item)
    extra = p.get('auto_entries') or []
    for e in extra:
        data['cashbook'].insert(0, {'id': _new_id('cb'), **e})
    return {'ok': True, 'item': item}


# --- Users / groups ---

def upsert_app_group(data: dict, p: dict) -> dict:
    fields = dict(p.get('fields') or p)
    gid = p.get('id')
    if gid:
        row = next((g for g in data.get('appGroups', []) if g.get('id') == gid), None)
        if not row:
            return {'ok': False, 'error': 'not_found'}
        row.update(fields)
        return {'ok': True, 'item': row}
    item = {'id': fields.get('id') or _new_id('grp'), **fields}
    data.setdefault('appGroups', []).append(item)
    return {'ok': True, 'item': item}


def upsert_app_user(data: dict, p: dict) -> dict:
    fields = dict(p.get('fields') or p)
    uid = p.get('id')
    if uid:
        row = next((u for u in data.get('appUsers', []) if u.get('id') == uid), None)
        if not row:
            return {'ok': False, 'error': 'not_found'}
        row.update(fields)
    else:
        item = {'id': _new_id('usr'), **fields}
        data.setdefault('appUsers', []).append(item)
        row = item
    priest_id = fields.get('priestId')
    if priest_id:
        pr = next((x for x in data.get('parishPriests', []) if x.get('id') == priest_id), None)
        if pr:
            pr['userId'] = row['id']
            pr['email'] = row.get('email', '')
            pr['name'] = row.get('name', '')
    return {'ok': True, 'item': row}


def upsert_parish_priest(data: dict, p: dict) -> dict:
    fields = dict(p.get('fields') or p)
    pid = p.get('id')
    if pid:
        row = next((x for x in data.get('parishPriests', []) if x.get('id') == pid), None)
        if not row:
            return {'ok': False, 'error': 'not_found'}
        row.update(fields)
        return {'ok': True, 'item': row}
    item = {'id': _new_id('pr'), **fields}
    data.setdefault('parishPriests', []).append(item)
    return {'ok': True, 'item': item}


# --- Staff messages ---

def send_staff_message(data: dict, p: dict) -> dict:
    item = {
        'id': _new_id('msg'),
        'from': p.get('from', ''),
        'fromRole': p.get('from_role') or p.get('fromRole', ''),
        'to': p.get('to', ''),
        'toRole': p.get('to_role') or p.get('toRole', ''),
        'subject': p.get('subject', ''),
        'body': p.get('body', ''),
        'at': p.get('at') or datetime.now(timezone.utc).isoformat(),
        'read': False,
    }
    data.setdefault('staffMessages', []).insert(0, item)
    return {'ok': True, 'item': item}


def delete_staff_message(data: dict, p: dict) -> dict:
    mid = p.get('id')
    data['staffMessages'] = [m for m in data.get('staffMessages', []) if m.get('id') != mid]
    return {'ok': True}


def mark_staff_message_read(data: dict, p: dict) -> dict:
    row = next((m for m in data.get('staffMessages', []) if m.get('id') == p.get('id')), None)
    if not row:
        return {'ok': False, 'error': 'not_found'}
    row['read'] = True
    return {'ok': True}


# --- Prep checklist ---

def toggle_prep_checklist(data: dict, p: dict) -> dict:
    key = p.get('array_key') or p.get('arrayKey')
    rid = p.get('id')
    step_id = p.get('step_id') or p.get('stepId')
    row = next((x for x in data.get(key, []) if x.get('id') == rid), None)
    if not row:
        return {'ok': False, 'error': 'not_found'}
    for step in row.get('prepChecklist') or []:
        if step.get('id') == step_id:
            step['done'] = bool(p.get('done'))
    side = p.get('side_fields') or {}
    row.update(side)
    return {'ok': True, 'item': row}


# --- Public submissions ---

def mark_public_submission_imported(data: dict, p: dict) -> dict:
    row = next((s for s in data.get('publicSubmissions', []) if s.get('id') == p.get('id')), None)
    if not row:
        return {'ok': False, 'error': 'not_found'}
    row['status'] = 'preuzeto'
    return {'ok': True}


def import_public_submission(data: dict, p: dict) -> dict:
    sub = p.get('submission') or p
    stype = sub.get('type') or sub.get('formType')
    d = sub.get('data') or {}
    year = int(p.get('year') or date.today().year)
    sid = sub.get('id')

    if stype == 'krizma':
        upsert_krizmanik(data, {
            'year': year,
            'name': f"{d.get('ime', '')} {d.get('prezime', '')}".strip(),
            'birthDate': d.get('datum_rodjenja', ''),
            'school': d.get('skola', ''),
            'class': d.get('razred', ''),
            'group': 'A',
            'baptized': d.get('datum_krstenja', ''),
            'sponsor': d.get('kum', ''),
            'status': 'upis',
            'oib': '',
        })
    elif stype == 'krstenje':
        upsert_sacrament(data, {
            'array_key': 'baptisms',
            'fields': {
                'childName': d.get('ime_djeteta') or '—',
                'birthDate': d.get('datum_rodjenja', ''),
                'baptismDate': d.get('zeljeni_termin', ''),
                'parents': d.get('roditelji', ''),
                'godparents': d.get('kumovi', ''),
                'celebrant': '',
                'registryNo': '',
                'status': 'upis',
            },
        })
    elif stype == 'pricest':
        name_raw = str(d.get('ime_djeteta') or '—').strip()
        parts = name_raw.split()
        last_name = parts.pop() if len(parts) > 1 else ''
        first_name = ' '.join(parts) or name_raw
        upsert_prvopricestnik(data, {
            'year': year,
            'fields': {
                'firstName': first_name,
                'lastName': last_name,
                'name': f'{first_name} {last_name}'.strip(),
                'school': d.get('skola', ''),
                'class': d.get('razred', ''),
                'parents': d.get('roditelji', ''),
                'paid': False,
            },
        })
    elif stype == 'ukop':
        upsert_sacrament(data, {
            'array_key': 'funerals',
            'fields': {
                'deceased': d.get('pokojnik') or '—',
                'deathDate': d.get('datum_smrti', ''),
                'funeralDate': d.get('zeljeni_datum', ''),
                'cemetery': d.get('groblje', ''),
                'cemeteryLocation': d.get('groblje', ''),
                'celebrant': '',
                'massPlanned': False,
                'massDate': d.get('zeljeni_datum', ''),
                'massTime': '',
                'familyContact': f"{d.get('kontakt', '')} {d.get('telefon', '')}".strip(),
                'status': 'upis',
                'stipend': 0,
                'stipendPaid': False,
            },
        })
    else:
        return {'ok': False, 'error': 'unknown_type'}

    if sid:
        mark_public_submission_imported(data, {'id': sid})
    return {'ok': True}


def import_krizmanici(data: dict, p: dict) -> dict:
    year = int(p.get('year') or date.today().year)
    for row in p.get('rows') or []:
        upsert_krizmanik(data, {
            'year': year,
            'name': row.get('Ime') or row.get('name') or row.get('Ime i prezime') or '—',
            'birthDate': row.get('Datum rođenja') or row.get('birthDate') or '',
            'school': row.get('Škola') or row.get('school') or '',
            'class': row.get('Razred') or row.get('class') or '',
            'group': row.get('Grupa') or row.get('group') or 'A',
            'baptized': row.get('Krštenje') or row.get('baptized') or '',
            'sponsor': row.get('Kum') or row.get('sponsor') or '',
            'status': row.get('Status') or 'upis',
            'oib': row.get('OIB') or '',
        })
    return {'ok': True, 'count': len(p.get('rows') or [])}


HANDLERS = {
    'create_intention': create_intention,
    'update_intention': update_intention,
    'delete_intention': delete_intention,
    'mark_intention_paid': mark_intention_paid,
    'toggle_intention_paid': toggle_intention_paid,
    'create_family': create_family,
    'update_family': update_family,
    'delete_family': delete_family,
    'upsert_family_member': upsert_family_member,
    'delete_family_member': delete_family_member,
    'upsert_contribution': upsert_contribution,
    'delete_contribution': delete_contribution,
    'update_spouse': update_spouse,
    'upsert_relative': upsert_relative,
    'delete_relative': delete_relative,
    'update_family_notes': update_family_notes,
    'upsert_street': upsert_street,
    'delete_street': delete_street,
    'upsert_sacrament': upsert_sacrament,
    'delete_sacrament': delete_sacrament_record,
    'upsert_task': upsert_task,
    'delete_task': delete_task,
    'toggle_task': toggle_task,
    'create_krizma_year': create_krizma_year,
    'update_krizma_group': update_krizma_group,
    'upsert_krizmanik': upsert_krizmanik,
    'delete_krizmanik': delete_krizmanik,
    'create_fc_year': create_fc_year,
    'upsert_prvopricestnik': upsert_prvopricestnik,
    'delete_prvopricestnik': delete_prvopricestnik,
    'upsert_parish_debt': upsert_parish_debt,
    'delete_parish_debt': delete_parish_debt,
    'mark_debt_paid': mark_debt_paid,
    'upsert_mass_schedule': upsert_mass_schedule,
    'delete_mass_schedule': delete_mass_schedule,
    'upsert_mass_exception': upsert_mass_exception,
    'delete_mass_exception': delete_mass_exception,
    'save_listic_layout': save_listic_layout,
    'reset_listic_layout': reset_listic_layout,
    'upsert_listic_issue': upsert_listic_issue,
    'delete_listic_issue': delete_listic_issue,
    'render_listic_preview': render_listic_preview,
    'get_analytics_stats': get_analytics_stats,
    'get_reminders': get_reminders,
    'build_bulletin_html': build_bulletin_html,
    'list_document_templates': list_document_templates,
    'load_document_templates': load_document_templates,
    'merge_document_template': merge_document_template,
    'search_matica': search_matica,
    'get_masses_for_date': get_masses_for_date,
    'upsert_visit': upsert_visit,
    'toggle_visit_done': toggle_visit_done,
    'upsert_invoice': upsert_invoice,
    'mark_invoice_paid': mark_invoice_paid,
    'create_cashbook_entry': create_cashbook_entry,
    'upsert_app_group': upsert_app_group,
    'upsert_app_user': upsert_app_user,
    'upsert_parish_priest': upsert_parish_priest,
    'send_staff_message': send_staff_message,
    'delete_staff_message': delete_staff_message,
    'mark_staff_message_read': mark_staff_message_read,
    'toggle_prep_checklist': toggle_prep_checklist,
    'mark_public_submission_imported': mark_public_submission_imported,
    'import_public_submission': import_public_submission,
    'import_krizmanici': import_krizmanici,
}


READONLY_ACTIONS = frozenset({
    'render_listic_preview',
    'get_analytics_stats',
    'get_reminders',
    'build_bulletin_html',
    'list_document_templates',
    'load_document_templates',
    'merge_document_template',
    'search_matica',
    'get_masses_for_date',
})

SETTINGS_AWARE_ACTIONS = READONLY_ACTIONS | frozenset({'upsert_listic_issue'})


def dispatch_action(action: str, payload: dict, svc) -> dict:
    handler = HANDLERS.get(action)
    if not handler:
        return {'ok': False, 'error': 'unknown_action', 'action': action}
    data = svc.load()
    normalize_data(data)
    settings = svc.load_settings()
    if action in SETTINGS_AWARE_ACTIONS:
        result = handler(data, payload or {}, settings)
    else:
        result = handler(data, payload or {})
    if action in READONLY_ACTIONS:
        return result if isinstance(result, dict) else {'ok': True}
    if not result.get('ok', True):
        return result
    svc.save(data)
    return {'ok': True, 'data': svc.load(), **{k: v for k, v in result.items() if k not in ('ok',)}}
