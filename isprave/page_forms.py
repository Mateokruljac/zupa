"""Priprema formi za matične knjige."""
from __future__ import annotations

from typing import TYPE_CHECKING

from isprave.forms import RegistryBookForm, RegistryRecordForm

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService

ISPRAVE_PAGE_SLUGS = frozenset({'potvrde', 'maticne-knjige'})


def attach_registry_book_forms(
    request,
    parish_data_service: ParishDataService,
    page_context: dict,
) -> None:
    page_context['book_form'] = RegistryBookForm()
    selected_registry_book = page_context.get('selected_registry_book_view')
    selected_registry_year = page_context.get('selected_registry_year')
    if selected_registry_book and selected_registry_year:
        page_context['registry_record_form'] = RegistryRecordForm(
            registry_type=selected_registry_book.get('type', 'ostalo'),
            selected_year=selected_registry_year,
        )
    selected_book_id = request.GET.get('book')
    if not selected_book_id:
        return

    selected_book = next(
        (
            registry_book
            for registry_book in parish_data_service.load().get(
                'registryBooks',
                [],
            )
            if registry_book.get('id') == selected_book_id
        ),
        None,
    )
    if not selected_book:
        return
    page_context['selected_book'] = selected_book
    page_context['book_form'] = RegistryBookForm(initial={
        'title': selected_book.get('title', ''),
        'book_type': selected_book.get('type', 'krštenja'),
        'location': selected_book.get('location', ''),
        'last_entry': selected_book.get('lastEntry') or None,
        'last_no': selected_book.get('lastNo', ''),
        'custodian': selected_book.get('custodian', ''),
        'status': selected_book.get('status', 'u župi'),
        'notes': selected_book.get('notes', ''),
    })


def attach_isprave_forms(
    request,
    page_slug: str,
    parish_data_service: ParishDataService,
    page_context: dict,
) -> bool:
    if page_slug == 'maticne-knjige':
        attach_registry_book_forms(
            request,
            parish_data_service,
            page_context,
        )
        return True
    if page_slug == 'potvrde':
        return True
    return False
