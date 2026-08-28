"""POST akcije za obitelji, ulice i pastoralne posjete."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages

from pastoral.services.api_actions import normalize_parish_data
from zupa_vjernici.api_actions import (
    create_family,
    delete_street,
    toggle_visit_done,
    update_family,
    update_family_notes,
    upsert_contribution,
    upsert_family_member,
    upsert_street,
    upsert_visit,
)
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
            action_result = upsert_family_member(parish_data, {
                'family_id': request.POST.get('family_id', ''),
                'member_id': request.POST.get('member_id', ''),
                **family_member_form.cleaned_data,
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
            lukno_paid_at = cleaned_data.get('lukno_paid_at')
            donation_date = cleaned_data.get('donation_date')
            action_result = upsert_contribution(parish_data, {
                'family_id': request.POST.get('family_id', ''),
                'year': cleaned_data['year'],
                'lukno_amount': cleaned_data['lukno_amount'],
                'lukno_paid': cleaned_data.get('lukno_paid', False),
                'lukno_paid_at': (
                    lukno_paid_at.isoformat() if lukno_paid_at else ''
                ),
                'church_donation': cleaned_data.get('church_donation') or 0,
                'donation_date': (
                    donation_date.isoformat() if donation_date else ''
                ),
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
            action_result = update_family(parish_data, {
                'id': request.POST.get('family_id', ''),
                **cleaned_data,
            })
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

    if action_name == 'upsert_visit' and page_slug == 'posjete':
        visit_form = VisitForm(
            request.POST,
            families=parish_data.get('families', []),
        )
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
