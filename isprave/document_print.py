"""Ispis župnih dokumenata i potvrda."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import redirect, render

from isprave.services.documents import get_template, render_template
from isprave.services.documents_page import (
    build_field_values,
    intentions_table_html,
    parish_doc_defaults,
)

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


def document_print_context(
    *,
    document_template,
    rendered_document,
    parish_settings,
    document_defaults,
) -> dict:
    return {
        'doc_html': rendered_document,
        'doc_title': document_template.get('name', 'Ispis'),
        'doc_category': document_template.get('category', 'dokument'),
        'doc_template_id': document_template.get('id', ''),
        'doc_parish': (
            parish_settings.get('name')
            or parish_settings.get('shortName')
            or 'Župa'
        ),
        'doc_city': parish_settings.get('city') or '',
        'doc_diocese': parish_settings.get('diocese') or '',
        'doc_pastor': parish_settings.get('pastor') or '',
        'doc_issued_at': document_defaults.get('danas', ''),
        'doc_primary': parish_settings.get('primaryColor') or '#5c2e3a',
        'doc_accent': parish_settings.get('accentColor') or '#b8922a',
    }


def document_print_response(request, parish_data_service: ParishDataService):
    template_id = request.POST.get('template_id', '')
    document_template = get_template(template_id)
    if not document_template:
        messages.error(request, 'Predložak nije pronađen.')
        return redirect(request.get_full_path())

    parish_data = parish_data_service.load()
    parish_settings = parish_data_service.load_settings()
    document_defaults = parish_doc_defaults(parish_settings)
    field_values = build_field_values(
        request,
        document_template,
        document_defaults,
    )
    if template_id == 'raspored_nakana':
        field_values['tablica_nakana'] = intentions_table_html(
            parish_data,
            field_values.get('tjedan_od', ''),
        )

    rendered_document = render_template(template_id, field_values)
    return render(
        request,
        'isprave/document_print.html',
        document_print_context(
            document_template=document_template,
            rendered_document=rendered_document,
            parish_settings=parish_settings,
            document_defaults=document_defaults,
        ),
    )
