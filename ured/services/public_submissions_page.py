"""Pregled, provjera i uvoz javnih prijava u župnu evidenciju."""
from __future__ import annotations

from datetime import date, datetime


FORM_LABELS = {
    'prijava-krizma': 'Krizma',
    'prijava-krsenje': 'Krštenje',
    'prijava-pricest': 'Prva pričest',
    'prijava-ukop': 'Ukop / pogreb',
    'prijava-vjencanje': 'Vjenčanje',
}

DISPLAY_SECTIONS = {
    'prijava-krizma': (
        ('Prijava', ('pastoralna_godina', 'podnositelj', 'email')),
        (
            'Krizmanik',
            (
                'ime', 'prezime', 'spol', 'datum_rodjenja', 'mjesto_rodjenja',
                'zupa_stanovanja', 'djetetov_email', 'djetetov_telefon', 'adresa',
            ),
        ),
        (
            'Škola i priprava',
            ('skola', 'razred_broj', 'razred_slovo', 'vjeronauk', 'vjeroucitelj'),
        ),
        ('Sakramenti', ('datum_krstenja', 'zupa_krstenja', 'zupa_pricesti')),
        (
            'Roditelji',
            (
                'otac_ime', 'otac_prezime', 'otac_telefon', 'otac_email',
                'majka_ime', 'majka_prezime', 'majka_djevojacko',
                'majka_telefon', 'majka_email',
            ),
        ),
        (
            'Kum',
            ('kum_ime', 'kum_prezime', 'kum_spol', 'kum_telefon', 'kum_email', 'napomena'),
        ),
    ),
    'prijava-pricest': (
        ('Prijava', ('pastoralna_godina', 'podnositelj', 'email')),
        (
            'Prvopričesnik',
            (
                'ime', 'prezime', 'spol', 'datum_rodjenja', 'mjesto_rodjenja',
                'zupa_stanovanja', 'djetetov_email', 'djetetov_telefon', 'adresa',
            ),
        ),
        (
            'Škola i priprava',
            ('skola', 'razred_broj', 'razred_slovo', 'vjeronauk', 'vjeroucitelj'),
        ),
        ('Krštenje', ('datum_krstenja', 'zupa_krstenja')),
        (
            'Roditelji',
            (
                'otac_ime', 'otac_prezime', 'otac_telefon', 'otac_email',
                'majka_ime', 'majka_prezime', 'majka_djevojacko',
                'majka_telefon', 'majka_email', 'napomena',
            ),
        ),
    ),
    'prijava-krsenje': (
        ('Termin', ('dogovoreni_datum', 'vrijeme', 'podnositelj', 'telefon', 'email')),
        (
            'Krštenik',
            (
                'ime', 'prezime', 'spol', 'datum_rodjenja', 'mjesto_rodjenja',
                'zupa_stanovanja', 'vjencani_status_roditelja', 'adresa',
            ),
        ),
        (
            'Otac',
            (
                'otac_poznat', 'otac_ime', 'otac_prezime', 'otac_datum_rodjenja',
                'otac_vjeroispovijest', 'otac_mjesto_rodjenja', 'otac_telefon',
            ),
        ),
        (
            'Majka',
            (
                'majka_poznata', 'majka_ime', 'majka_prezime', 'majka_djevojacko',
                'majka_datum_rodjenja', 'majka_vjeroispovijest',
                'majka_mjesto_rodjenja', 'majka_telefon',
            ),
        ),
        (
            'Kumovi',
            (
                'kum1_ime', 'kum1_prezime', 'kum1_spol', 'kum1_zupa',
                'kum2_ime', 'kum2_prezime', 'kum2_spol', 'kum2_zupa', 'napomena',
            ),
        ),
    ),
    'prijava-vjencanje': (
        (
            'Župa',
            (
                'dogovoreni_datum', 'vrijeme', 'podnositelj', 'email',
                'zupa_vjencanja_ista', 'zupa_vjencanja',
            ),
        ),
        (
            'Zaručnik',
            (
                'zarucnik_ime', 'zarucnik_prezime', 'zarucnik_datum_rodjenja',
                'zarucnik_mjesto_rodjenja', 'zarucnik_vjeroispovijest',
                'zarucnik_mjesto', 'zarucnik_ulica', 'zarucnik_kbr',
                'zarucnik_zupa_stanovanja', 'zarucnik_telefon', 'zarucnik_email',
                'zarucnik_otac_ime', 'zarucnik_otac_prezime',
                'zarucnik_majka_ime', 'zarucnik_majka_djevojacko',
                'zarucnik_datum_krstenja', 'zarucnik_zupa_krstenja',
                'zarucnik_datum_krizme', 'zarucnik_zupa_krizme',
                'zarucnik_druge_zupe',
            ),
        ),
        (
            'Zaručnica',
            (
                'zarucnica_ime', 'zarucnica_rodjeno_prezime',
                'zarucnica_civilno_prezime', 'zarucnica_datum_rodjenja',
                'zarucnica_mjesto_rodjenja', 'zarucnica_vjeroispovijest',
                'zarucnica_mjesto', 'zarucnica_ulica', 'zarucnica_kbr',
                'zarucnica_zupa_stanovanja', 'zarucnica_telefon',
                'zarucnica_email', 'zarucnica_otac_ime',
                'zarucnica_otac_prezime', 'zarucnica_majka_ime',
                'zarucnica_majka_djevojacko', 'zarucnica_datum_krstenja',
                'zarucnica_zupa_krstenja', 'zarucnica_datum_krizme',
                'zarucnica_zupa_krizme', 'zarucnica_druge_zupe',
            ),
        ),
        (
            'Kumovi',
            (
                'svjedok1_ime', 'svjedok1_prezime', 'svjedok1_spol',
                'svjedok1_mjesto', 'svjedok1_ulica', 'svjedok1_kbr',
                'svjedok2_ime', 'svjedok2_prezime', 'svjedok2_spol',
                'svjedok2_mjesto', 'svjedok2_ulica', 'svjedok2_kbr',
                'napomena', 'adresa',
            ),
        ),
    ),
}

WIDE_FIELD_NAMES = {
    'adresa', 'napomena', 'skola', 'podnositelj', 'email',
    'zupa_stanovanja', 'zupa_krstenja', 'zupa_pricesti', 'vjeroucitelj', 'pastoralna_godina',
    'zupa_vjencanja', 'zupa_vjencanja_ista',
    'zarucnik_zupa_stanovanja', 'zarucnik_zupa_krstenja', 'zarucnik_zupa_krizme',
    'zarucnik_druge_zupe', 'zarucnik_ulica',
    'zarucnica_zupa_stanovanja', 'zarucnica_zupa_krstenja', 'zarucnica_zupa_krizme',
    'zarucnica_druge_zupe', 'zarucnica_ulica',
}


def _normalized_text(value) -> str:
    return str(value or '').strip().casefold()


def _section_title_for_field(form_type: str, field: dict) -> str | None:
    name = str(field.get('name') or '')
    spec = DISPLAY_SECTIONS.get(form_type) or ()
    if name:
        for title, names in spec:
            if name in names:
                return title
        return None
    label = _normalized_text(field.get('label'))
    if form_type == 'prijava-krizma':
        if any(token in label for token in ('pastoralna', 'podnositelj', 'e-mail za obavijesti', 'krizma će')):
            return 'Prijava'
        if any(token in label for token in ('škola', 'razred', 'vjeronauk', 'vjeroučitelj')):
            return 'Škola i priprava'
        if any(token in label for token in ('krštenj', 'pričest')):
            return 'Sakramenti'
        if any(token in label for token in ('kuma', 'kume')):
            return 'Kum'
        if any(token in label for token in ('oca', 'majke', 'djevojačko')):
            return 'Roditelji'
        return 'Krizmanik'
    if form_type == 'prijava-pricest':
        if any(token in label for token in ('pastoralna', 'podnositelj', 'e-mail za obavijesti')):
            return 'Prijava'
        if any(token in label for token in ('škola', 'razred', 'vjeronauk', 'vjeroučitelj')):
            return 'Škola i priprava'
        if 'krštenj' in label:
            return 'Krštenje'
        if any(token in label for token in ('oca', 'majke', 'djevojačko', 'napomena')):
            return 'Roditelji'
        return 'Prvopričesnik'
    if form_type == 'prijava-krsenje':
        if any(token in label for token in ('datum krštenja', 'vrijeme', 'podnositelj', 'kontakt telefon', 'e-mail za')):
            return 'Termin'
        if any(token in label for token in ('oca', 'otac')):
            return 'Otac'
        if any(token in label for token in ('majke', 'majka', 'djevojačko')):
            return 'Majka'
        if 'kum' in label or label == 'napomena':
            return 'Kumovi'
        return 'Krštenik'
    if form_type == 'prijava-vjencanje':
        if any(token in label for token in (
            'dogovoreni datum', 'vrijeme', 'podnositelj', 'e-mail za',
            'sakrament vjenčanja', 'župa u kojoj će se sklopiti',
        )):
            return 'Župa'
        if 'zaručnice' in label or 'zaručnica' in label:
            return 'Zaručnica'
        if 'zaručnika' in label or 'zaručnik' in label:
            return 'Zaručnik'
        if 'svjedok' in label or label == 'napomena':
            return 'Kumovi'
        return 'Župa'
    return None


def _group_display_fields(submission: dict) -> list[dict]:
    fields = list(submission.get('displayFields') or [])
    form_type = submission.get('formType') or submission.get('type')
    if not fields:
        return []
    spec = DISPLAY_SECTIONS.get(form_type)
    if not spec:
        return [{'title': 'Podaci prijave', 'fields': fields}]

    buckets: dict[str, list] = {title: [] for title, _names in spec}
    leftover = []
    for field in fields:
        field = dict(field)
        name = str(field.get('name') or '')
        field['wide'] = name in WIDE_FIELD_NAMES or _normalized_text(field.get('label')) in {
            'adresa', 'napomena', 'škola', 'podnositelj zahtjeva',
        }
        title = _section_title_for_field(form_type, field)
        if title in buckets:
            buckets[title].append(field)
        else:
            leftover.append(field)

    grouped = [
        {'title': title, 'fields': buckets[title]}
        for title, _names in spec
        if buckets[title]
    ]
    if leftover:
        grouped.append({'title': 'Ostalo', 'fields': leftover})
    return grouped


def _known_person_names(parish_data: dict) -> set[str]:
    known_names = {
        _normalized_text(value)
        for collection_name, field_name in (
            ('baptisms', 'childName'),
            ('weddings', 'couple'),
            ('funerals', 'deceased'),
            ('anointing', 'person'),
        )
        for record in parish_data.get(collection_name, [])
        for value in [record.get(field_name)]
        if value
    }
    for formation_collection_name in ('confirmation', 'firstCommunion'):
        for formation_group in parish_data.get(formation_collection_name, []):
            known_names.update(
                _normalized_text(
                    formation_candidate.get('name')
                    or ' '.join(filter(None, (
                        formation_candidate.get('firstName'),
                        formation_candidate.get('lastName'),
                    )))
                )
                for formation_candidate in formation_group.get('candidates', [])
                if formation_candidate.get('name')
                or formation_candidate.get('firstName')
                or formation_candidate.get('lastName')
            )
    known_names.discard('')
    return known_names


def _has_repeated_submission(
    selected_submission: dict,
    all_submissions: list[dict],
) -> bool:
    selected_name = _normalized_text(selected_submission.get('name'))
    selected_form_type = (
        selected_submission.get('formType')
        or selected_submission.get('type')
    )
    if not selected_name or not selected_form_type:
        return False
    selected_contacts = {
        _normalized_text(selected_submission.get('phone')),
        _normalized_text(selected_submission.get('email')),
        _normalized_text(selected_submission.get('address')),
    }
    selected_contacts.discard('')
    return any(
        other_submission.get('id') != selected_submission.get('id')
        and (
            other_submission.get('formType')
            or other_submission.get('type')
        ) == selected_form_type
        and _normalized_text(other_submission.get('name')) == selected_name
        and bool(selected_contacts & {
            _normalized_text(other_submission.get('phone')),
            _normalized_text(other_submission.get('email')),
            _normalized_text(other_submission.get('address')),
        })
        for other_submission in all_submissions
    )


def _submission_age_in_days(submitted_at, today: date) -> int | None:
    try:
        submitted_date = datetime.fromisoformat(
            str(submitted_at or '').replace('Z', '+00:00')
        ).date()
    except (TypeError, ValueError):
        return None
    return max(0, (today - submitted_date).days)


def _enrich_submissions(parish_data: dict) -> list[dict]:
    today = date.today()
    all_submissions = list(parish_data.get('publicSubmissions', []))
    parish_street_names = [
        _normalized_text(street.get('name'))
        for street in parish_data.get('streets', [])
        if street.get('name')
    ]
    known_person_names = _known_person_names(parish_data)
    enriched_submissions = []

    for original_submission in all_submissions:
        submission = dict(original_submission)
        submission['ageDays'] = _submission_age_in_days(
            submission.get('submittedAt'),
            today,
        )
        submission['hasContact'] = bool(
            submission.get('phone') or submission.get('email')
        )
        submitted_address = _normalized_text(
            submission.get('address')
            or (submission.get('data') or {}).get('adresa')
        )
        submission['jurisdictionKnown'] = bool(
            submitted_address
            and any(
                street_name in submitted_address
                for street_name in parish_street_names
            )
        )
        submission['matchesExistingRecord'] = (
            _normalized_text(submission.get('name')) in known_person_names
        )
        submission['repeatedSubmission'] = _has_repeated_submission(
            submission,
            all_submissions,
        )
        submission['possibleDuplicate'] = bool(
            submission['matchesExistingRecord']
            or submission['repeatedSubmission']
        )

        review_reasons = []
        if not submission.get('consentGranted'):
            review_reasons.append('nedostaje privola')
        if not submission['hasContact']:
            review_reasons.append('nedostaje kontakt')
        if not submission['jurisdictionKnown']:
            review_reasons.append('adresa nije prepoznata u župi')
        if submission['repeatedSubmission']:
            review_reasons.append('moguća ponovljena prijava')
        elif submission['matchesExistingRecord']:
            review_reasons.append('moguć postojeći zapis')
        submission['reviewReasons'] = review_reasons
        submission['triageReady'] = not review_reasons
        submission['displaySections'] = _group_display_fields(submission)
        enriched_submissions.append(submission)

    return enriched_submissions


def public_submissions_context(parish_data: dict, request) -> dict:
    status_filter = request.GET.get('status') or 'nova'
    form_type_filter = request.GET.get('type') or ''
    search_term = _normalized_text(request.GET.get('q'))
    all_submissions = _enrich_submissions(parish_data)

    visible_submissions = list(all_submissions)
    if status_filter == 'obradeno':
        visible_submissions = [
            submission
            for submission in visible_submissions
            if submission.get('status') != 'nova'
        ]
    elif status_filter != 'all':
        visible_submissions = [
            submission
            for submission in visible_submissions
            if submission.get('status') == status_filter
        ]

    if form_type_filter:
        visible_submissions = [
            submission
            for submission in visible_submissions
            if (
                submission.get('formType')
                or submission.get('type')
            ) == form_type_filter
        ]
    if search_term:
        visible_submissions = [
            submission
            for submission in visible_submissions
            if any(
                search_term in _normalized_text(submission.get(field_name))
                for field_name in ('name', 'phone', 'email', 'address')
            )
            or any(
                search_term in _normalized_text(display_field.get('value'))
                for display_field in submission.get('displayFields', [])
            )
        ]

    visible_submissions = sorted(
        visible_submissions,
        key=lambda submission: submission.get('submittedAt') or '',
        reverse=True,
    )
    visible_submissions.sort(
        key=lambda submission: submission.get('status') != 'nova'
    )
    selected_submission_id = request.GET.get('submission', '')
    selected_submission = next(
        (
            submission
            for submission in all_submissions
            if submission.get('id') == selected_submission_id
        ),
        None,
    )

    new_submissions = [
        submission
        for submission in all_submissions
        if submission.get('status') == 'nova'
    ]
    return {
        'submission_rows': visible_submissions,
        'selected_submission': selected_submission,
        'submission_filters': {
            'status': status_filter,
            'type': form_type_filter,
            'q': request.GET.get('q', ''),
        },
        'submission_stats': {
            'new': len(new_submissions),
            'review': sum(
                1
                for submission in new_submissions
                if not submission.get('triageReady')
            ),
            'processed': sum(
                1
                for submission in all_submissions
                if submission.get('status') != 'nova'
            ),
        },
        'submission_nova_count': len(new_submissions),
        'form_labels': FORM_LABELS,
        'submission_form_types': sorted({
            submission.get('formType') or submission.get('type')
            for submission in all_submissions
            if submission.get('formType') or submission.get('type')
        }),
        'import_year': int(request.GET.get('year') or date.today().year),
    }
