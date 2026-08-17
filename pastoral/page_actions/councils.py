"""POST akcije za župno pastoralno i ekonomsko vijeće."""
from __future__ import annotations

from typing import TYPE_CHECKING
import uuid

from django.contrib import messages

from pastoral.forms import CouncilMeetingForm, CouncilMemberForm

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


COUNCIL_CONFIGURATION = {
    'pastoral': {
        'data_key': 'pastoralCouncil',
        'member_id_prefix': 'zpv',
        'next_meeting_key': 'nextMeeting',
        'label': 'Župno pastoralno vijeće',
    },
    'economic': {
        'data_key': 'economicCouncil',
        'member_id_prefix': 'zev',
        'next_meeting_key': 'nextReview',
        'label': 'Župno ekonomsko vijeće',
    },
}


def _council_configuration(council_type: str) -> dict | None:
    return COUNCIL_CONFIGURATION.get(council_type)


def _council_data(parish_data: dict, council_type: str) -> dict | None:
    council_configuration = _council_configuration(council_type)
    if not council_configuration:
        return None
    return parish_data.setdefault(council_configuration['data_key'], {})


def handle_council_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
    if page_slug != 'vijeca':
        return False

    if action_name == 'add_council_member':
        council_member_form = CouncilMemberForm(request.POST)
        if council_member_form.is_valid():
            cleaned_data = council_member_form.cleaned_data
            council_configuration = _council_configuration(
                cleaned_data['council_type']
            )
            council = _council_data(
                parish_data,
                cleaned_data['council_type'],
            )
            council.setdefault('members', []).append({
                'id': (
                    f"{council_configuration['member_id_prefix']}-"
                    f"{uuid.uuid4().hex[:8]}"
                ),
                'name': cleaned_data['name'],
                'role': cleaned_data['role'],
                'confirmed': cleaned_data['confirmed'],
            })
            parish_data_service.save(parish_data)
            messages.success(
                request,
                f"Član je dodan u {council_configuration['label']}.",
            )
        else:
            messages.error(request, 'Provjerite podatke novog člana vijeća.')
        return True

    if action_name == 'schedule_council_meeting':
        council_meeting_form = CouncilMeetingForm(request.POST)
        if council_meeting_form.is_valid():
            cleaned_data = council_meeting_form.cleaned_data
            council_configuration = _council_configuration(
                cleaned_data['council_type']
            )
            council = _council_data(
                parish_data,
                cleaned_data['council_type'],
            )
            council[council_configuration['next_meeting_key']] = (
                cleaned_data['meeting_date'].isoformat()
            )
            parish_data_service.save(parish_data)
            messages.success(
                request,
                f"Sljedeći termin za {council_configuration['label']} je spremljen.",
            )
        else:
            messages.error(request, 'Provjerite datum i odabrano vijeće.')
        return True

    if action_name == 'toggle_council_member_confirmation':
        council_type = request.POST.get('council_type', '')
        council_member_id = request.POST.get('member_id', '')
        council = _council_data(parish_data, council_type)
        council_member = next(
            (
                member
                for member in (council or {}).get('members', [])
                if member.get('id') == council_member_id
            ),
            None,
        )
        if council_member:
            council_member['confirmed'] = not council_member.get('confirmed')
            parish_data_service.save(parish_data)
            messages.success(request, 'Status članstva je ažuriran.')
        else:
            messages.error(request, 'Član vijeća nije pronađen.')
        return True

    return False
