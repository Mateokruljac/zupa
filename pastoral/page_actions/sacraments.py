"""POST akcije za pojedinačne sakramentalne evidencije."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.db import transaction

from pastoral.forms import (
    AnointingForm,
    BaptismForm,
    FuneralForm,
    WeddingForm,
)
from pastoral.services.mutations import (
    add_sacrament_record,
    delete_sacrament,
    update_sacrament_record,
)
from pastoral.services.baptism_records import (
    cancel_synchronized_baptism,
    synchronize_baptism_record,
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
