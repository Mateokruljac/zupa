"""API mutacije za raspored misa i župni listić.

Pišu direktno u ORM; ``parish_data`` se osvježi iz baze za JSON odgovor.
"""
from __future__ import annotations

from liturgija.models import BulletinIssue, MassScheduleSlot
from liturgija.services.mass_records import (
    bulletin_issue_as_legacy_record,
    bulletin_issue_field_defaults_from_legacy,
    mass_schedule_slot_as_legacy_record,
    mass_schedule_slot_field_defaults_from_legacy,
    parse_optional_uuid,
)


def _reload_mass_schedule(data: dict) -> None:
    data['massSchedule'] = [
        mass_schedule_slot_as_legacy_record(slot)
        for slot in MassScheduleSlot.objects.all()
    ]


def _reload_listic_issues(data: dict) -> None:
    data['zupniListicIssues'] = [
        bulletin_issue_as_legacy_record(issue)
        for issue in BulletinIssue.objects.all()
    ]


def upsert_mass_schedule(data: dict, action_payload: dict) -> dict:
    """Ažuriraj termin po ``id`` ili kreiraj novi (UUID PK odmah)."""
    fields = dict(action_payload.get('fields') or action_payload)
    schedule_id = action_payload.get('id')

    if schedule_id:
        slot = MassScheduleSlot.objects.filter(
            pk=parse_optional_uuid(schedule_id),
        ).first()
        if slot is None:
            return {'ok': False, 'error': 'not_found'}
        for field_name, field_value in mass_schedule_slot_field_defaults_from_legacy(
            fields,
        ).items():
            setattr(slot, field_name, field_value)
        slot.save()
    else:
        slot = MassScheduleSlot(
            **mass_schedule_slot_field_defaults_from_legacy(fields),
        )
        slot.save()

    _reload_mass_schedule(data)
    return {'ok': True, 'item': mass_schedule_slot_as_legacy_record(slot)}


def delete_mass_schedule(data: dict, action_payload: dict) -> dict:
    """Obriši termin rasporeda."""
    pk = parse_optional_uuid(action_payload.get('id'))
    if pk:
        MassScheduleSlot.objects.filter(pk=pk).delete()
    _reload_mass_schedule(data)
    return {'ok': True}


def upsert_listic_issue(
    data: dict,
    action_payload: dict,
    settings: dict | None = None,
) -> dict:
    """Spremi izdanje listića (update po UUID ili novo s ORM PK)."""
    from liturgija.services.zupni_listic import prepare_issue

    issue = prepare_issue(
        data,
        settings or {},
        dict(action_payload.get('issue') or action_payload),
    )
    defaults = bulletin_issue_field_defaults_from_legacy(issue)
    if defaults['week_start'] is None or defaults['week_end'] is None:
        return {'ok': False, 'error': 'invalid_week'}

    pk = parse_optional_uuid(issue.get('id'))
    bulletin = BulletinIssue.objects.filter(pk=pk).first() if pk else None
    if bulletin is None:
        bulletin = BulletinIssue(**defaults)
    else:
        for field_name, field_value in defaults.items():
            setattr(bulletin, field_name, field_value)
    bulletin.save()

    _reload_listic_issues(data)
    return {'ok': True, 'item': bulletin_issue_as_legacy_record(bulletin)}


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
    pk = parse_optional_uuid(action_payload.get('id'))
    if pk:
        BulletinIssue.objects.filter(pk=pk).delete()
    _reload_listic_issues(data)
    return {'ok': True}
