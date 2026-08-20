"""Kontekst faze 2 za međužupnu suradnju."""
from __future__ import annotations

import copy
from datetime import date, datetime, timedelta

from pastoral.services.dates import parse_iso_date


REQUEST_TYPES = {
    'marriage_certificate': {
        'label': 'Potvrda za ženidbeni postupak',
        'short': 'Ženidba',
        'icon': '♥',
        'team': 'Isprave i matice',
        'defaultDays': 3,
    },
    'baptism_certificate': {
        'label': 'Krsni list / potvrda krštenja',
        'short': 'Krštenje',
        'icon': '✦',
        'team': 'Isprave i matice',
        'defaultDays': 3,
    },
    'marriage_delegation': {
        'label': 'Delegacija za ženidbu',
        'short': 'Delegacija',
        'icon': '⌁',
        'team': 'Župnik',
        'defaultDays': 4,
    },
    'priest_substitution': {
        'label': 'Zamjena svećenika',
        'short': 'Zamjena',
        'icon': '◎',
        'team': 'Svećenici',
        'defaultDays': 1,
    },
    'mass_intention_transfer': {
        'label': 'Prijenos misnih nakana',
        'short': 'Nakane',
        'icon': '☩',
        'team': 'Liturgija',
        'defaultDays': 7,
    },
    'sacrament_record_check': {
        'label': 'Provjera sakramentalnog zapisa',
        'short': 'Provjera matice',
        'icon': '▤',
        'team': 'Isprave i matice',
        'defaultDays': 5,
    },
    'pastoral_handover': {
        'label': 'Pastoralna primopredaja',
        'short': 'Primopredaja',
        'icon': '⇄',
        'team': 'Pastoral',
        'defaultDays': 5,
    },
}

STATUS_TYPES = {
    'draft': {'label': 'Skica', 'tone': 'muted'},
    'sent': {'label': 'Poslano', 'tone': 'info'},
    'received': {'label': 'Novo', 'tone': 'urgent'},
    'in_review': {'label': 'U obradi', 'tone': 'progress'},
    'needs_info': {'label': 'Čeka dopunu', 'tone': 'warning'},
    'approved': {'label': 'Odobreno', 'tone': 'success'},
    'rejected': {'label': 'Odbijeno', 'tone': 'danger'},
    'completed': {'label': 'Dovršeno', 'tone': 'success'},
    'closed': {'label': 'Zatvoreno', 'tone': 'muted'},
}

OPEN_STATUSES = frozenset({'sent', 'received', 'in_review', 'needs_info', 'approved'})
ACTION_STATUSES = frozenset({'received', 'needs_info'})


def default_due_date(request_type: str) -> date:
    days = REQUEST_TYPES.get(request_type, {}).get('defaultDays', 5)
    return date.today() + timedelta(days=days)


def default_checklist(request_type: str) -> list[dict]:
    rows = {
        'marriage_certificate': (
            'Provjera upisa u matici', 'Provjera bilježaka', 'Potpis i pečat potvrde',
        ),
        'baptism_certificate': ('Pronaći upis u matici', 'Izdati noviji izvadak s bilješkama'),
        'marriage_delegation': ('Provjera nadležnosti', 'Potpis delegacije'),
        'mass_intention_transfer': ('Potvrda preuzimanja', 'Evidencija stipendija'),
        'sacrament_record_check': ('Provjera identiteta osobe', 'Provjera izvornog upisa'),
        'pastoral_handover': ('Potvrda primopredaje', 'Evidencija ovlaštenog primatelja'),
    }.get(request_type, ())
    return [{'label': label, 'done': False} for label in rows]


def _decorate(row: dict, directory: dict[str, dict], active_parish_id: str) -> dict:
    item = copy.deepcopy(row)
    source = directory.get(item.get('sourceParishId'), {})
    target = directory.get(item.get('targetParishId'), {})
    item['sourceParish'] = source
    item['targetParish'] = target
    item['direction'] = 'outgoing' if item.get('sourceParishId') == active_parish_id else 'incoming'
    item['counterparty'] = target if item['direction'] == 'outgoing' else source
    item['typeMeta'] = REQUEST_TYPES.get(item.get('type'), {
        'label': item.get('type') or 'Drugi zahtjev', 'short': 'Zahtjev', 'icon': '•', 'team': 'Župni ured',
    })
    item['statusMeta'] = STATUS_TYPES.get(item.get('status'), {'label': item.get('status') or '—', 'tone': 'muted'})
    due = parse_iso_date(item.get('dueAt'))
    item['isOverdue'] = bool(due and due < date.today() and item.get('status') in OPEN_STATUSES)
    item['daysLeft'] = (due - date.today()).days if due else None
    checklist = item.get('requiredDocuments') or []
    item['checklistDone'] = sum(1 for entry in checklist if entry.get('done'))
    item['checklistTotal'] = len(checklist)
    item['checklistPercent'] = round(item['checklistDone'] / len(checklist) * 100) if checklist else 100
    return item


def deanery_page_context(data: dict, request, settings: dict) -> dict:
    active_parish_id = settings.get('_parishId') or 'bdm-slavonski-brod'
    directory_rows = copy.deepcopy(data.get('parishDirectory') or [])
    directory = {row.get('id'): row for row in directory_rows}
    for parish in directory_rows:
        parish['isCurrent'] = parish.get('id') == active_parish_id

    requests = [
        _decorate(row, directory, active_parish_id)
        for row in data.get('interparishRequests') or []
    ]
    requests.sort(key=lambda row: row.get('updatedAt') or row.get('createdAt') or '', reverse=True)

    view = request.GET.get('view') or 'inbox'
    status = request.GET.get('status') or ''
    query = (request.GET.get('q') or '').strip().lower()
    filtered = requests
    if view == 'inbox':
        filtered = [row for row in filtered if row.get('direction') == 'incoming' and row.get('status') in OPEN_STATUSES]
    elif view == 'outbox':
        filtered = [row for row in filtered if row.get('direction') == 'outgoing']
    elif view == 'closed':
        filtered = [row for row in filtered if row.get('status') in {'completed', 'closed', 'rejected'}]
    if status:
        filtered = [row for row in filtered if row.get('status') == status]
    if query:
        filtered = [
            row for row in filtered
            if query in ' '.join((
                row.get('reference', ''), row.get('subject', ''), row.get('personName', ''),
                row.get('caseReference', ''), row.get('counterparty', {}).get('name', ''),
            )).lower()
        ]

    selected_id = request.GET.get('request') or (filtered[0].get('id') if filtered else '')
    selected = next((row for row in requests if row.get('id') == selected_id), None)

    today = date.today()
    first_week = today - timedelta(days=today.weekday())
    volume = []
    for weeks_back in range(5, -1, -1):
        start = first_week - timedelta(weeks=weeks_back)
        end = start + timedelta(days=7)
        volume.append({
            'label': f'{start.day}.{start.month}.',
            'count': sum(
                1 for row in requests
                if (created := parse_iso_date(row.get('createdAt'))) and start <= created < end
            ),
        })

    inbox_open = [row for row in requests if row['direction'] == 'incoming' and row.get('status') in OPEN_STATUSES]
    outbox_open = [row for row in requests if row['direction'] == 'outgoing' and row.get('status') in OPEN_STATUSES]
    workloads: dict[str, int] = {}
    for row in inbox_open:
        team = row['typeMeta'].get('team', 'Župni ured')
        workloads[team] = workloads.get(team, 0) + 1

    return {
        'deanery': data.get('deanery') or {},
        'parish_directory': directory_rows,
        'interparish_requests': filtered,
        'selected_request': selected,
        'deanery_filters': {'view': view, 'status': status, 'q': request.GET.get('q') or ''},
        'request_type_meta': REQUEST_TYPES,
        'request_status_meta': STATUS_TYPES,
        'deanery_stats': {
            'inbox': len(inbox_open),
            'action': sum(1 for row in inbox_open if row.get('status') in ACTION_STATUSES),
            'outbox': len(outbox_open),
            'overdue': sum(1 for row in requests if row.get('isOverdue')),
            'urgent': sum(1 for row in inbox_open if row.get('priority') in {'urgent', 'high'}),
            'parishes': len(directory_rows),
            'averageResponseHours': round(
                sum(row.get('responseHours', 0) for row in directory_rows) / len(directory_rows)
            ) if directory_rows else 0,
        },
        'deanery_workloads': [
            {'label': label, 'count': count} for label, count in sorted(workloads.items(), key=lambda item: -item[1])
        ],
        'deanery_volume': volume,
        'today': today.isoformat(),
    }
