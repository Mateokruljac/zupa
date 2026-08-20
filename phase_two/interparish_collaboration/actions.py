"""POST akcije faze 2 za međužupnu suradnju."""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from django.contrib import messages

from phase_two.forms import InterparishRequestForm
from phase_two.interparish_collaboration.services import default_checklist

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


def _current_actor_name(request) -> str:
    return (
        getattr(request.user, 'name', '')
        or getattr(request.user, 'email', '')
        or 'Župni ured'
    )


def _find_interparish_request(
    parish_data: dict,
    request_id: str,
) -> dict | None:
    return next(
        (
            interparish_request
            for interparish_request in parish_data.get(
                'interparishRequests',
                [],
            )
            if interparish_request.get('id') == request_id
        ),
        None,
    )


def _next_interparish_reference_number(interparish_requests: list[dict]) -> int:
    existing_reference_numbers = [
        int(
            str(interparish_request.get('reference', '')).rsplit('-', 1)[-1]
        )
        for interparish_request in interparish_requests
        if str(interparish_request.get('reference', '')).rsplit(
            '-',
            1,
        )[-1].isdigit()
    ]
    return max(existing_reference_numbers or [0]) + 1


def handle_deanery_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
    if page_slug != 'dekanat':
        return False

    if action_name == 'create_interparish_request':
        parish_settings = parish_data_service.load_settings()
        active_parish_id = (
            parish_settings.get('_parishId') or 'bdm-slavonski-brod'
        )
        interparish_request_form = InterparishRequestForm(
            request.POST,
            parishes=parish_data.get('parishDirectory', []),
            active_parish_id=active_parish_id,
        )
        if interparish_request_form.is_valid():
            cleaned_data = interparish_request_form.cleaned_data
            interparish_requests = parish_data.setdefault(
                'interparishRequests',
                [],
            )
            reference_number = _next_interparish_reference_number(
                interparish_requests
            )
            timestamp = datetime.now().astimezone().isoformat(
                timespec='seconds'
            )
            actor_name = _current_actor_name(request)
            interparish_requests.append({
                'id': f'ipr-{date.today().year}-{reference_number:04d}',
                'reference': f'DZ-{date.today().year}-{reference_number:04d}',
                'type': cleaned_data['request_type'],
                'subject': cleaned_data['subject'],
                'personName': cleaned_data.get('person_name') or '',
                'caseReference': cleaned_data.get('case_reference') or '',
                'sourceParishId': active_parish_id,
                'targetParishId': cleaned_data['target_parish'],
                'direction': 'outgoing',
                'status': 'sent',
                'priority': cleaned_data['priority'],
                'confidentiality': cleaned_data['confidentiality'],
                'dueAt': cleaned_data['due_date'].isoformat(),
                'createdAt': timestamp,
                'updatedAt': timestamp,
                'requestedBy': actor_name,
                'assignedTo': '',
                'description': cleaned_data['description'],
                'requiredDocuments': default_checklist(
                    cleaned_data['request_type']
                ),
                'attachments': [],
                'timeline': [{
                    'at': timestamp,
                    'kind': 'sent',
                    'actor': actor_name,
                    'text': 'Zahtjev izrađen i poslan odabranoj župi.',
                }],
            })
            parish_data_service.save(parish_data)
            messages.success(
                request,
                'Međužupni zahtjev sigurno je evidentiran i poslan.',
            )
        else:
            messages.error(
                request,
                'Provjerite podatke međužupnog zahtjeva.',
            )
        return True

    if action_name == 'update_interparish_status':
        request_id = request.POST.get('request_id', '')
        next_status = request.POST.get('status', '')
        allowed_statuses = {
            'received',
            'in_review',
            'needs_info',
            'approved',
            'rejected',
            'completed',
            'closed',
        }
        interparish_request = _find_interparish_request(
            parish_data,
            request_id,
        )
        if interparish_request and next_status in allowed_statuses:
            timestamp = datetime.now().astimezone().isoformat(
                timespec='seconds'
            )
            actor_name = _current_actor_name(request)
            interparish_request['status'] = next_status
            interparish_request['updatedAt'] = timestamp
            interparish_request.setdefault('timeline', []).append({
                'at': timestamp,
                'kind': 'status',
                'actor': actor_name,
                'text': (
                    request.POST.get('note')
                    or f'Status promijenjen u {next_status}.'
                ),
            })
            parish_data_service.save(parish_data)
            messages.success(request, 'Status predmeta je ažuriran.')
        else:
            messages.error(request, 'Predmet ili status nije valjan.')
        return True

    if action_name == 'toggle_interparish_checklist':
        request_id = request.POST.get('request_id', '')
        try:
            checklist_index = int(
                request.POST.get('checklist_index', '-1')
            )
        except ValueError:
            checklist_index = -1
        interparish_request = _find_interparish_request(
            parish_data,
            request_id,
        )
        checklist = (
            interparish_request.get('requiredDocuments', [])
            if interparish_request
            else []
        )
        if 0 <= checklist_index < len(checklist):
            checklist_item = checklist[checklist_index]
            checklist_item['done'] = not checklist_item.get('done')
            interparish_request['updatedAt'] = (
                datetime.now().astimezone().isoformat(timespec='seconds')
            )
            parish_data_service.save(parish_data)
            messages.success(request, 'Kontrolna lista je ažurirana.')
        return True

    if action_name == 'add_interparish_message':
        request_id = request.POST.get('request_id', '')
        message_text = (request.POST.get('message') or '').strip()
        interparish_request = _find_interparish_request(
            parish_data,
            request_id,
        )
        if interparish_request and message_text:
            timestamp = datetime.now().astimezone().isoformat(
                timespec='seconds'
            )
            actor_name = _current_actor_name(request)
            interparish_request['updatedAt'] = timestamp
            interparish_request.setdefault('timeline', []).append({
                'at': timestamp,
                'kind': 'message',
                'actor': actor_name,
                'text': message_text,
            })
            parish_data_service.save(parish_data)
            messages.success(
                request,
                'Poruka je dodana u sigurni trag predmeta.',
            )
        return True

    return False
