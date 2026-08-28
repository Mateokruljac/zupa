"""Predlošci dokumenata — izvor istine (prije documents-engine.js)."""
from __future__ import annotations

import copy
import re

from django.utils.html import escape
from django.utils.safestring import SafeData

from isprave.document_templates_data import DOCUMENT_TEMPLATES

_cache: list | None = None


def load_templates() -> list[dict]:
    global _cache
    if _cache is None:
        _cache = copy.deepcopy(DOCUMENT_TEMPLATES)
    return copy.deepcopy(_cache)


def get_template(template_id: str) -> dict | None:
    return next((t for t in load_templates() if t.get('id') == template_id), None)


def list_templates() -> list[dict]:
    return [
        {'id': t['id'], 'name': t['name'], 'category': t['category'], 'fields': t.get('fields', [])}
        for t in load_templates()
    ]


def merge_template(html: str, values: dict) -> str:
    out = html or ''
    for key, val in (values or {}).items():
        replacement = (
            val
            if isinstance(val, SafeData)
            else escape('' if val is None else val)
        )
        out = out.replace(f'{{{{{key}}}}}', str(replacement))
    return re.sub(r'\{\{[^}]+\}\}', '—', out)


def render_template(template_id: str, values: dict) -> str:
    tpl = get_template(template_id)
    if not tpl:
        return ''
    return merge_template(tpl.get('body', ''), values)
