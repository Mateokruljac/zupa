"""Župni list — ispis misnih nakana za tjedan."""
from __future__ import annotations

from html import escape

from pastoral.services.dates import fmt_hr_date, week_start_from
from pastoral.services.documents import get_template, merge_template
from pastoral.services.mass_schedule import week_intentions


def build_bulletin_html(data: dict, settings: dict, start_iso: str | None = None) -> str:
    start = week_start_from(start_iso)
    rows = week_intentions(data, start)
    if rows:
        body = ''.join(
            '<tr>'
            f'<td>{escape(fmt_hr_date(n["date"]))}</td>'
            f'<td>{escape(n.get("massTime") or "")}</td>'
            f'<td>{escape(n.get("intentionFor") or "")}</td>'
            f'<td>{escape(n.get("requestedBy") or "—")}</td>'
            f'<td>{"✓" if n.get("paid") else "—"}</td>'
            '</tr>'
            for n in rows
        )
    else:
        body = '<tr><td colspan="5">Nema nakan u tom tjednu</td></tr>'

    tpl = get_template('raspored_nakana')
    html = tpl.get('body', '') if tpl else ''
    return merge_template(html, {
        'zupa': settings.get('name') or '',
        'tjedan_od': fmt_hr_date(start),
        'tablica_nakana': body,
    })
