"""Pregled, provjera i uvoz javnih prijava u župnu evidenciju."""
from __future__ import annotations

from datetime import date, datetime


FORM_LABELS = {
    'prijava-krizma': 'Krizma',
    'prijava-krsenje': 'Krštenje',
    'prijava-pricest': 'Prva pričest',
    'prijava-ukop': 'Ukop / pogreb',
}


def _normalized_text(value) -> str:
    return str(value or '').strip().casefold()


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
