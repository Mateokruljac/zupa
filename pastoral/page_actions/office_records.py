"""POST akcije za ulice, prijave, posjete, knjige i dokumente."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
import uuid

from django.contrib import messages

from pastoral.forms import RegistryBookForm, StreetForm, VisitForm
from pastoral.services.api_actions import (
    delete_street,
    import_public_submission,
    normalize_parish_data,
    toggle_visit_done,
    upsert_street,
    upsert_visit,
)
from pastoral.services.document_import import delete_binding, save_binding
from pastoral.services.documents import get_template

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


def handle_office_records_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
    if action_name == 'upsert_street' and page_slug == 'ulice':
        street_form = StreetForm(request.POST)
        if street_form.is_valid():
            cleaned_data = street_form.cleaned_data
            street_payload = {
                'id': request.POST.get('street_id') or None,
                'name': cleaned_data['name'],
                'zone': cleaned_data.get('zone') or '',
                'notes': cleaned_data.get('notes') or '',
            }
            normalize_parish_data(parish_data)
            operation_result = upsert_street(parish_data, street_payload)
            if operation_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Ulica spremljena.')
            else:
                messages.error(request, 'Provjerite unos ulice.')
        else:
            messages.error(request, 'Provjerite unos ulice.')
        return True

    if action_name == 'delete_street' and page_slug == 'ulice':
        normalize_parish_data(parish_data)
        delete_street(
            parish_data,
            {'id': request.POST.get('street_id', '')},
        )
        parish_data_service.save(parish_data)
        messages.success(request, 'Ulica obrisana.')
        return True

    if action_name == 'import_submission' and page_slug == 'javne-prijave':
        submission_id = request.POST.get('submission_id', '')
        public_submission = next(
            (
                submission
                for submission in parish_data.get('publicSubmissions', [])
                if submission.get('id') == submission_id
            ),
            None,
        )
        if not public_submission:
            messages.error(request, 'Prijava nije pronađena.')
            return True
        selected_year = int(request.POST.get('year') or date.today().year)
        normalize_parish_data(parish_data)
        operation_result = import_public_submission(
            parish_data,
            {'submission': public_submission, 'year': selected_year},
        )
        if operation_result.get('ok'):
            parish_data_service.save(parish_data)
            messages.success(request, 'Prijava uvezena u evidenciju.')
        else:
            messages.error(request, 'Uvoz nije uspio.')
        return True

    if (
        action_name == 'mark_submission_imported'
        and page_slug == 'javne-prijave'
    ):
        submission_id = request.POST.get('submission_id', '')
        public_submission = next(
            (
                submission
                for submission in parish_data.get('publicSubmissions', [])
                if submission.get('id') == submission_id
            ),
            None,
        )
        if public_submission:
            public_submission['status'] = 'preuzeto'
            parish_data_service.save(parish_data)
            messages.success(request, 'Prijava označena kao preuzeta.')
        return True

    if action_name == 'upsert_visit' and page_slug == 'posjete':
        visit_form = VisitForm(request.POST)
        if visit_form.is_valid():
            cleaned_data = visit_form.cleaned_data
            visit_payload = {
                'scheduled': cleaned_data['scheduled'].isoformat(),
                'person': cleaned_data['person'],
                'type': cleaned_data['visit_type'],
                'address': cleaned_data.get('address') or '',
                'priest': cleaned_data.get('priest') or '',
                'purpose': cleaned_data.get('purpose') or '',
                'familyId': cleaned_data.get('family_id') or '',
                'report': cleaned_data.get('report') or '',
            }
            visit_id = request.POST.get('visit_id')
            operation_result = upsert_visit(
                parish_data,
                {'id': visit_id, 'fields': visit_payload}
                if visit_id
                else visit_payload,
            )
            if operation_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Posjet spremljen.')
            else:
                messages.error(request, 'Posjet nije spremljen.')
        else:
            messages.error(request, 'Provjerite unos posjeta.')
        return True

    if action_name == 'toggle_visit' and page_slug == 'posjete':
        visit_id = request.POST.get('visit_id', '')
        selected_visit = next(
            (
                visit
                for visit in parish_data.get('visits', [])
                if visit.get('id') == visit_id
            ),
            None,
        )
        if (
            selected_visit
            and not selected_visit.get('done')
            and not (selected_visit.get('report') or '').strip()
        ):
            messages.error(
                request,
                'Prije zaključivanja posjeta upišite kratki ishod i sljedeći '
                'korak u polje Izvještaj.',
            )
            return True
        operation_result = toggle_visit_done(parish_data, {'id': visit_id})
        if operation_result.get('ok'):
            parish_data_service.save(parish_data)
            messages.success(request, 'Status posjeta ažuriran.')
        return True

    if action_name == 'delete_visit' and page_slug == 'posjete':
        messages.error(
            request,
            'Pastoralni zapis posjeta ne briše se. Uredite termin ili ga '
            'označite otkazanim kada uvedemo statusni tijek.',
        )
        return True

    if action_name == 'upsert_registry_book' and page_slug == 'maticne-knjige':
        registry_book_form = RegistryBookForm(request.POST)
        if registry_book_form.is_valid():
            cleaned_data = registry_book_form.cleaned_data
            registry_book_id = request.POST.get('book_id')
            registry_book_payload = {
                'title': cleaned_data['title'],
                'type': cleaned_data['book_type'],
                'location': cleaned_data.get('location') or '',
                'lastEntry': (
                    cleaned_data['last_entry'].isoformat()
                    if cleaned_data.get('last_entry')
                    else ''
                ),
                'lastNo': cleaned_data.get('last_no') or '',
                'custodian': cleaned_data.get('custodian') or '',
                'status': cleaned_data.get('status') or 'u župi',
                'notes': cleaned_data.get('notes') or '',
            }
            registry_books = parish_data.setdefault('registryBooks', [])
            if registry_book_id:
                registry_book = next(
                    (
                        existing_book
                        for existing_book in registry_books
                        if existing_book.get('id') == registry_book_id
                    ),
                    None,
                )
                if registry_book:
                    registry_book.update(registry_book_payload)
            else:
                registry_books.append({
                    'id': f"rk_{uuid.uuid4().hex[:8]}",
                    **registry_book_payload,
                })
            parish_data_service.save(parish_data)
            messages.success(request, 'Matična knjiga spremljena.')
        else:
            messages.error(request, 'Provjerite unos.')
        return True

    if action_name == 'delete_registry_book' and page_slug == 'maticne-knjige':
        messages.error(
            request,
            'Matična knjiga se ne briše. Promijenite status i evidentirajte '
            'lokaciju, skrbnika te razlog promjene.',
        )
        return True

    if action_name == 'save_doc_binding' and page_slug == 'dokumenti':
        template_id = request.POST.get('template_id', '')
        document_template = get_template(template_id)
        if not document_template:
            messages.error(request, 'Predložak nije pronađen.')
            return True
        column_mapping = {}
        for field_name in request.POST:
            if field_name.startswith('map_'):
                column_mapping[field_name[4:]] = request.POST.get(
                    field_name,
                    '',
                )
        import_data = request.session.get('doc_import') or {}
        imported_rows = import_data.get('rows') or []
        save_binding(
            parish_data,
            template_id,
            document_template.get('name', ''),
            import_data.get('fileName', ''),
            column_mapping,
            len(imported_rows),
        )
        parish_data_service.save(parish_data)
        messages.success(request, 'Povezivanje stupaca spremljeno.')
        return True

    if action_name == 'delete_doc_binding' and page_slug == 'dokumenti':
        if delete_binding(
            parish_data,
            request.POST.get('binding_id', ''),
        ):
            parish_data_service.save(parish_data)
            messages.success(request, 'Povezivanje uklonjeno.')
        return True

    return False
