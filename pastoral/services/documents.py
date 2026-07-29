"""Predlošci dokumenata — izvor istine (prije documents-engine.js)."""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

TEMPLATES_PATH = Path(__file__).resolve().parent.parent / 'data' / 'document_templates.json'

_cache: list | None = None


def load_templates() -> list[dict]:
    global _cache
    if _cache is None:
        with TEMPLATES_PATH.open(encoding='utf-8') as f:
            _cache = json.load(f)
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
        out = out.replace(f'{{{{{key}}}}}', str(val if val is not None else ''))
    return re.sub(r'\{\{[^}]+\}\}', '—', out)


def render_template(template_id: str, values: dict) -> str:
    tpl = get_template(template_id)
    if not tpl:
        return ''
    return merge_template(tpl.get('body', ''), values)
