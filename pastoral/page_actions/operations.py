"""POST akcije operativnog središta župnog ureda."""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
import uuid

from django.contrib import messages

from pastoral.forms import (
    CommunicationPlanForm,
    FacilityIssueForm,
    OfficeEntryForm,
)

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


def handle_operations_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
    if page_slug != 'operativno-srediste':
        return False

    if action_name == 'create_office_entry':
        office_entry_form = OfficeEntryForm(request.POST)
        if office_entry_form.is_valid():
            cleaned_data = office_entry_form.cleaned_data
            office_entries = parish_data.setdefault(
                'officeCorrespondence',
                [],
            )
            timestamp = datetime.now().astimezone().isoformat(
                timespec='seconds'
            )
            direction_mark = (
                'I' if cleaned_data['direction'] == 'incoming' else 'II'
            )
            reference_number = len(office_entries) + 139
            office_entries.append({
                'id': f"cor-{date.today().year}-{uuid.uuid4().hex[:8]}",
                'reference': (
                    f"UP/{direction_mark}-{date.today().year}-"
                    f"{reference_number:04d}"
                ),
                'direction': cleaned_data['direction'],
                'channel': cleaned_data['channel'],
                'subject': cleaned_data['subject'],
                'contact': cleaned_data.get('contact') or '',
                'receivedAt': timestamp,
                'dueAt': (
                    cleaned_data['due_date'].isoformat()
                    if cleaned_data.get('due_date')
                    else ''
                ),
                'owner': cleaned_data.get('owner') or 'Župni ured',
                'status': (
                    'new'
                    if cleaned_data['direction'] == 'incoming'
                    else 'open'
                ),
                'priority': cleaned_data['priority'],
                'confidentiality': cleaned_data['confidentiality'],
                'linkedCase': cleaned_data.get('linked_case') or '',
                'nextAction': cleaned_data.get('note') or '',
                'note': cleaned_data.get('note') or '',
            })
            parish_data_service.save(parish_data)
            messages.success(
                request,
                'Uredski zapis je evidentiran i dobio je urudžbenu oznaku.',
            )
        else:
            messages.error(request, 'Provjerite podatke uredskog zapisa.')
        return True

    if action_name == 'create_facility_issue':
        facility_issue_form = FacilityIssueForm(request.POST)
        if facility_issue_form.is_valid():
            cleaned_data = facility_issue_form.cleaned_data
            parish_data.setdefault('facilityTasks', []).append({
                'id': f"fac-{date.today().year}-{uuid.uuid4().hex[:8]}",
                'facility': cleaned_data['facility'],
                'title': cleaned_data['title'],
                'risk': cleaned_data['risk'],
                'reportedAt': date.today().isoformat(),
                'dueAt': (
                    cleaned_data['due_date'].isoformat()
                    if cleaned_data.get('due_date')
                    else ''
                ),
                'owner': cleaned_data.get('owner') or 'Župni ured',
                'supplier': cleaned_data.get('supplier') or '',
                'status': 'open',
                'estimatedCost': float(
                    cleaned_data.get('estimated_cost') or 0
                ),
                'nextAction': cleaned_data.get('description') or '',
                'assetId': '',
            })
            parish_data_service.save(parish_data)
            messages.success(
                request,
                'Zahtjev održavanja dodan je u jedinstveni radni red.',
            )
        else:
            messages.error(request, 'Provjerite podatke prijave održavanja.')
        return True

    if action_name == 'schedule_communication':
        communication_plan_form = CommunicationPlanForm(request.POST)
        if communication_plan_form.is_valid():
            cleaned_data = communication_plan_form.cleaned_data
            channel_names_by_value = {
                'email': ['e-mail'],
                'sms': ['SMS'],
                'email_sms': ['e-mail', 'SMS'],
                'app': ['aplikacija'],
                'web': ['web'],
                'print': ['tisak'],
            }
            scheduled_time = cleaned_data.get('scheduled_at')
            parish_data.setdefault('communications', []).append({
                'id': f"com-{date.today().year}-{uuid.uuid4().hex[:8]}",
                'title': cleaned_data['title'],
                'audience': cleaned_data['audience'],
                'channels': channel_names_by_value.get(
                    cleaned_data['channel'],
                    [cleaned_data['channel']],
                ),
                'scheduledAt': (
                    scheduled_time.astimezone().isoformat(timespec='seconds')
                    if scheduled_time
                    else ''
                ),
                'status': (
                    'draft'
                    if cleaned_data.get('requires_approval')
                    else 'scheduled'
                ),
                'recipients': 0,
                'delivered': 0,
                'owner': getattr(request.user, 'name', '') or 'Župni ured',
                'requiresApproval': bool(
                    cleaned_data.get('requires_approval')
                ),
                'message': cleaned_data['message'],
            })
            parish_data_service.save(parish_data)
            messages.success(
                request,
                'Komunikacija je spremljena kao plan; stvarno slanje još '
                'nije uključeno u demo.',
            )
        else:
            messages.error(request, 'Provjerite plan komunikacije.')
        return True

    if action_name == 'update_operation_status':
        collection_name = request.POST.get('collection', '')
        source_id = request.POST.get('source_id', '')
        next_status = request.POST.get('status', '')
        allowed_collections = {
            'officeCorrespondence',
            'officeApprovals',
            'communications',
            'facilityTasks',
            'complianceControls',
            'serviceRota',
            'roomBookings',
            'handoverChecklist',
        }
        allowed_statuses = {
            'new',
            'open',
            'in_progress',
            'waiting',
            'pending',
            'planned',
            'scheduled',
            'due',
            'draft',
            'review',
            'gap',
            'completed',
            'closed',
            'approved',
            'sent',
            'ready',
            'resolved',
        }
        operational_item = None
        if (
            collection_name in allowed_collections
            and next_status in allowed_statuses
        ):
            operational_item = next(
                (
                    item
                    for item in parish_data.get(collection_name, [])
                    if item.get('id') == source_id
                ),
                None,
            )
        if operational_item:
            operational_item['status'] = next_status
            operational_item['updatedAt'] = (
                datetime.now().astimezone().isoformat(timespec='seconds')
            )
            parish_data_service.save(parish_data)
            messages.success(
                request,
                'Status operativne stavke je ažuriran.',
            )
        else:
            messages.error(
                request,
                'Stavka ili promjena statusa nije valjana.',
            )
        return True

    return False
