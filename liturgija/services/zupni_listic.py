"""Župni listić — konfiguracija, renderiranje i kontekst stranice."""
from __future__ import annotations

import copy
import re
from datetime import date, datetime
from html import escape

from django.template.loader import render_to_string

from pastoral.services.dates import fmt_hr_short as fmt_short
from pastoral.services.dates import week_end_from, week_start_from
from liturgija.services.liturgical import LiturgicalService
from liturgija.services.mass_schedule import format_mass_schedule_html as format_mass_schedule
from liturgija.config.zupni_listic_config_data import ZUPNI_LISTIC_CONFIG

_config_cache: dict | None = None


def load_config() -> dict:
    """Vrste blokova i default layout iz Python dicta (kopija, da se ne mutira modul)."""
    global _config_cache
    if _config_cache is None:
        _config_cache = copy.deepcopy(ZUPNI_LISTIC_CONFIG)
    return copy.deepcopy(_config_cache)


def plain_text_to_html(text: str | None) -> str:
    """Običan tekst (prazan red = novi odlomak) → escapeani HTML."""
    t = (text or '').strip()
    if not t:
        return '<p>—</p>'
    parts = re.split(r'\n\s*\n', t)
    return ''.join(
        f'<p>{escape(p.strip()).replace(chr(10), "<br>")}</p>'
        for p in parts if p.strip()
    )


_LEGACY_CUSTOM_TEXT = 'Korizmeni program i pobožnosti prema župnom kalendaru.'
_LEGACY_ANNOUNCEMENT_PLACEHOLDERS = {
    'Upišite tekst…',
    'Upišite tekst...',
    'Upišite obavijesti za ovaj tjedan.',
}


def _plain_listic_body(html: str) -> str:
    """Makni tagove da usporedimo placeholder tekst."""
    return re.sub(r'<[^>]+>', '', html or '').replace('\xa0', ' ').strip()


def _strip_legacy_listic_defaults(layout: dict) -> dict:
    """Očisti stare demo rečenice iz custom/announcements blokova."""
    for block in layout.get('blocks') or []:
        plain = _plain_listic_body(block.get('body') or '')
        if block.get('type') == 'custom_text' and plain == _LEGACY_CUSTOM_TEXT:
            block['body'] = ''
        if block.get('type') == 'announcements' and plain in _LEGACY_ANNOUNCEMENT_PLACEHOLDERS:
            block['body'] = ''
    return layout


def get_layout(data: dict | None = None, config: dict | None = None) -> dict:
    """Kostur listića: default iz koda, ne spremljeni predložak župe."""
    cfg = config or load_config()
    return _strip_legacy_listic_defaults(copy.deepcopy(cfg['defaultLayout']))


def migrate_listic_data(data: dict) -> dict:
    """Osiguraj listu izdanja (in-place)."""
    if not isinstance(data.get('zupniListicIssues'), list):
        data['zupniListicIssues'] = []
    return data


def liturgical_color_hint(iso: str) -> str:
    """Kratki natpis boje/dana za UI; fallback po danu u tjednu ako kalendar prazan."""
    day = LiturgicalService().get_day(iso, with_hilp=False)
    if day.get('colorLabel'):
        return day['colorLabel']
    if day.get('title') and day.get('source') != 'offline':
        return day['title']
    d = date.fromisoformat(iso)
    if d.weekday() == 6:
        return 'Zelena (ili liturgija dana)'
    if d.weekday() == 4:
        return 'Ljubičasta / crvena (petak)'
    return 'Zelena (ferija)'


def format_nakane_html(data: dict, week_start: str) -> str:
    """Tablica nakana tog tjedna za listić."""
    start = week_start_from(week_start)
    end = week_end_from(start)
    rows = sorted(
        [
            n for n in (data.get('intentions') or [])
            if start <= (n.get('date') or '') <= end
        ],
        key=lambda n: (n.get('date') or '', n.get('massTime') or ''),
    )
    if not rows:
        return '<p>U tom tjednu nema upisanih nakana.</p>'
    body = ''.join(
        '<tr>'
        f'<td>{fmt_short(n["date"])}</td>'
        f'<td>{escape(n.get("massTime") or "")}</td>'
        f'<td>{escape(n.get("intentionFor") or "")}</td>'
        '</tr>'
        for n in rows
    )
    return render_to_string('liturgija/listic/nakane_table.html', {'rows_html': body})


def format_announcements(data: dict, body_html: str = '') -> str:
    """Tijelo obavijesti: plain → HTML, ili ostavi postojeći HTML."""
    if not body_html.strip():
        return ''
    return (
        plain_text_to_html(body_html)
        if '<' not in body_html
        else body_html
    )


def format_sacraments_and_events(data: dict, week_start: str, week_end: str) -> str:
    """Krštenja, vjenčanja, pogrebi i događaji unutar tjedna → HTML lista."""
    lines: list[str] = []
    for b in data.get('baptisms') or []:
        bd = b.get('baptismDate') or ''
        if week_start <= bd <= week_end:
            lines.append(f'Krštenje: {b.get("childName") or ""} — {fmt_short(bd)}')
    for w in data.get('weddings') or []:
        wd = w.get('weddingDate') or ''
        if week_start <= wd <= week_end:
            lines.append(f'Vjenčanje: {w.get("couple") or ""} — {fmt_short(wd)}')
    for f in data.get('funerals') or []:
        fd = f.get('funeralDate') or ''
        if week_start <= fd <= week_end:
            lines.append(f'Pogreb: {f.get("deceased") or ""} — {fmt_short(fd)}')
    for e in data.get('events') or []:
        ed = e.get('date') or ''
        if week_start <= ed <= week_end:
            place = escape(e.get('place') or '')
            lines.append(f'{e.get("title") or ""} — {fmt_short(ed)} ({place})')
    if not lines:
        return '<p>Nema sakramenata ni događaja u ovom tjednu.</p>'
    lis = ''.join(f'<li>{escape(line)}</li>' for line in lines)
    return f'<ul class="listic-ul">{lis}</ul>'


def render_block_html(block: dict, data: dict, settings: dict, week_start: str) -> str:
    """Jedan blok listića prema ``type`` (header, mise, nakane, …)."""
    start = week_start_from(week_start)
    end = week_end_from(start)
    btype = block.get('type') or ''
    title = block.get('title') or ''
    body_html = block.get('body') or ''

    if btype == 'header':
        return render_to_string('liturgija/listic/header.html', {
            'settings': settings,
            'week_start': start,
            'week_end': end,
            'week_start_fmt': fmt_short(start),
            'week_end_fmt': fmt_short(end),
        })
    if btype == 'mass_schedule':
        return render_to_string('liturgija/listic/section.html', {
            'title': title or 'Raspored sv. misa',
            'body_html': format_mass_schedule(data),
        })
    if btype == 'nakane':
        return render_to_string('liturgija/listic/section.html', {
            'title': title or 'Molitvene nakane',
            'body_html': format_nakane_html(data, start),
        })
    if btype == 'announcements':
        return render_to_string('liturgija/listic/section.html', {
            'title': title or 'Obavijesti župe',
            'body_html': format_announcements(data, body_html),
        })
    if btype == 'custom_text':
        return render_to_string('liturgija/listic/section.html', {
            'title': title or 'Obavijest',
            'body_html': plain_text_to_html(body_html) if '<' not in body_html else body_html,
        })
    if btype == 'sacraments':
        return render_to_string('liturgija/listic/section.html', {
            'title': title or 'Sakramenti i događaji',
            'body_html': format_sacraments_and_events(data, start, end),
        })
    if btype == 'contact':
        return render_to_string('liturgija/listic/section.html', {
            'title': title or 'Župni ured',
            'body_html': render_to_string('liturgija/listic/contact.html', {'settings': settings}),
        })
    if btype == 'footer':
        footer_body = plain_text_to_html(body_html) if body_html and '<' not in body_html else body_html
        return render_to_string('liturgija/listic/footer.html', {
            'body_html': footer_body,
            'issued_at': date.today().strftime('%d.%m.%Y.'),
        })
    return ''


def render_layout_to_html(layout: dict, data: dict, settings: dict, week_start: str) -> str:
    """Spoji uključene blokove u cijeli HTML dokument listića."""
    blocks = [b for b in (layout or {}).get('blocks') or [] if b.get('enabled', True)]
    inner = '\n'.join(
        render_block_html(b, data, settings, week_start)
        for b in blocks
    )
    return render_to_string('liturgija/listic/document.html', {'inner_html': inner})


def sync_auto_blocks(layout: dict, data: dict, settings: dict, week_start: str) -> dict:
    """Ako footer nema tijelo, uzmi default iz konfiguracije."""
    layout = _strip_legacy_listic_defaults(copy.deepcopy(layout))
    cfg = load_config()
    for block in layout.get('blocks') or []:
        if block.get('type') == 'footer' and block.get('id') == 'blk_ft' and not block.get('body'):
            for b in cfg['defaultLayout']['blocks']:
                if b.get('id') == 'blk_ft':
                    block['body'] = b.get('body') or ''
                    break
    return layout


def sorted_issues(data: dict) -> list:
    """Izdanja listića, najnovije prvo."""
    return sorted(
        data.get('zupniListicIssues') or [],
        key=lambda x: x.get('createdAt') or '',
        reverse=True,
    )


def zupni_listic_page_context(data: dict, settings: dict, request) -> dict:
    """Kontekst stranice: default layout, tjedan iz ``?week=``, pretpregled HTML."""
    cfg = load_config()
    layout = get_layout(data, cfg)
    week_start = week_start_from(request.GET.get('week') or None)
    issues = sorted_issues(data)
    edit_layout = sync_auto_blocks(layout, data, settings, week_start)
    return {
        'listic_edit_layout': edit_layout,
        'listic_issues': issues,
        'week_start': week_start,
        'block_types': cfg['blockTypes'],
        'initial_preview_html': render_layout_to_html(edit_layout, data, settings, week_start),
    }


def render_preview(data: dict, settings: dict, payload: dict) -> dict:
    """API pretpregled: layout iz requesta ili default iz koda."""
    layout = payload.get('layout') or get_layout(data)
    week_start = payload.get('weekStart') or week_start_from()
    html = render_layout_to_html(layout, data, settings, week_start)
    return {'ok': True, 'html': html}


def prepare_issue(data: dict, settings: dict, issue: dict) -> dict:
    """Dopuni izdanje (naslov, snapshot, ``renderedHtml``) prije spremanja.

    Novi broj nema ``id`` dok ga ORM ne dodijeli (FCTA UUID).
    """
    issue = dict(issue)
    ws = issue.get('weekStart') or week_start_from()
    we = issue.get('weekEnd') or week_end_from(ws)
    layout = issue.get('layoutSnapshot') or get_layout(data)
    issue['layoutSnapshot'] = copy.deepcopy(layout)
    if not issue.get('title'):
        issue['title'] = f'Listić {fmt_short(ws)} – {fmt_short(we)}'
    issue['weekStart'] = ws
    issue['weekEnd'] = we
    now = datetime.now().astimezone().isoformat()
    if not issue.get('createdAt'):
        issue['createdAt'] = now
    issue['updatedAt'] = now
    issue['renderedHtml'] = render_layout_to_html(layout, data, settings, ws)
    if not issue.get('id'):
        issue.pop('id', None)
    return issue
