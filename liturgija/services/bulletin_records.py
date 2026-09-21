"""Pretvorba župnog listića ORM ↔ legacy API dict (camelCase za JS)."""
from __future__ import annotations

import copy

from datetime import timedelta

from core.utils import _iso_or_empty, _parse_iso_date
from liturgija.models import BulletinIssue


def bulletin_issue_as_legacy_record(issue: BulletinIssue) -> dict:
    """Red tablice listića → dict koji čita JS i povijest izdanja."""
    layout = issue.layout if isinstance(issue.layout, dict) else {}
    return {
        'id': str(issue.id),
        'weekStart': _iso_or_empty(issue.week_start),
        'weekEnd': _iso_or_empty(issue.week_end),
        'title': issue.title or '',
        'status': issue.status or BulletinIssue.Status.PUBLISHED,
        'layoutSnapshot': copy.deepcopy(layout),
        'renderedHtml': issue.rendered_html or '',
        'createdAt': issue.created_at.isoformat() if issue.created_at else '',
        'updatedAt': issue.updated_at.isoformat() if issue.updated_at else '',
    }


def bulletin_issue_field_defaults_from_legacy(record: dict) -> dict:
    """JS dict → kwargs za ``BulletinIssue`` (bez PK)."""
    layout = record.get('layoutSnapshot')
    if not isinstance(layout, dict):
        layout = {}
    status = str(record.get('status') or BulletinIssue.Status.PUBLISHED)
    if status not in BulletinIssue.Status.values:
        status = BulletinIssue.Status.PUBLISHED
    week_start = _parse_iso_date(record.get('weekStart'))
    week_end = _parse_iso_date(record.get('weekEnd'))
    if week_start is not None and week_end is None:
        week_end = week_start + timedelta(days=6)
    return {
        'week_start': week_start,
        'week_end': week_end,
        'title': str(record.get('title') or '')[:255],
        'status': status,
        'layout': copy.deepcopy(layout),
        'rendered_html': str(record.get('renderedHtml') or ''),
    }
