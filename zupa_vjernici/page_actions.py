"""POST akcije za obitelji, ulice i pastoralne posjete."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages

from pastoral.services.api_action_handlers.shared import normalize_parish_data
from zupa_vjernici.api_actions import (
    create_family,
    delete_street,
    delete_visit,
    toggle_visit_done,
    update_family,
    update_family_notes,
    upsert_contribution,
    upsert_family_member,
    upsert_street,
    upsert_visit,
)
from django_multitenant.schema import with_tenant_schema
from zupa_vjernici.forms import (
    FamilyContributionForm,
    FamilyForm,
    FamilyMemberForm,
    FamilyNotesForm,
    StreetForm,
    VisitForm,
)

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


@with_tenant_schema
def handle_family_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
    if page_slug != 'obitelji':
        return False

    if action_name == 'save_family_member':
        family_member_form = FamilyMemberForm(request.POST)
        if family_member_form.is_valid():
            cleaned_member = family_member_form.cleaned_data
            birth_date = cleaned_member.get('birth_date')
            action_result = upsert_family_member(parish_data, {
                'family_id': request.POST.get('family_id', ''),
                'member_id': request.POST.get('member_id', ''),
                'given_name': cleaned_member.get('given_name') or '',
                'surname': cleaned_member.get('surname') or '',
                'relation': cleaned_member.get('relation') or '',
                'birth_date': birth_date.isoformat() if birth_date else '',
                'notes': cleaned_member.get('notes') or '',
            })
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(
                    request,
                    'Član obitelji je spremljen.'
                    if request.POST.get('member_id')
                    else 'Član obitelji je dodan.',
                )
            else:
                messages.error(
                    request,
                    'Član obitelji nije mogao biti spremljen.',
                )
        else:
            messages.error(request, 'Provjerite podatke člana obitelji.')
        return True

    if action_name == 'save_family_contribution':
        contribution_form = FamilyContributionForm(request.POST)
        if contribution_form.is_valid():
            cleaned_data = contribution_form.cleaned_data
            paid_at = cleaned_data.get('paid_at')
            action_result = upsert_contribution(parish_data, {
                'family_id': request.POST.get('family_id', ''),
                'contribution_id': cleaned_data.get('contribution_id') or '',
                'year': cleaned_data['year'],
                'category': cleaned_data['category'],
                'amount': cleaned_data['amount'],
                'paid_at': paid_at.isoformat() if paid_at else '',
                'notes': cleaned_data.get('notes') or '',
            })
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Lukno i darovi su spremljeni.')
            else:
                messages.error(
                    request,
                    'Financijski zapis nije mogao biti spremljen.',
                )
        else:
            messages.error(request, 'Provjerite podatke lukna i darova.')
        return True

    if action_name == 'update_family_notes':
        notes_form = FamilyNotesForm(request.POST)
        if notes_form.is_valid():
            action_result = update_family_notes(parish_data, {
                'family_id': request.POST.get('family_id', ''),
                'pastoral_notes': notes_form.cleaned_data.get('pastoral_notes') or '',
            })
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Bilješka je spremljena.')
            else:
                messages.error(request, 'Bilješka nije mogla biti spremljena.')
        else:
            messages.error(request, 'Provjerite tekst bilješke.')
        return True

    if action_name == 'add_street':
        street_form = StreetForm(request.POST)
        if not street_form.is_valid():
            request.pastoral_json_response = {
                'ok': False,
                'error': 'invalid_street',
            }
            return True
        cleaned_street = street_form.cleaned_data
        street_name = cleaned_street['name'].strip()
        existing_street = next(
            (
                street
                for street in parish_data.get('streets', [])
                if (street.get('name') or '').strip().casefold() == street_name.casefold()
            ),
            None,
        )
        if existing_street:
            request.pastoral_json_response = {
                'ok': True,
                'street': {
                    'id': existing_street.get('id'),
                    'name': existing_street.get('name') or '',
                    'city': existing_street.get('city') or '',
                },
            }
            return True
        normalize_parish_data(parish_data)
        operation_result = upsert_street(parish_data, {
            'name': street_name,
            'city': cleaned_street.get('city') or '',
            'notes': cleaned_street.get('notes') or '',
        })
        if not operation_result.get('ok'):
            request.pastoral_json_response = {
                'ok': False,
                'error': 'street_not_saved',
            }
            return True
        parish_data_service.save(parish_data)
        created_street = operation_result['item']
        request.pastoral_json_response = {
            'ok': True,
            'street': {
                'id': created_street.get('id'),
                'name': created_street.get('name') or '',
                'city': created_street.get('city') or '',
            },
        }
        return True

    if action_name not in {'add_family', 'update_family'}:
        return False

    family_form = FamilyForm(
        request.POST,
        streets=parish_data.get('streets', []),
    )
    if family_form.is_valid():
        cleaned_data = family_form.cleaned_data
        if action_name == 'add_family':
            action_result = create_family(parish_data, cleaned_data)
        else:
            update_payload = {
                'id': request.POST.get('family_id', ''),
                **cleaned_data,
            }
            if 'pastoral_notes' not in request.POST:
                update_payload.pop('pastoral_notes', None)
            action_result = update_family(parish_data, update_payload)
        if action_result.get('ok'):
            parish_data_service.save(parish_data)
            success_message = (
                'Karton obitelji je dodan.'
                if action_name == 'add_family'
                else 'Podaci obitelji su spremljeni.'
            )
            messages.success(request, success_message)
        else:
            messages.error(
                request,
                'Karton obitelji nije mogao biti spremljen.',
            )
    else:
        messages.error(request, 'Provjerite osnovne podatke obitelji.')
    return True


@with_tenant_schema
def handle_streets_and_visits_action(
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
                'city': cleaned_data.get('city') or '',
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
        operation_result = delete_street(
            parish_data,
            {'id': request.POST.get('street_id', '')},
        )
        if operation_result.get('ok'):
            parish_data_service.save(parish_data)
            messages.success(request, 'Ulica obrisana.')
        elif operation_result.get('error') == 'has_families':
            count = operation_result.get('family_count') or 0
            messages.error(
                request,
                (
                    f'Ulicu nije moguće obrisati dok na njoj postoji '
                    f'{count} povezanih obitelji. Premjestite ili odspojite '
                    f'obitelji pa pokušajte ponovno.'
                ),
            )
        else:
            messages.error(request, 'Ulica nije obrisana.')
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
        operation_result = toggle_visit_done(parish_data, {'id': visit_id})
        if operation_result.get('ok'):
            parish_data_service.save(parish_data)
            messages.success(request, 'Status posjeta ažuriran.')
        return True

    if action_name == 'delete_visit' and page_slug == 'posjete':
        operation_result = delete_visit(
            parish_data,
            {'id': request.POST.get('visit_id', '')},
        )
        if operation_result.get('ok'):
            parish_data_service.save(parish_data)
            messages.success(request, 'Posjet obrisan.')
        else:
            messages.error(request, 'Posjet nije obrisan.')
        return True

    return False


def handle_parish_community_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
    if handle_family_action(
        request,
        page_slug,
        action_name,
        parish_data,
        parish_data_service,
    ):
        return True
    return handle_streets_and_visits_action(
        request,
        page_slug,
        action_name,
        parish_data,
        parish_data_service,
    )
