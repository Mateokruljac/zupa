"""
Popunjavanje HTML predložaka župnih isprava.

Predlošci žive u `document_templates_data.DOCUMENT_TEMPLATES` (statski katalog,
nije DMS niti `RegisterTemplate`). Ovdje se samo čitaju i u `{{ključeve}}`
ubacuju vrijednosti. Tijelo je HTML za ispis; običan tekst se escapea,
`SafeData` (npr. tablica nakana) ostaje HTML.

Pozivatelji: ekran potvrda, ispis, preview u `pastoral.views`.
Ne smije se mutirati vraćeni dict predloška — to je isti objekt iz kataloga.
"""
from __future__ import annotations

import re

from django.utils.html import escape
from django.utils.safestring import SafeData

from isprave.document_templates_data import DOCUMENT_TEMPLATES

_UNFILLED_PLACEHOLDER = re.compile(r'\{\{[^}]+\}\}')
_TEMPLATES_BY_ID = {
    template['id']: template
    for template in DOCUMENT_TEMPLATES
}


def load_templates() -> list[dict]:
    """Cijeli katalog predložaka za popis na ekranu potvrda."""
    return DOCUMENT_TEMPLATES


def get_template(template_id: str) -> dict | None:
    """Jedan predložak po `id`, ili None ako šifra nije u katalogu."""
    return _TEMPLATES_BY_ID.get(template_id)


def render_template(template_id: str, values: dict) -> str:
    """
    HTML dokument spreman za preview ili ispis.

    Nepoznat `template_id` daje prazan string, ne iznimku — UI već javlja
    da predložak nije pronađen.

    Args:
        template_id: Šifra iz kataloga (`potvrda_krsenja`, …).
        values: Zamjene za `{{polje}}`; tablica nakana smije biti SafeData.

    Returns:
        HTML s popunjenim poljima; nepopunjeni `{{…}}` postaju crtica.
    """
    template = get_template(template_id)
    if not template:
        return ''
    return _fill_placeholders(template.get('body', ''), values)


def _fill_placeholders(html: str, values: dict) -> str:
    """Zamjenjuje `{{ključ}}` u HTML-u; nepoznati ostaci idu u —."""
    filled = html or ''
    for key, value in (values or {}).items():
        replacement = (
            value
            if isinstance(value, SafeData)
            else escape('' if value is None else value)
        )
        filled = filled.replace(f'{{{{{key}}}}}', str(replacement))
    return _UNFILLED_PLACEHOLDER.sub('—', filled)
