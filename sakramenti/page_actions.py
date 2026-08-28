"""POST akcije za sakramente i sakramentalnu pripravu."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.db import transaction

from sakramenti.services.baptism_records import (
    cancel_synchronized_baptism,
    synchronize_baptism_record,
)
from sakramenti.forms import (
    AnointingForm,
    BaptismForm,
    ConfirmationCandidateForm,
    ConfirmationGroupForm,
    ConfirmationYearCreateForm,
    ConfirmationYearForm,
    FirstCommunionCandidateForm,
    FirstCommunionGroupForm,
    FirstCommunionYearCreateForm,
    FirstCommunionYearForm,
    FuneralForm,
    WeddingForm,
)
from sakramenti.services.api_action_handlers.formation import (
    create_confirmation_year,
    create_first_communion_year,
    delete_confirmation_candidate,
    delete_first_communion_candidate,
    update_confirmation_group,
    update_first_communion_group,
    upsert_confirmation_candidate,
    upsert_first_communion_candidate,
)
from sakramenti.services.sacrament_mutations import (
    add_sacrament_record,
    delete_sacrament,
    update_sacrament_record,
)

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


def handle_sacrament_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
    if action_name == 'add_baptism' and page_slug == 'krsenja':
        baptism_form = BaptismForm(request.POST)
        if baptism_form.is_valid():
            cleaned_data = baptism_form.cleaned_data
            with transaction.atomic():
                baptism_record = add_sacrament_record(parish_data, 'baptisms', {
                    'childName': cleaned_data['child_name'],
                    'birthDate': (
                        cleaned_data['birth_date'].isoformat()
                        if cleaned_data.get('birth_date')
                        else ''
                    ),
                    'baptismDate': (
                        cleaned_data['baptism_date'].isoformat()
                        if cleaned_data.get('baptism_date')
                        else ''
                    ),
                    'parents': cleaned_data['parents'],
                    'godparents': cleaned_data.get('godparents') or '',
                    'godparentCertReceived': cleaned_data.get(
                        'godparent_certificate_received',
                        False,
                    ),
                    'celebrant': cleaned_data.get('celebrant') or '',
                    'registryNo': cleaned_data.get('registry_number') or '',
                    'status': cleaned_data.get('status') or 'planirano',
                    'stipend': float(cleaned_data.get('stipend') or 0),
                    'stipendPaid': False,
                })
                parish_data_service.save(parish_data)
                synchronize_baptism_record(
                    parish_data_service.parish,
                    baptism_record,
                    actor=request.user,
                )
            messages.success(request, 'Krštenje dodano.')
        return True

    if action_name == 'update_baptism' and page_slug == 'krsenja':
        baptism_form = BaptismForm(request.POST)
        if baptism_form.is_valid():
            cleaned_data = baptism_form.cleaned_data
            was_updated = update_sacrament_record(
                parish_data,
                'baptisms',
                request.POST.get('record_id', ''),
                {
                    'childName': cleaned_data['child_name'],
                    'birthDate': (
                        cleaned_data['birth_date'].isoformat()
                        if cleaned_data.get('birth_date')
                        else ''
                    ),
                    'baptismDate': (
                        cleaned_data['baptism_date'].isoformat()
                        if cleaned_data.get('baptism_date')
                        else ''
                    ),
                    'parents': cleaned_data['parents'],
                    'godparents': cleaned_data.get('godparents') or '',
                    'godparentCertReceived': cleaned_data.get(
                        'godparent_certificate_received',
                        False,
                    ),
                    'celebrant': cleaned_data.get('celebrant') or '',
                    'registryNo': cleaned_data.get('registry_number') or '',
                    'status': cleaned_data.get('status') or 'planirano',
                    'stipend': float(cleaned_data.get('stipend') or 0),
                },
            )
            if was_updated:
                baptism_record = next(
                    baptism
                    for baptism in parish_data.get('baptisms', [])
                    if baptism.get('id') == request.POST.get('record_id', '')
                )
                with transaction.atomic():
                    parish_data_service.save(parish_data)
                    synchronize_baptism_record(
                        parish_data_service.parish,
                        baptism_record,
                        actor=request.user,
                    )
                messages.success(request, 'Krštenje ažurirano.')
        return True

    if action_name == 'delete_baptism' and page_slug == 'krsenja':
        record_identifier = request.POST.get('record_id', '')
        if delete_sacrament(parish_data, 'baptisms', record_identifier):
            with transaction.atomic():
                parish_data_service.save(parish_data)
                cancel_synchronized_baptism(
                    parish_data_service.parish,
                    record_identifier,
                    actor=request.user,
                )
            messages.success(request, 'Zapis obrisan.')
        return True

    if action_name == 'add_wedding' and page_slug == 'vjencanja':
        wedding_form = WeddingForm(request.POST)
        if wedding_form.is_valid():
            cleaned_data = wedding_form.cleaned_data
            add_sacrament_record(parish_data, 'weddings', {
                'couple': cleaned_data['couple'],
                'weddingDate': (
                    cleaned_data['wedding_date'].isoformat()
                    if cleaned_data.get('wedding_date')
                    else ''
                ),
                'church': cleaned_data.get('church') or '',
                'contact': cleaned_data.get('contact') or '',
                'celebrant': cleaned_data.get('celebrant') or '',
                'preparatorySessions': cleaned_data.get('preparatory_sessions') or 0,
                'documentsOk': cleaned_data.get('documents_ok', False),
                'witnesses': cleaned_data.get('witnesses') or '',
                'status': cleaned_data.get('status') or 'planirano',
                'stipend': float(cleaned_data.get('stipend') or 0),
                'stipendPaid': False,
            })
            parish_data_service.save(parish_data)
            messages.success(request, 'Vjenčanje dodano.')
        return True

    if action_name == 'update_wedding' and page_slug == 'vjencanja':
        wedding_form = WeddingForm(request.POST)
        if wedding_form.is_valid():
            cleaned_data = wedding_form.cleaned_data
            was_updated = update_sacrament_record(
                parish_data,
                'weddings',
                request.POST.get('record_id', ''),
                {
                    'couple': cleaned_data['couple'],
                    'weddingDate': (
                        cleaned_data['wedding_date'].isoformat()
                        if cleaned_data.get('wedding_date')
                        else ''
                    ),
                    'church': cleaned_data.get('church') or '',
                    'contact': cleaned_data.get('contact') or '',
                    'celebrant': cleaned_data.get('celebrant') or '',
                    'preparatorySessions': cleaned_data.get('preparatory_sessions') or 0,
                    'documentsOk': cleaned_data.get('documents_ok', False),
                    'witnesses': cleaned_data.get('witnesses') or '',
                    'status': cleaned_data.get('status') or 'planirano',
                    'stipend': float(cleaned_data.get('stipend') or 0),
                },
            )
            if was_updated:
                parish_data_service.save(parish_data)
                messages.success(request, 'Vjenčanje ažurirano.')
        return True

    if action_name == 'delete_wedding' and page_slug == 'vjencanja':
        if delete_sacrament(
            parish_data,
            'weddings',
            request.POST.get('record_id', ''),
        ):
            parish_data_service.save(parish_data)
            messages.success(request, 'Zapis obrisan.')
        return True

    if action_name == 'add_funeral' and page_slug == 'pogrebi':
        funeral_form = FuneralForm(request.POST)
        if funeral_form.is_valid():
            cleaned_data = funeral_form.cleaned_data
            add_sacrament_record(parish_data, 'funerals', {
                'deceased': cleaned_data['deceased'],
                'funeralDate': (
                    cleaned_data['funeral_date'].isoformat()
                    if cleaned_data.get('funeral_date')
                    else ''
                ),
                'cemetery': cleaned_data.get('cemetery') or '',
                'familyContact': cleaned_data.get('family_contact') or '',
                'celebrant': cleaned_data.get('celebrant') or '',
                'massPlanned': cleaned_data.get('mass_planned', False),
                'massDate': (
                    cleaned_data['mass_date'].isoformat()
                    if cleaned_data.get('mass_date')
                    else ''
                ),
                'massTime': (
                    cleaned_data['mass_time'].strftime('%H:%M')
                    if cleaned_data.get('mass_time')
                    else ''
                ),
                'status': cleaned_data.get('status') or 'planirano',
                'stipend': float(cleaned_data.get('stipend') or 0),
                'stipendPaid': False,
            })
            parish_data_service.save(parish_data)
            messages.success(request, 'Pogreb dodan.')
        return True

    if action_name == 'update_funeral' and page_slug == 'pogrebi':
        funeral_form = FuneralForm(request.POST)
        if funeral_form.is_valid():
            cleaned_data = funeral_form.cleaned_data
            was_updated = update_sacrament_record(
                parish_data,
                'funerals',
                request.POST.get('record_id', ''),
                {
                    'deceased': cleaned_data['deceased'],
                    'funeralDate': (
                        cleaned_data['funeral_date'].isoformat()
                        if cleaned_data.get('funeral_date')
                        else ''
                    ),
                    'cemetery': cleaned_data.get('cemetery') or '',
                    'familyContact': cleaned_data.get('family_contact') or '',
                    'celebrant': cleaned_data.get('celebrant') or '',
                    'massPlanned': cleaned_data.get('mass_planned', False),
                    'massDate': (
                        cleaned_data['mass_date'].isoformat()
                        if cleaned_data.get('mass_date')
                        else ''
                    ),
                    'massTime': (
                        cleaned_data['mass_time'].strftime('%H:%M')
                        if cleaned_data.get('mass_time')
                        else ''
                    ),
                    'status': cleaned_data.get('status') or 'planirano',
                    'stipend': float(cleaned_data.get('stipend') or 0),
                },
            )
            if was_updated:
                parish_data_service.save(parish_data)
                messages.success(request, 'Sprovod ažuriran.')
        return True

    if action_name == 'delete_funeral' and page_slug == 'pogrebi':
        if delete_sacrament(
            parish_data,
            'funerals',
            request.POST.get('record_id', ''),
        ):
            parish_data_service.save(parish_data)
            messages.success(request, 'Zapis obrisan.')
        return True

    if action_name == 'add_anointing' and page_slug == 'pomazanje':
        anointing_form = AnointingForm(request.POST)
        if anointing_form.is_valid():
            cleaned_data = anointing_form.cleaned_data
            add_sacrament_record(parish_data, 'anointing', {
                'person': cleaned_data['person'],
                'scheduled': (
                    cleaned_data['scheduled'].isoformat()
                    if cleaned_data.get('scheduled')
                    else ''
                ),
                'priest': cleaned_data.get('priest') or '',
                'address': cleaned_data.get('address') or '',
                'contact': cleaned_data.get('contact') or '',
                'status': cleaned_data.get('status') or 'planirano',
            })
            parish_data_service.save(parish_data)
            messages.success(request, 'Pomazanje dodano.')
        return True

    if action_name == 'update_anointing' and page_slug == 'pomazanje':
        anointing_form = AnointingForm(request.POST)
        if anointing_form.is_valid():
            cleaned_data = anointing_form.cleaned_data
            was_updated = update_sacrament_record(
                parish_data,
                'anointing',
                request.POST.get('record_id', ''),
                {
                    'person': cleaned_data['person'],
                    'scheduled': (
                        cleaned_data['scheduled'].isoformat()
                        if cleaned_data.get('scheduled')
                        else ''
                    ),
                    'priest': cleaned_data.get('priest') or '',
                    'address': cleaned_data.get('address') or '',
                    'contact': cleaned_data.get('contact') or '',
                    'status': cleaned_data.get('status') or 'planirano',
                },
            )
            if was_updated:
                parish_data_service.save(parish_data)
                messages.success(request, 'Pomazanje ažurirano.')
        return True

    if action_name == 'delete_anointing' and page_slug == 'pomazanje':
        if delete_sacrament(
            parish_data,
            'anointing',
            request.POST.get('record_id', ''),
        ):
            parish_data_service.save(parish_data)
            messages.success(request, 'Zapis obrisan.')
        return True

    return False


def _optional_date(calendar_date) -> str:
    return calendar_date.isoformat() if calendar_date else ''


def _confirmation_candidate_payload(
    cleaned_data: dict,
    candidate_id: str = '',
    existing_oib: str = '',
) -> dict:
    return {
        'id': candidate_id,
        'year': cleaned_data['year'],
        'name': cleaned_data['name'],
        'birthDate': _optional_date(cleaned_data.get('birth_date')),
        'school': cleaned_data.get('school') or '',
        'class': cleaned_data.get('school_class') or '',
        'group': cleaned_data.get('formation_group') or '',
        'baptized': _optional_date(cleaned_data.get('baptism_date')),
        'sponsor': cleaned_data.get('sponsor') or '',
        'status': cleaned_data['status'],
        'oib': existing_oib,
    }


def _existing_confirmation_candidate_oib(
    parish_data: dict,
    confirmation_year: int,
    candidate_id: str,
) -> str:
    confirmation_group = next(
        (
            group
            for group in parish_data.get('confirmations', [])
            if group.get('year') == confirmation_year
        ),
        {},
    )
    confirmation_candidate = next(
        (
            candidate
            for candidate in confirmation_group.get('candidates', [])
            if candidate.get('id') == candidate_id
        ),
        {},
    )
    return confirmation_candidate.get('oib', '')


def _first_communion_candidate_payload(
    cleaned_data: dict,
    candidate_id: str = '',
) -> dict:
    first_name = cleaned_data['first_name']
    last_name = cleaned_data['last_name']
    return {
        'id': candidate_id,
        'year': cleaned_data['year'],
        'fields': {
            'firstName': first_name,
            'lastName': last_name,
            'name': f'{first_name} {last_name}'.strip(),
            'school': cleaned_data.get('school') or '',
            'class': cleaned_data.get('school_class') or '',
            'parents': cleaned_data.get('parents') or '',
            'status': cleaned_data.get('status') or 'priprema',
            'paid': cleaned_data.get('paid', False),
        },
    }


def handle_formation_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
    if page_slug == 'krizma' and action_name == 'add_confirmation_year':
        confirmation_year_create_form = ConfirmationYearCreateForm(request.POST)
        if confirmation_year_create_form.is_valid():
            cleaned_data = confirmation_year_create_form.cleaned_data
            confirmation_year = cleaned_data['year']
            action_result = create_confirmation_year(
                parish_data,
                {
                    'year': confirmation_year,
                    'ceremony_date': _optional_date(
                        cleaned_data.get('ceremony_date'),
                    ),
                    'bishop': cleaned_data.get('bishop') or '',
                    'group_fee': cleaned_data.get('group_fee') or 0,
                    'group_fee_paid': cleaned_data.get(
                        'group_fee_paid',
                        False,
                    ),
                },
            )
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(
                    request,
                    f'Godina krizme {confirmation_year} je dodana.',
                )
            else:
                messages.error(request, 'Ta godina krizme već postoji.')
        else:
            messages.error(request, 'Provjerite podatke nove godine krizme.')
        return True

    if page_slug == 'krizma' and action_name == 'save_confirmation_group':
        confirmation_group_form = ConfirmationGroupForm(request.POST)
        if confirmation_group_form.is_valid():
            cleaned_data = confirmation_group_form.cleaned_data
            action_payload = {
                'year': cleaned_data['year'],
                'ceremony_date': _optional_date(cleaned_data.get('ceremony_date')),
                'bishop': cleaned_data.get('bishop') or '',
                'group_fee': cleaned_data.get('group_fee') or 0,
                'group_fee_paid': cleaned_data.get('group_fee_paid', False),
            }
            action_result = update_confirmation_group(
                parish_data,
                action_payload,
            )
            if action_result.get('error') == 'not_found':
                action_result = create_confirmation_year(
                    parish_data,
                    action_payload,
                )
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Podaci godine krizme su spremljeni.')
            else:
                messages.error(request, 'Godina krizme nije mogla biti spremljena.')
        else:
            messages.error(
                request,
                'Provjerite samo podatke godine krizme; kandidati nisu mijenjani.',
            )
        return True

    if page_slug == 'krizma' and action_name == 'add_confirmation_candidate':
        confirmation_candidate_form = ConfirmationCandidateForm(request.POST)
        if confirmation_candidate_form.is_valid():
            cleaned_data = confirmation_candidate_form.cleaned_data
            action_result = upsert_confirmation_candidate(
                parish_data,
                _confirmation_candidate_payload(cleaned_data),
            )
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Krizmanik je dodan u odabranu godinu.')
        else:
            messages.error(
                request,
                'Provjerite podatke krizmanika; podaci godine ostali su spremljeni.',
            )
        return True

    if page_slug == 'krizma' and action_name == 'update_confirmation_candidate':
        confirmation_candidate_form = ConfirmationCandidateForm(request.POST)
        if confirmation_candidate_form.is_valid():
            cleaned_data = confirmation_candidate_form.cleaned_data
            candidate_id = request.POST.get('candidate_id', '')
            action_result = upsert_confirmation_candidate(
                parish_data,
                _confirmation_candidate_payload(
                    cleaned_data,
                    candidate_id,
                    _existing_confirmation_candidate_oib(
                        parish_data,
                        cleaned_data['year'],
                        candidate_id,
                    ),
                ),
            )
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Podaci krizmanika su spremljeni.')
            else:
                messages.error(request, 'Krizmanik nije pronađen.')
        else:
            messages.error(request, 'Provjerite podatke krizmanika.')
        return True

    if page_slug == 'krizma' and action_name == 'delete_confirmation_candidate':
        action_result = delete_confirmation_candidate(parish_data, {
            'year': request.POST.get('year'),
            'id': request.POST.get('candidate_id', ''),
        })
        if action_result.get('ok'):
            parish_data_service.save(parish_data)
            messages.success(request, 'Krizmanik je obrisan.')
        else:
            messages.error(request, 'Krizmanik nije pronađen.')
        return True

    if (
        page_slug == 'prva-pricest'
        and action_name == 'add_first_communion_candidate'
    ):
        first_communion_candidate_form = FirstCommunionCandidateForm(
            request.POST
        )
        if first_communion_candidate_form.is_valid():
            cleaned_data = first_communion_candidate_form.cleaned_data
            action_result = upsert_first_communion_candidate(
                parish_data,
                _first_communion_candidate_payload(cleaned_data),
            )
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Prvopričesnik je dodan u odabranu godinu.')
        else:
            messages.error(request, 'Provjerite podatke prvopričesnika.')
        return True

    if page_slug == 'prva-pricest' and action_name == 'add_first_communion_year':
        first_communion_year_create_form = FirstCommunionYearCreateForm(
            request.POST,
        )
        if first_communion_year_create_form.is_valid():
            cleaned_data = first_communion_year_create_form.cleaned_data
            first_communion_year = cleaned_data['year']
            action_result = create_first_communion_year(
                parish_data,
                {
                    'year': first_communion_year,
                    'group_name': cleaned_data.get('group_name') or '',
                    'ceremony_date': _optional_date(
                        cleaned_data.get('ceremony_date'),
                    ),
                    'celebrant': cleaned_data.get('celebrant') or '',
                    'group_fee': cleaned_data.get('group_fee') or 0,
                    'group_fee_paid': cleaned_data.get(
                        'group_fee_paid',
                        False,
                    ),
                },
            )
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(
                    request,
                    f'Godina prve pričesti {first_communion_year} je dodana.',
                )
            else:
                messages.error(request, 'Ta godina prve pričesti već postoji.')
        else:
            messages.error(request, 'Provjerite podatke nove godine prve pričesti.')
        return True

    if page_slug == 'prva-pricest' and action_name == 'save_first_communion_group':
        first_communion_group_form = FirstCommunionGroupForm(request.POST)
        if first_communion_group_form.is_valid():
            cleaned_data = first_communion_group_form.cleaned_data
            action_result = update_first_communion_group(parish_data, {
                'year': cleaned_data['year'],
                'group_name': cleaned_data.get('group_name') or '',
                'ceremony_date': _optional_date(cleaned_data.get('ceremony_date')),
                'celebrant': cleaned_data.get('celebrant') or '',
                'group_fee': cleaned_data.get('group_fee') or 0,
                'group_fee_paid': cleaned_data.get('group_fee_paid', False),
            })
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Podaci godine prve pričesti su spremljeni.')
            else:
                messages.error(request, 'Godina prve pričesti nije pronađena.')
        else:
            messages.error(request, 'Provjerite podatke godine prve pričesti.')
        return True

    if (
        page_slug == 'prva-pricest'
        and action_name == 'update_first_communion_candidate'
    ):
        first_communion_candidate_form = FirstCommunionCandidateForm(request.POST)
        if first_communion_candidate_form.is_valid():
            action_result = upsert_first_communion_candidate(
                parish_data,
                _first_communion_candidate_payload(
                    first_communion_candidate_form.cleaned_data,
                    request.POST.get('candidate_id', ''),
                ),
            )
            if action_result.get('ok'):
                parish_data_service.save(parish_data)
                messages.success(request, 'Podaci prvopričesnika su spremljeni.')
            else:
                messages.error(request, 'Prvopričesnik nije pronađen.')
        else:
            messages.error(request, 'Provjerite podatke prvopričesnika.')
        return True

    if (
        page_slug == 'prva-pricest'
        and action_name == 'delete_first_communion_candidate'
    ):
        action_result = delete_first_communion_candidate(parish_data, {
            'year': request.POST.get('year'),
            'id': request.POST.get('candidate_id', ''),
        })
        if action_result.get('ok'):
            parish_data_service.save(parish_data)
            messages.success(request, 'Prvopričesnik je obrisan.')
        else:
            messages.error(request, 'Prvopričesnik nije pronađen.')
        return True

    return False

def handle_sakramenti_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
    if handle_sacrament_action(
        request,
        page_slug,
        action_name,
        parish_data,
        parish_data_service,
    ):
        return True
    return handle_formation_action(
        request,
        page_slug,
        action_name,
        parish_data,
        parish_data_service,
    )

