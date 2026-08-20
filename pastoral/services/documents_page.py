"""Jedinstveni ekran za izdavanje župnih dokumenata i potvrda."""
from __future__ import annotations

from datetime import date

from pastoral.services.documents import get_template, load_templates, render_template
from pastoral.services.matica import search_all


def parish_doc_defaults(settings: dict) -> dict:
    today = date.today()
    months = ['sij', 'velj', 'ožu', 'tra', 'svi', 'lip', 'srp', 'kol', 'ruj', 'lis', 'stu', 'pro']
    danas = f'{today.day}. {months[today.month - 1]} {today.year}.'
    return {
        'zupa': settings.get('name') or settings.get('shortName') or 'Župa',
        'zupnik': settings.get('pastor') or '',
        'mjesto': settings.get('city') or '',
        'danas': danas,
        'godina': str(today.year),
    }


def templates_by_category(templates: list[dict]) -> list[dict]:
    groups: dict[str, list] = {}
    for t in templates:
        cat = t.get('category') or 'ostalo'
        groups.setdefault(cat, []).append(t)
    return [{'id': k, 'label': k, 'templates': v} for k, v in sorted(groups.items())]


def prefill_from_matica(data: dict, record_type: str, record_id: str) -> dict:
    key_map = {
        'krštenja': 'baptisms',
        'krsenja': 'baptisms',
        'vjenčanja': 'weddings',
        'vjencanja': 'weddings',
        'umrli': 'funerals',
        'pogrebi': 'funerals',
    }
    arr_key = key_map.get(record_type, record_type)
    row = next((x for x in data.get(arr_key, []) if x.get('id') == record_id), None)
    if not row:
        return {}
    if arr_key == 'baptisms':
        return {
            'ime_djeteta': row.get('childName', ''),
            'datum_krstenja': row.get('baptismDate', ''),
            'roditelji': row.get('parents', ''),
            'kumovi': row.get('godparents', ''),
            'maticni_broj': row.get('registryNo', ''),
        }
    if arr_key == 'weddings':
        return {
            'mladenci': row.get('couple', ''),
            'datum_vjencanja': row.get('weddingDate', ''),
            'svjedoci': row.get('witnesses', ''),
        }
    if arr_key == 'funerals':
        deceased = (row.get('deceased') or '').lstrip('+').strip()
        return {
            'pokojnik': deceased,
            'datum_pogreba': row.get('funeralDate', ''),
            'datum_smrti': row.get('deathDate', ''),
        }
    return {}


def build_field_values(request, template: dict, defaults: dict) -> dict:
    values = dict(defaults)
    for field in template.get('fields') or []:
        key = f'field_{field}'
        if key in request.POST:
            values[field] = request.POST.get(key, '')
        elif field in request.POST:
            values[field] = request.POST.get(field, '')
    return values


def documents_page_context(data: dict, settings: dict, request) -> dict:
    templates = load_templates()
    selected_id = (request.GET.get('tpl') or request.POST.get('template_id') or '').strip()
    selected = get_template(selected_id) if selected_id else None
    defaults = parish_doc_defaults(settings)
    prefill = {}
    if request.GET.get('record_type') and request.GET.get('record_id'):
        prefill = prefill_from_matica(data, request.GET.get('record_type'), request.GET.get('record_id'))
    matica_q = (request.GET.get('q') or '').strip()
    matica_results = search_all(data, matica_q, 12) if matica_q else []

    preview_html = ''
    if request.method == 'GET' and request.GET.get('preview') == '1' and selected:
        vals = {**defaults, **prefill}
        for field in selected.get('fields') or []:
            if request.GET.get(field):
                vals[field] = request.GET.get(field)
        if selected['id'] == 'raspored_nakana':
            vals['tablica_nakana'] = intentions_table_html(data, vals.get('tjedan_od', ''))
        preview_html = render_template(selected['id'], vals)

    result = {
        'doc_templates': templates,
        'doc_categories': templates_by_category(templates),
        'selected_template': selected,
        'doc_defaults': defaults,
        'doc_prefill': prefill,
        'matica_query': matica_q,
        'matica_results': matica_results,
        'preview_html': preview_html,
    }
    return result


def render_document_for_print(template_id: str, values: dict) -> str:
    return render_template(template_id, values)


def intentions_table_html(data: dict, week_start: str) -> str:
    rows = []
    for n in sorted(data.get('intentions', []), key=lambda x: (x.get('date') or '', x.get('massTime') or '')):
        if not (n.get('date') or '').startswith(week_start[:7]):
            continue
        rows.append(
            f'<tr><td>{n.get("date", "")}</td><td>{n.get("massTime", "")}</td>'
            f'<td>{n.get("intentionFor", "")}</td><td>{n.get("requestedBy", "")}</td>'
            f'<td>{n.get("stipend", "")}</td></tr>'
        )
    return ''.join(rows) or '<tr><td colspan="5">—</td></tr>'
