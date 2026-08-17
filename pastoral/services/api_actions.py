"""Kompatibilna fasada API akcija koje koristi `/api/action/` endpoint.

Nove domenske mutacije pripadaju paketu ``api_action_handlers``. Ovaj modul
zadržava stabilne importe i registar akcija dok se preostale domene postupno
izdvajaju bez promjene javnog JSON ugovora.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from pastoral.services.dates import today_iso
from pastoral.services.api_action_handlers.families import (
    create_family,
    delete_contribution,
    delete_family,
    delete_family_member,
    delete_relative,
    update_family,
    update_family_notes,
    update_spouse,
    upsert_contribution,
    upsert_family_member,
    upsert_relative,
)
from pastoral.services.api_action_handlers.intentions import (
    create_intention,
    delete_intention,
    mark_intention_paid,
    toggle_intention_paid,
    update_intention,
)
from pastoral.services.api_action_handlers.formation import (
    create_confirmation_year,
    create_first_communion_year,
    delete_confirmation_candidate,
    delete_first_communion_candidate,
    update_confirmation_group,
    upsert_confirmation_candidate,
    upsert_first_communion_candidate,
)
from pastoral.services.api_action_handlers.shared import (
    find_family,
    generate_record_identifier,
    normalize_date_value,
    normalize_parish_data,
)
from pastoral.services.api_action_handlers.streets import (
    delete_street,
    upsert_street,
)

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService

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
    item = {'id': generate_record_identifier(prefix), **fields}
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
        'due': normalize_date_value(p.get('due')),
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
    item = {'id': generate_record_identifier('t'), **payload}
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


# --- Parish debts ---

def upsert_parish_debt(data: dict, p: dict) -> dict:
    payload = {
        'direction': p.get('direction') or 'payable',
        'label': (p.get('label') or '').strip(),
        'category': p.get('category') or 'ostalo',
        'year': int(p.get('year') or date.today().year),
        'amount': float(p.get('amount') or 0),
        'dueDate': normalize_date_value(p.get('due_date') or p.get('dueDate')),
        'contact': (p.get('contact') or '').strip(),
        'notes': (p.get('notes') or '').strip(),
        'paid': bool(p.get('paid')),
        'paidAt': normalize_date_value(p.get('paid_at') or p.get('paidAt')),
    }
    if not payload['label']:
        return {'ok': False, 'error': 'label_required'}
    if payload['paid'] and not payload['paidAt']:
        payload['paidAt'] = today_iso()
    did = p.get('id')
    if did:
        row = next((d for d in data.get('parishDebts', []) if d.get('id') == did), None)
        if not row:
            return {'ok': False, 'error': 'not_found'}
        row.update(payload)
        return {'ok': True, 'item': row}
    item = {'id': generate_record_identifier('pd'), **payload}
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
        'id': generate_record_identifier('msl'),
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
    item = {'id': generate_record_identifier('ms'), **fields}
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
    item = {'id': generate_record_identifier('mexc'), **fields}
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
    iso = p.get('date') or p.get('iso') or today_iso()
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
            fam = find_family(data, row['familyId'])
            if fam:
                fam['lastVisit'] = today_iso()
        return {'ok': True, 'item': row}
    item = {'id': generate_record_identifier('v'), 'done': False, **payload}
    data.setdefault('visits', []).append(item)
    return {'ok': True, 'item': item}


def toggle_visit_done(data: dict, p: dict) -> dict:
    row = next((v for v in data.get('visits', []) if v.get('id') == p.get('id')), None)
    if not row:
        return {'ok': False, 'error': 'not_found'}
    row['done'] = not row.get('done')
    if row['done'] and row.get('familyId'):
        fam = find_family(data, row['familyId'])
        if fam:
            fam['lastVisit'] = today_iso()
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
    item = {'id': generate_record_identifier('inv'), 'direction': 'incoming', **fields}
    data.setdefault('invoices', []).append(item)
    return {'ok': True, 'item': item}


def mark_invoice_paid(data: dict, p: dict) -> dict:
    row = next((x for x in data.get('invoices', []) if x.get('id') == p.get('id')), None)
    if not row:
        return {'ok': False, 'error': 'not_found'}
    row['paidAmount'] = row.get('total') or row.get('amount')
    row['paidAt'] = today_iso()
    row['status'] = 'placen'
    return {'ok': True, 'item': row}


# --- Cashbook ---

def create_cashbook_entry(data: dict, p: dict) -> dict:
    fields = dict(p.get('fields') or p)
    item = {'id': generate_record_identifier('cb'), **fields}
    data.setdefault('cashbook', []).insert(0, item)
    extra = p.get('auto_entries') or []
    for e in extra:
        data['cashbook'].insert(0, {'id': generate_record_identifier('cb'), **e})
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
    item = {'id': fields.get('id') or generate_record_identifier('grp'), **fields}
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
        item = {'id': generate_record_identifier('usr'), **fields}
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
    item = {'id': generate_record_identifier('pr'), **fields}
    data.setdefault('parishPriests', []).append(item)
    return {'ok': True, 'item': item}


# --- Staff messages ---

def send_staff_message(data: dict, p: dict) -> dict:
    item = {
        'id': generate_record_identifier('msg'),
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
    stype = {
        'prijava-krizma': 'krizma',
        'prijava-krsenje': 'krstenje',
        'prijava-pricest': 'pricest',
        'prijava-ukop': 'ukop',
    }.get(stype, stype)
    d = sub.get('data') or {}
    year = int(p.get('year') or date.today().year)
    sid = sub.get('id')

    if stype == 'krizma':
        upsert_confirmation_candidate(data, {
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
        upsert_first_communion_candidate(data, {
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
        upsert_confirmation_candidate(data, {
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


ACTION_HANDLERS = {
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
    'create_krizma_year': create_confirmation_year,
    'update_krizma_group': update_confirmation_group,
    'upsert_krizmanik': upsert_confirmation_candidate,
    'delete_krizmanik': delete_confirmation_candidate,
    'create_fc_year': create_first_communion_year,
    'upsert_prvopricestnik': upsert_first_communion_candidate,
    'delete_prvopricestnik': delete_first_communion_candidate,
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


READ_ONLY_ACTION_NAMES = frozenset({
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

SETTINGS_AWARE_ACTION_NAMES = READ_ONLY_ACTION_NAMES | frozenset({
    'upsert_listic_issue',
})


def dispatch_action(
    action_name: str,
    action_payload: dict,
    parish_data_service: ParishDataService,
) -> dict:
    action_handler = ACTION_HANDLERS.get(action_name)
    if not action_handler:
        return {
            'ok': False,
            'error': 'unknown_action',
            'action': action_name,
        }

    parish_data = parish_data_service.load()
    normalize_parish_data(parish_data)
    parish_settings = parish_data_service.load_settings()
    if action_name in SETTINGS_AWARE_ACTION_NAMES:
        action_result = action_handler(
            parish_data,
            action_payload or {},
            parish_settings,
        )
    else:
        action_result = action_handler(parish_data, action_payload or {})

    if action_name in READ_ONLY_ACTION_NAMES:
        return action_result if isinstance(action_result, dict) else {'ok': True}
    if not action_result.get('ok', True):
        return action_result

    parish_data_service.save(parish_data)
    additional_response_data = {
        response_key: response_value
        for response_key, response_value in action_result.items()
        if response_key != 'ok'
    }
    return {
        'ok': True,
        'data': parish_data_service.load(),
        **additional_response_data,
    }
