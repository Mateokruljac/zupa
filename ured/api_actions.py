"""API mutacije za zadatke i javne prijave župnog ureda."""
from __future__ import annotations

from datetime import date

from sakramenti.api_actions import upsert_sacrament
from sakramenti.forms_public import (
    compose_baptism_child_name,
    compose_baptism_godparents_line,
    compose_baptism_parents_line,
    compose_couple_name,
    compose_person_name,
    compose_school_class,
    compose_sponsor_name,
    compose_wedding_witnesses_line,
    pastoral_year_end,
)
from sakramenti.services.api_action_handlers.formation import (
    upsert_confirmation_candidate,
    upsert_first_communion_candidate,
)


def toggle_task(data: dict, action_payload: dict) -> dict:
    task_record = next(
        (
            task
            for task in data.get('tasks', [])
            if task.get('id') == action_payload.get('id')
        ),
        None,
    )
    if not task_record:
        return {'ok': False, 'error': 'not_found'}
    task_record['done'] = not task_record.get('done')
    return {'ok': True, 'item': task_record}


def mark_public_submission_imported(data: dict, action_payload: dict) -> dict:
    submission = next(
        (
            public_submission
            for public_submission in data.get('publicSubmissions', [])
            if public_submission.get('id') == action_payload.get('id')
        ),
        None,
    )
    if not submission:
        return {'ok': False, 'error': 'not_found'}
    submission['status'] = 'preuzeto'
    return {'ok': True}


def import_public_submission(data: dict, action_payload: dict) -> dict:
    submission = action_payload.get('submission') or action_payload
    submission_type = submission.get('type') or submission.get('formType')
    submission_type = {
        'prijava-krizma': 'krizma',
        'prijava-krsenje': 'krstenje',
        'prijava-pricest': 'pricest',
        'prijava-ukop': 'ukop',
        'prijava-vjencanje': 'vjencanje',
    }.get(submission_type, submission_type)
    form_data = submission.get('data') or {}
    year = int(action_payload.get('year') or date.today().year)
    submission_id = submission.get('id')

    if submission_type == 'krizma':
        upsert_confirmation_candidate(data, {
            'year': pastoral_year_end(form_data.get('pastoralna_godina')) or year,
            'name': compose_baptism_child_name(form_data) or '—',
            'birthDate': form_data.get('datum_rodjenja', ''),
            'school': form_data.get('skola', ''),
            'class': compose_school_class(form_data),
            'group': 'A',
            'baptized': form_data.get('datum_krstenja', ''),
            'sponsor': compose_sponsor_name(form_data),
            'status': 'upis',
            'oib': '',
        })
    elif submission_type == 'krstenje':
        upsert_sacrament(data, {
            'array_key': 'baptisms',
            'fields': {
                'childName': compose_baptism_child_name(form_data) or '—',
                'birthDate': form_data.get('datum_rodjenja', ''),
                'baptismDate': (
                    form_data.get('dogovoreni_datum')
                    or form_data.get('zeljeni_termin')
                    or ''
                ),
                'parents': compose_baptism_parents_line(form_data),
                'godparents': compose_baptism_godparents_line(form_data),
                'celebrant': '',
                'registryNo': '',
                'status': 'upis',
            },
        })
    elif submission_type == 'pricest':
        first_name = str(form_data.get('ime') or '').strip()
        last_name = str(form_data.get('prezime') or '').strip()
        if not first_name and not last_name:
            name_raw = str(form_data.get('ime_djeteta') or '—').strip()
            name_parts = name_raw.split()
            last_name = name_parts.pop() if len(name_parts) > 1 else ''
            first_name = ' '.join(name_parts) or name_raw
        upsert_first_communion_candidate(data, {
            'year': pastoral_year_end(form_data.get('pastoralna_godina')) or year,
            'fields': {
                'firstName': first_name,
                'lastName': last_name,
                'name': f'{first_name} {last_name}'.strip() or '—',
                'school': form_data.get('skola', ''),
                'class': compose_school_class(form_data),
                'parents': compose_baptism_parents_line(form_data),
                'paid': False,
            },
        })
    elif submission_type == 'vjencanje':
        couple = compose_couple_name(form_data) or '—'
        witnesses = compose_wedding_witnesses_line(form_data)
        groom_name = compose_person_name(
            form_data.get('zarucnik_ime'), form_data.get('zarucnik_prezime'),
        )
        bride_name = compose_person_name(
            form_data.get('zarucnica_ime'),
            form_data.get('zarucnica_civilno_prezime')
            or form_data.get('zarucnica_rodjeno_prezime'),
        )
        upsert_sacrament(data, {
            'array_key': 'weddings',
            'fields': {
                'couple': couple,
                'groomName': groom_name,
                'brideName': bride_name,
                'weddingDate': form_data.get('dogovoreni_datum', ''),
                'church': form_data.get('zupa_vjencanja') or '',
                'contact': (
                    f"{form_data.get('podnositelj') or ''} "
                    f"{form_data.get('telefon') or form_data.get('zarucnik_telefon') or form_data.get('zarucnica_telefon') or ''}"
                ).strip(),
                'celebrant': '',
                'preparatorySessions': 0,
                'documentsOk': False,
                'groomSponsor': compose_person_name(
                    form_data.get('svjedok1_ime'), form_data.get('svjedok1_prezime'),
                ),
                'brideSponsor': compose_person_name(
                    form_data.get('svjedok2_ime'), form_data.get('svjedok2_prezime'),
                ),
                'witnesses': witnesses,
                'status': 'upis',
                'stipend': 0,
                'stipendPaid': False,
            },
        })
    elif submission_type == 'ukop':
        upsert_sacrament(data, {
            'array_key': 'funerals',
            'fields': {
                'deceased': form_data.get('pokojnik') or '—',
                'deathDate': form_data.get('datum_smrti', ''),
                'funeralDate': form_data.get('zeljeni_datum', ''),
                'cemetery': form_data.get('groblje', ''),
                'cemeteryLocation': form_data.get('groblje', ''),
                'celebrant': '',
                'massPlanned': False,
                'massDate': form_data.get('zeljeni_datum', ''),
                'massTime': '',
                'familyContact': (
                    f"{form_data.get('kontakt', '')} "
                    f"{form_data.get('telefon', '')}"
                ).strip(),
                'status': 'upis',
                'stipend': 0,
                'stipendPaid': False,
            },
        })
    else:
        return {'ok': False, 'error': 'unknown_type'}

    if submission_id:
        mark_public_submission_imported(data, {'id': submission_id})
    return {'ok': True}
