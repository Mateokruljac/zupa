"""API mutacije za raspored misa, župni listić i misne nakane.

Nakane su u ``api_action_handlers.intentions``; ovdje se samo re-exportaju
da pastoral dispatcher vidi imena akcija.
"""
from __future__ import annotations

from pastoral.services.api_action_handlers.shared import generate_record_identifier
from liturgija.services.api_action_handlers.intentions import (
    create_intention,
    delete_intention,
    update_intention,
)


def upsert_mass_schedule(data: dict, action_payload: dict) -> dict:
    """Ažuriraj termin po ``id`` ili dodaj novi ako id nema."""
    fields = dict(action_payload.get('fields') or action_payload)
    schedule_id = action_payload.get('id')
    if schedule_id:
        schedule_entry = next(
            (
                entry
                for entry in data.get('massSchedule', [])
                if entry.get('id') == schedule_id
            ),
            None,
        )
        if not schedule_entry:
            return {'ok': False, 'error': 'not_found'}
        schedule_entry.update(fields)
        return {'ok': True, 'item': schedule_entry}
    item = {'id': generate_record_identifier('ms'), **fields}
    data.setdefault('massSchedule', []).append(item)
    return {'ok': True, 'item': item}


def delete_mass_schedule(data: dict, action_payload: dict) -> dict:
    """Obriši termin rasporeda."""
    schedule_id = action_payload.get('id')
    data['massSchedule'] = [
        entry
        for entry in data.get('massSchedule', [])
        if entry.get('id') != schedule_id
    ]
    return {'ok': True}


def upsert_listic_issue(
    data: dict,
    action_payload: dict,
    settings: dict | None = None,
) -> dict:
    """Spremi izdanje listića (update po id ili novo na početak liste)."""
    from liturgija.services.zupni_listic import prepare_issue

    issue = prepare_issue(
        data,
        settings or {},
        dict(action_payload.get('issue') or action_payload),
    )
    issue_id = issue.get('id')
    issues = data.setdefault('zupniListicIssues', [])
    if issue_id:
        existing_issue = next(
            (issue_row for issue_row in issues if issue_row.get('id') == issue_id),
            None,
        )
        if existing_issue:
            existing_issue.update(issue)
            return {'ok': True, 'item': existing_issue}
    issues.insert(0, issue)
    return {'ok': True, 'item': issue}


def render_listic_preview(
    data: dict,
    action_payload: dict,
    settings: dict | None = None,
) -> dict:
    """HTML pretpregled bez spremanja izdanja."""
    from liturgija.services.zupni_listic import render_preview

    return render_preview(data, settings or {}, action_payload)


def delete_listic_issue(data: dict, action_payload: dict) -> dict:
    """Ukloni izdanje listića po ``id``."""
    issue_id = action_payload.get('id')
    data['zupniListicIssues'] = [
        issue
        for issue in data.get('zupniListicIssues', [])
        if issue.get('id') != issue_id
    ]
    return {'ok': True}
