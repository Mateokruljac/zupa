"""Kontekst stranice vijeća ŽPV/ŽEV."""
from __future__ import annotations


def councils_page_context(parish_data: dict, request) -> dict:
    pastoral_council = parish_data.get('pastoralCouncil', {})
    economic_council = parish_data.get('economicCouncil', {})
    selected_council_type = request.GET.get('council', 'pastoral')
    if selected_council_type not in {'pastoral', 'economic'}:
        selected_council_type = 'pastoral'
    selected_council = (
        economic_council
        if selected_council_type == 'economic'
        else pastoral_council
    )
    selected_member_identifier = request.GET.get('member', '')
    selected_council_member = next(
        (
            council_member
            for council_member in selected_council.get('members', [])
            if council_member.get('id') == selected_member_identifier
        ),
        None,
    )
    return {
        'pastoral_council': pastoral_council,
        'economic_council': economic_council,
        'selected_council_type': selected_council_type,
        'selected_council_member': selected_council_member,
        'council_member_form_mode': (
            'add'
            if selected_member_identifier == 'new'
            else 'edit'
            if selected_council_member
            else ''
        ),
        'council_meeting_dialog_open': request.GET.get('meeting') == '1',
        'pastoral_confirmed_member_count': sum(
            bool(council_member.get('confirmed'))
            for council_member in pastoral_council.get('members', [])
        ),
        'economic_confirmed_member_count': sum(
            bool(council_member.get('confirmed'))
            for council_member in economic_council.get('members', [])
        ),
    }
