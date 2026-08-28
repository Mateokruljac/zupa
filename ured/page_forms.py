"""Priprema formi za stranice župnog ureda."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ured.forms import (
    CouncilMeetingForm,
    CouncilMemberForm,
    EventForm,
    ParishSettingsForm,
    TaskForm,
)

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService

URED_PAGE_SLUGS = frozenset({
    'kalendar',
    'podsjetnici',
    'vijeca',
    'postavke',
    'javne-prijave',
})


def attach_ured_forms(
    request,
    page_slug: str,
    parish_data_service: ParishDataService,
    page_context: dict,
) -> bool:
    if page_slug not in URED_PAGE_SLUGS:
        return False

    if page_slug == 'kalendar':
        pastor_name = parish_data_service.load_settings().get('pastor', '')
        selected_date = (
            page_context.get('filter_date')
            or parish_data_service.today_iso()
        )
        selected_task = page_context.get('selected_task')
        task_initial_values = {
            'owner': pastor_name,
            'due': selected_date,
            'priority': 'srednja',
        }
        if selected_task:
            task_initial_values.update({
                'title': selected_task.get('title', ''),
                'owner': selected_task.get('owner', ''),
                'due': selected_task.get('due') or None,
                'priority': selected_task.get('priority', 'srednja'),
                'category': selected_task.get('category', ''),
            })
        page_context['task_form'] = TaskForm(initial=task_initial_values)

        selected_event = page_context.get('selected_event')
        event_initial_values = {
            'owner': pastor_name,
            'event_date': selected_date,
        }
        if selected_event:
            event_initial_values.update({
                'title': selected_event.get('title', ''),
                'event_date': selected_event.get('date') or selected_date,
                'event_time': selected_event.get('time') or None,
                'place': selected_event.get('place', ''),
                'event_type': selected_event.get('type', 'pastoral'),
                'owner': selected_event.get('owner', ''),
                'notes': selected_event.get('notes', ''),
            })
        page_context['event_form'] = EventForm(initial=event_initial_values)
        return True

    if page_slug == 'vijeca':
        selected_council_member = page_context.get('selected_council_member')
        council_member_initial_values = {
            'council_type': page_context.get(
                'selected_council_type',
                'pastoral',
            ),
            'confirmed': True,
        }
        if selected_council_member:
            council_member_initial_values.update({
                'name': selected_council_member.get('name', ''),
                'role': selected_council_member.get('role', ''),
                'phone': selected_council_member.get('phone', ''),
                'confirmed': selected_council_member.get('confirmed', False),
            })
        page_context['council_member_form'] = CouncilMemberForm(
            initial=council_member_initial_values,
        )
        page_context['council_meeting_form'] = CouncilMeetingForm(initial={
            'council_type': page_context.get(
                'selected_council_type',
                'pastoral',
            ),
        })
        return True

    if page_slug == 'postavke':
        parish_settings = page_context.get('settings', {})
        page_context['settings_form'] = ParishSettingsForm(initial={
            'name': parish_settings.get('name'),
            'short_name': parish_settings.get('shortName'),
            'city': parish_settings.get('city'),
            'diocese': parish_settings.get('diocese'),
            'pastor': parish_settings.get('pastor'),
            'phone': parish_settings.get('phone'),
            'email': parish_settings.get('email'),
            'primary_color': parish_settings.get('primaryColor'),
            'accent_color': parish_settings.get('accentColor'),
            'logo_url': parish_settings.get('logoUrl', ''),
            'default_mass_intention_stipend': parish_settings.get(
                'defaultMassIntentionStipend',
                0,
            ),
        })
        return True

    return True
