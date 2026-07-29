"""Uvoz CSV za serijski ispis dokumenata."""
from __future__ import annotations

import csv
import io
import uuid

from pastoral.services.documents import get_template, render_template


def parse_csv_upload(uploaded_file) -> tuple[list[str], list[dict]]:
    raw = uploaded_file.read()
    for encoding in ('utf-8-sig', 'utf-8', 'cp1250', 'latin-1'):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode('utf-8', errors='replace')

    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    columns = list(reader.fieldnames or [])
    rows = [dict(row) for row in reader]
    return columns, rows


def map_row_to_values(row: dict, mapping: dict, defaults: dict) -> dict:
    values = dict(defaults)
    for placeholder, column in (mapping or {}).items():
        if column and column in row:
            values[placeholder] = row.get(column, '')
    return values


def render_row_html(template_id: str, row: dict, mapping: dict, defaults: dict) -> str:
    values = map_row_to_values(row, mapping, defaults)
    if template_id == 'raspored_nakana':
        from pastoral.services.documents_page import intentions_table_html
        from pastoral.services.data import ParishDataService
        data = ParishDataService().load()
        values['tablica_nakana'] = intentions_table_html(data, values.get('tjedan_od', ''))
    return render_template(template_id, values)


def save_binding(data: dict, template_id: str, template_name: str, file_name: str, mapping: dict, row_count: int) -> dict:
    bindings = data.setdefault('docBindings', [])
    binding = {
        'id': f"bind_{uuid.uuid4().hex[:8]}",
        'templateId': template_id,
        'templateName': template_name,
        'fileName': file_name,
        'mapping': mapping,
        'rowCount': row_count,
    }
    bindings.insert(0, binding)
    return binding


def delete_binding(data: dict, binding_id: str) -> bool:
    before = len(data.get('docBindings', []))
    data['docBindings'] = [b for b in data.get('docBindings', []) if b.get('id') != binding_id]
    return len(data['docBindings']) < before
