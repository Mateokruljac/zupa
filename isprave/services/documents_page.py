"""
Ekran „Dokumenti i potvrde”: katalog, pretpopuna s matice, preview.

Nije matična knjiga i nije DMS. Predlošci su statični HTML
(`documents.render_template`). Ispis u novom prozoru radi
`document_print` s istim zadanim poljima župe.

Što predstavlja svaki dio:
- zadane vrijednosti župe (`zupa`, `zupnik`, `danas`) — header svake isprave
- pretpopuna s krštenja — jedini automatski izvor iz matice danas
- preview — GET nakon gumba Pregledaj; ispis je odvojeni POST
"""
from __future__ import annotations

from datetime import date

from django.utils.html import escape
from django.utils.safestring import mark_safe

from isprave.services.documents import get_template, load_templates, render_template
from isprave.services.matica import search_all

_CROATIAN_MONTH_ABBREVIATIONS = (
    'sij', 'velj', 'ožu', 'tra', 'svi', 'lip',
    'srp', 'kol', 'ruj', 'lis', 'stu', 'pro',
)
_BAPTISM_RECORD_TYPES = frozenset({'krštenja', 'krsenja', 'baptisms'})
_INTENTIONS_SCHEDULE_TEMPLATE_ID = 'raspored_nakana'


def parish_doc_defaults(settings: dict) -> dict:
    """
    Polja koja svaka isprava dobije iz profila župe, bez unosa korisnika.

    `danas` je hrvatski kratki datum (npr. 18. ruj 2026.), ne ISO.
    Koriste ga i ekran i ispis.

    Args:
        settings: Parish.settings (name, pastor, city).

    Returns:
        Ključevi predloška: zupa, zupnik, mjesto, danas, godina.
    """
    today = date.today()
    month_name = _CROATIAN_MONTH_ABBREVIATIONS[today.month - 1]
    return {
        'zupa': settings.get('name') or settings.get('shortName') or 'Župa',
        'zupnik': settings.get('pastor') or '',
        'mjesto': settings.get('city') or '',
        'danas': f'{today.day}. {month_name} {today.year}.',
        'godina': str(today.year),
    }


def build_field_values(request, template: dict, defaults: dict) -> dict:
    """
    Vrijednosti polja za ispis iz POST obrasca.

    Predložak šalje `field_<ključ>`; stariji klijent može slati goli ključ.
    Zadane vrijednosti župe ostaju ako polje nije u POST-u.

    Args:
        request: POST s `field_*`.
        template: Katalog-predložak s listom `fields`.
        defaults: Izlaz `parish_doc_defaults`.

    Returns:
        Dict za `render_template`.
    """
    values = dict(defaults)
    for field in template.get('fields') or []:
        prefixed = f'field_{field}'
        if prefixed in request.POST:
            values[field] = request.POST.get(prefixed, '')
        elif field in request.POST:
            values[field] = request.POST.get(field, '')
    return values


def intentions_table_html(data: dict, week_start: str) -> str:
    """
    HTML retci tjednog rasporeda nakana (`{{tablica_nakana}}`).

    Filtrira po YYYY-MM iz `week_start`, ne po točnom tjednu — polje
    predloška zove se tjedan, a usporedba je mjesec. Mark_safe da
    `render_template` ne escapea tablicu.

    Args:
        data: Parish dict s `intentions`.
        week_start: ISO datum ili prefiks; prazno uključuje sve nakanе.

    Returns:
        Safe HTML `<tr>…` ili jedan prazan red.
    """
    month_prefix = (week_start or '')[:7]
    rows = []
    sorted_intentions = sorted(
        data.get('intentions', []),
        key=lambda item: (item.get('date') or '', item.get('massTime') or ''),
    )
    for intention in sorted_intentions:
        if month_prefix and not (intention.get('date') or '').startswith(month_prefix):
            continue
        rows.append(
            f'<tr><td>{escape(intention.get("date", ""))}</td>'
            f'<td>{escape(intention.get("massTime", ""))}</td>'
            f'<td>{escape(intention.get("intentionFor", ""))}</td>'
            f'<td>{escape(intention.get("requestedBy", ""))}</td>'
            f'<td>{escape(intention.get("stipend", ""))}</td></tr>'
        )
    return mark_safe(''.join(rows) or '<tr><td colspan="5">—</td></tr>')


def documents_page_context(data: dict, settings: dict, request) -> dict:
    """
    Kontekst stranice potvrda.

    GET `tpl` bira predložak; `q` pretražuje krštenja; `record_type` +
    `record_id` pretpopunjava izvadak o krštenju. Preview je GET
    `preview=1` nakon redirecta iz POST `preview_document`.

    Args:
        data: Parish dict (krštenja, nakane).
        settings: Parish.settings.
        request: GET/POST filteri ekrana.

    Returns:
        Ključevi za `documents_form.html` (kategorije, odabrani predložak,
        pretpopuna, rezultati matice, preview HTML).
    """
    templates = load_templates()
    selected_id = (
        request.GET.get('tpl') or request.POST.get('template_id') or ''
    ).strip()
    selected = get_template(selected_id) if selected_id else None
    defaults = parish_doc_defaults(settings)
    record_type = request.GET.get('record_type') or ''
    record_id = request.GET.get('record_id') or ''
    prefill = (
        _prefill_baptism_fields(data, record_type, record_id)
        if record_type and record_id
        else {}
    )
    matica_query = (request.GET.get('q') or '').strip()
    matica_results = (
        search_all(data, matica_query, 12, types=['krštenja'])
        if matica_query
        else []
    )
    return {
        'doc_categories': _templates_by_category(templates),
        'selected_template': selected,
        'doc_defaults': defaults,
        'doc_prefill': prefill,
        'matica_query': matica_query,
        'matica_results': matica_results,
        'preview_html': _preview_html(request, data, selected, defaults, prefill),
    }


def _templates_by_category(templates: list[dict]) -> list[dict]:
    """Grupe za lijevi izbornik; `id` i `label` su kod kategorije iz kataloga."""
    groups: dict[str, list] = {}
    for template in templates:
        category = template.get('category') or 'ostalo'
        groups.setdefault(category, []).append(template)
    return [
        {'id': category, 'label': category, 'templates': items}
        for category, items in sorted(groups.items())
    ]


def _prefill_baptism_fields(data: dict, record_type: str, record_id: str) -> dict:
    """
    Polja izvatka o krštenju s odabranog retka matice.

    Druge vrste zapisa namjerno ne pune obrazac — UI nudi samo krštenja.
    """
    if record_type not in _BAPTISM_RECORD_TYPES:
        return {}
    baptism = next(
        (
            row
            for row in data.get('baptisms', [])
            if row.get('id') == record_id
        ),
        None,
    )
    if not baptism:
        return {}
    return {
        'ime_djeteta': baptism.get('childName', ''),
        'datum_krstenja': baptism.get('baptismDate', ''),
        'roditelji': baptism.get('parents', ''),
        'kumovi': baptism.get('godparents', ''),
        'maticni_broj': baptism.get('registryNo', ''),
    }


def _preview_html(request, data, selected, defaults, prefill) -> str:
    """HTML pregleda ako je GET preview=1 i predložak odabran; inače prazno."""
    if request.method != 'GET' or request.GET.get('preview') != '1' or not selected:
        return ''
    values = {**defaults, **prefill}
    for field in selected.get('fields') or []:
        if request.GET.get(field):
            values[field] = request.GET.get(field)
    if selected['id'] == _INTENTIONS_SCHEDULE_TEMPLATE_ID:
        values['tablica_nakana'] = intentions_table_html(
            data,
            values.get('tjedan_od', ''),
        )
    return render_template(selected['id'], values)
