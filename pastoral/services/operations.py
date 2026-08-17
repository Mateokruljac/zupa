"""Operativno središte župe — jedinstveni pogled na ured, ljude i imovinu."""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta

from pastoral.services.dates import parse_iso_date


OPEN_STATUSES = frozenset({
    'new', 'open', 'in_progress', 'waiting', 'pending', 'planned', 'scheduled',
    'due', 'draft', 'review', 'gap',
})
DONE_STATUSES = frozenset({'completed', 'closed', 'approved', 'sent', 'ready', 'resolved'})

CATEGORY_META = {
    'correspondence': {'label': 'Uredska pošta', 'short': 'Pošta', 'icon': '✉', 'tone': 'blue'},
    'approval': {'label': 'Odobrenja', 'short': 'Odobrenje', 'icon': '✓', 'tone': 'gold'},
    'communication': {'label': 'Komunikacija', 'short': 'Komunikacija', 'icon': '◌', 'tone': 'violet'},
    'facility': {'label': 'Imovina i održavanje', 'short': 'Imovina', 'icon': '⌂', 'tone': 'rose'},
    'compliance': {'label': 'Kontrole i sigurnost', 'short': 'Kontrola', 'icon': '⌁', 'tone': 'green'},
    'rota': {'label': 'Službe i volonteri', 'short': 'Raspored', 'icon': '◎', 'tone': 'teal'},
    'room': {'label': 'Prostori i termini', 'short': 'Prostor', 'icon': '▦', 'tone': 'orange'},
}

STATUS_META = {
    'new': {'label': 'Novo', 'tone': 'urgent'},
    'open': {'label': 'Otvoreno', 'tone': 'info'},
    'in_progress': {'label': 'U obradi', 'tone': 'progress'},
    'waiting': {'label': 'Čeka odgovor', 'tone': 'warning'},
    'pending': {'label': 'Čeka odluku', 'tone': 'warning'},
    'planned': {'label': 'Planirano', 'tone': 'muted'},
    'scheduled': {'label': 'Zakazano', 'tone': 'info'},
    'due': {'label': 'Dospijeva', 'tone': 'urgent'},
    'draft': {'label': 'Skica', 'tone': 'muted'},
    'review': {'label': 'Za pregled', 'tone': 'warning'},
    'gap': {'label': 'Nedostaje osoba', 'tone': 'urgent'},
    'completed': {'label': 'Dovršeno', 'tone': 'success'},
    'closed': {'label': 'Zatvoreno', 'tone': 'muted'},
    'approved': {'label': 'Odobreno', 'tone': 'success'},
    'sent': {'label': 'Poslano', 'tone': 'success'},
    'ready': {'label': 'Spremno', 'tone': 'success'},
    'resolved': {'label': 'Riješeno', 'tone': 'success'},
}


def _is_open(status: str) -> bool:
    return status not in DONE_STATUSES


def _decorate(
    row: dict,
    *,
    category: str,
    collection: str,
    title_key: str = 'title',
    due_key: str = 'dueAt',
    meta: str = '',
    next_action: str = '',
) -> dict:
    today = date.today()
    due = parse_iso_date(row.get(due_key))
    status = row.get('status') or 'open'
    priority = row.get('priority') or ('high' if row.get('risk') == 'high' else 'normal')
    item_id = f"{category}:{row.get('id', '')}"
    return {
        **row,
        'itemId': item_id,
        'sourceId': row.get('id', ''),
        'collection': collection,
        'category': category,
        'categoryMeta': CATEGORY_META[category],
        'statusMeta': STATUS_META.get(status, {'label': status.replace('_', ' ').title(), 'tone': 'muted'}),
        'title': row.get(title_key) or 'Neimenovana stavka',
        'meta': meta,
        'due': due.isoformat() if due else '',
        'isOpen': _is_open(status),
        'isOverdue': bool(due and due < today and _is_open(status)),
        'isDueToday': bool(due and due == today and _is_open(status)),
        'daysLeft': (due - today).days if due else None,
        'priority': priority,
        'nextAction': next_action or row.get('nextAction') or '',
        'displaySource': row.get('contact') or row.get('requestedBy') or row.get('facility') or '—',
        'detailText': row.get('note') or row.get('message') or '',
    }


def build_work_queue(data: dict) -> list[dict]:
    items: list[dict] = []

    for row in data.get('officeCorrespondence', []):
        items.append(_decorate(
            row,
            category='correspondence',
            collection='officeCorrespondence',
            title_key='subject',
            meta=f"{row.get('reference', '')} · {row.get('contact', '')}".strip(' ·'),
        ))

    for row in data.get('officeApprovals', []):
        amount = float(row.get('amount') or 0)
        amount_meta = f" · {amount:,.2f} €" if amount else ''
        items.append(_decorate(
            row,
            category='approval',
            collection='officeApprovals',
            title_key='subject',
            meta=f"{row.get('requestedBy', '')}{amount_meta}",
        ))

    for row in data.get('communications', []):
        items.append(_decorate(
            row,
            category='communication',
            collection='communications',
            due_key='scheduledAt',
            meta=f"{row.get('audience', '')} · {row.get('recipients', 0)} primatelja",
            next_action=(
                'Odobriti i zakazati slanje.' if row.get('requiresApproval') and row.get('status') == 'draft'
                else row.get('message', '')
            ),
        ))

    for row in data.get('facilityTasks', []):
        items.append(_decorate(
            row,
            category='facility',
            collection='facilityTasks',
            meta=f"{row.get('facility', '')} · {row.get('supplier', '')}".strip(' ·'),
        ))

    for row in data.get('complianceControls', []):
        items.append(_decorate(
            row,
            category='compliance',
            collection='complianceControls',
            meta=f"{row.get('area', '')} · dokaz: {row.get('evidence', '')}".strip(' ·'),
            next_action=f"Prikupiti dokaz: {row.get('evidence', '')}",
        ))

    for row in data.get('serviceRota', []):
        if row.get('status') != 'gap':
            continue
        items.append(_decorate(
            row,
            category='rota',
            collection='serviceRota',
            due_key='date',
            title_key='celebration',
            meta=f"{row.get('date', '')} {row.get('time', '')} · {row.get('place', '')}",
            next_action=f"Popuniti: {', '.join(row.get('missingRoles') or [])}",
        ))

    for row in data.get('roomBookings', []):
        if not row.get('conflict'):
            continue
        items.append(_decorate(
            row,
            category='room',
            collection='roomBookings',
            due_key='startsAt',
            title_key='purpose',
            meta=f"{row.get('resource', '')} · kolizija s: {row.get('conflictWith', '')}",
            next_action='Premjestiti jedan termin ili potvrditi drugi prostor.',
        ))

    priority_rank = {'urgent': 0, 'high': 1, 'normal': 2, 'low': 3}
    items.sort(key=lambda item: (
        0 if item['isOverdue'] else 1 if item['isDueToday'] else 2,
        priority_rank.get(item.get('priority'), 9),
        item.get('due') or '9999-12-31',
        item.get('title') or '',
    ))
    return items


def _filter_queue(items: list[dict], request) -> tuple[list[dict], dict]:
    view = request.GET.get('view', 'attention')
    query = (request.GET.get('q') or '').strip().lower()
    allowed_views = {'attention', 'today', 'inbox', 'approvals', 'facilities', 'people', 'compliance', 'all', 'closed'}
    if view not in allowed_views:
        view = 'attention'

    def matches(item: dict) -> bool:
        if query:
            blob = ' '.join(str(item.get(key, '')) for key in (
                'title', 'meta', 'owner', 'contact', 'reference', 'nextAction', 'linkedCase',
            )).lower()
            if query not in blob:
                return False
        if view == 'today':
            return item['isDueToday'] or item['isOverdue']
        if view == 'inbox':
            return item['category'] in {'correspondence', 'communication'} and item['isOpen']
        if view == 'approvals':
            return item['category'] == 'approval' and item['isOpen']
        if view == 'facilities':
            return item['category'] in {'facility', 'room'} and item['isOpen']
        if view == 'people':
            return item['category'] == 'rota' and item['isOpen']
        if view == 'compliance':
            return item['category'] == 'compliance' and item['isOpen']
        if view == 'closed':
            return not item['isOpen']
        if view == 'all':
            return True
        return item['isOpen'] and (
            item['isOverdue'] or item['isDueToday'] or item.get('priority') in {'urgent', 'high'}
            or item['category'] in {'approval', 'rota', 'room'}
        )

    return [item for item in items if matches(item)], {'view': view, 'q': query}


def _pastoral_radar(data: dict) -> list[dict]:
    today = date.today()
    radar: list[dict] = []

    for family in data.get('families', []):
        notes = (family.get('pastoralNotes') or '').lower()
        last_visit = parse_iso_date(family.get('lastVisit'))
        days = (today - last_visit).days if last_visit else None
        if 'pričest' in notes and (days is None or days > 28):
            radar.append({
                'icon': '☩', 'tone': 'rose', 'label': 'Redovita pastoralna skrb',
                'title': f"Provjeriti termin kućne pričesti — {family.get('surname', '')}",
                'sub': f"Zadnji evidentirani posjet prije {days} dana" if days is not None else 'Nema evidentiranog posjeta',
                'page': 'obitelji', 'query': f"family={family.get('id', '')}",
                'why': 'Prijedlog proizlazi iz pastoralne bilješke i datuma zadnjeg posjeta.',
            })
        elif family.get('status') == 'aktivna' and not last_visit:
            radar.append({
                'icon': '⌂', 'tone': 'blue', 'label': 'Pastoralna pokrivenost',
                'title': f"Obitelj {family.get('surname', '')} još nema zabilježen posjet",
                'sub': family.get('address') or 'Adresa nije unesena',
                'page': 'obitelji', 'query': f"family={family.get('id', '')}",
                'why': 'Ne procjenjuje vjeru ni angažman; pokazuje samo nedostatak uredske evidencije posjeta.',
            })

    for baptism in data.get('baptisms', []):
        event_date = parse_iso_date(baptism.get('baptismDate'))
        if event_date and today <= event_date <= today + timedelta(days=21) and not baptism.get('godparentCertReceived'):
            radar.append({
                'icon': '✦', 'tone': 'gold', 'label': 'Sakramentalna priprava',
                'title': f"Nedostaje potvrda kuma — {baptism.get('childName', '')}",
                'sub': f"Krštenje {event_date.strftime('%d.%m.%Y.')}",
                'page': 'krsenja', 'query': '',
                'why': 'Provjera se temelji na roku slavlja i označenom nedostajućem dokumentu.',
            })

    for wedding in data.get('weddings', []):
        event_date = parse_iso_date(wedding.get('weddingDate'))
        if event_date and today <= event_date <= today + timedelta(days=45) and not wedding.get('documentsOk'):
            radar.append({
                'icon': '♥', 'tone': 'violet', 'label': 'Ženidbeni predmet',
                'title': f"Dokumentacija još nije potpuna — {wedding.get('couple', '')}",
                'sub': f"Vjenčanje {event_date.strftime('%d.%m.%Y.')}",
                'page': 'vjencanja', 'query': '',
                'why': 'Provjera se temelji na statusu dokumentacije i dogovorenom datumu.',
            })

    return radar[:6]


def _data_health(data: dict) -> list[dict]:
    families = data.get('families', [])
    no_contact = sum(1 for family in families if not family.get('phone') and not family.get('email'))
    no_street = sum(1 for family in families if not family.get('streetId'))
    registry = data.get('registryBooks', [])
    stale_books = sum(1 for book in registry if not book.get('lastEntry'))
    return [
        {'label': 'Obitelji bez kontakta', 'value': no_contact, 'page': 'obitelji', 'tone': 'warning' if no_contact else 'success'},
        {'label': 'Obitelji bez povezane ulice', 'value': no_street, 'page': 'ulice', 'tone': 'warning' if no_street else 'success'},
        {'label': 'Matice bez zadnjeg upisa', 'value': stale_books, 'page': 'maticne-knjige', 'tone': 'warning' if stale_books else 'success'},
        {'label': 'Neobrađene javne prijave', 'value': sum(1 for row in data.get('publicSubmissions', []) if row.get('status') == 'nova'), 'page': 'javne-prijave', 'tone': 'warning'},
    ]


def operations_attention_count(data: dict) -> int:
    return sum(1 for item in build_work_queue(data) if item['isOpen'] and (
        item['isOverdue'] or item['isDueToday'] or item.get('priority') in {'urgent', 'high'}
        or item['category'] in {'approval', 'rota', 'room'}
    ))


def operations_page_context(data: dict, request) -> dict:
    all_items = build_work_queue(data)
    visible_items, filters = _filter_queue(all_items, request)
    selected_id = request.GET.get('item') or (visible_items[0]['itemId'] if visible_items else '')
    selected = next((item for item in all_items if item['itemId'] == selected_id), None)

    open_items = [item for item in all_items if item['isOpen']]
    rota = data.get('serviceRota', [])
    rota_total = sum(int(row.get('rolesTotal') or 0) for row in rota)
    rota_filled = sum(int(row.get('rolesFilled') or 0) for row in rota)
    compliance = data.get('complianceControls', [])
    compliance_ready = sum(1 for row in compliance if row.get('status') in DONE_STATUSES)

    category_counts = Counter(item['category'] for item in open_items)
    flow_chart = [
        {'label': CATEGORY_META[key]['short'], 'value': category_counts.get(key, 0)}
        for key in ('correspondence', 'approval', 'communication', 'facility', 'compliance', 'rota', 'room')
    ]

    channels = Counter()
    for row in data.get('communications', []):
        for channel in row.get('channels') or []:
            channels[channel] += int(row.get('recipients') or 0)

    return {
        'operations_queue': visible_items,
        'operations_all_queue': all_items,
        'operations_selected': selected,
        'operations_filters': filters,
        'operations_stats': {
            'open': len(open_items),
            'attention': operations_attention_count(data),
            'today': sum(1 for item in open_items if item['isDueToday']),
            'overdue': sum(1 for item in open_items if item['isOverdue']),
            'approvals': sum(1 for item in open_items if item['category'] == 'approval'),
            'facilityRisks': sum(1 for item in open_items if item['category'] == 'facility' and item.get('risk') == 'high'),
            'rotaPercent': round(rota_filled / rota_total * 100) if rota_total else 100,
            'compliancePercent': round(compliance_ready / len(compliance) * 100) if compliance else 100,
        },
        'operations_category_meta': CATEGORY_META,
        'operations_flow_chart': flow_chart,
        'operations_channel_chart': [
            {'label': label, 'value': value} for label, value in channels.most_common()
        ],
        'operations_appointments': sorted(data.get('officeAppointments', []), key=lambda row: (row.get('date', ''), row.get('time', '')))[:6],
        'operations_bookings': sorted(data.get('roomBookings', []), key=lambda row: row.get('startsAt', ''))[:6],
        'operations_communications': sorted(data.get('communications', []), key=lambda row: row.get('scheduledAt', ''), reverse=True)[:5],
        'operations_facilities': sorted(data.get('facilityTasks', []), key=lambda row: row.get('dueAt', ''))[:5],
        'operations_rota': sorted(rota, key=lambda row: (row.get('date', ''), row.get('time', '')))[:5],
        'operations_compliance': sorted(compliance, key=lambda row: row.get('dueAt', ''))[:6],
        'operations_contracts': sorted(data.get('parishContracts', []), key=lambda row: row.get('renewalAt', ''))[:5],
        'operations_handover': data.get('handoverChecklist', []),
        'pastoral_radar': _pastoral_radar(data),
        'data_health': _data_health(data),
        'generated_at': datetime.now().astimezone().isoformat(timespec='minutes'),
    }
