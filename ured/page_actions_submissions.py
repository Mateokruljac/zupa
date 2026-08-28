"""POST akcije za javne prijave."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from django.contrib import messages
from django.db import transaction

from pastoral.services.api_action_handlers.shared import normalize_parish_data
from ured.api_actions import import_public_submission
from sakramenti.services.baptism_records import synchronize_baptism_record

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


def handle_public_submissions_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
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
        if public_submission.get('status') != 'nova':
            messages.error(
                request,
                'Samo novu prijavu moguće je uvesti u evidenciju.',
            )
            return True
        if not public_submission.get('consentGranted'):
            messages.error(
                request,
                'Prijavu nije moguće uvesti jer privola nije evidentirana.',
            )
            return True
        try:
            selected_year = int(
                request.POST.get('year') or date.today().year
            )
        except (TypeError, ValueError):
            messages.error(request, 'Godina upisa nije ispravna.')
            return True
        normalize_parish_data(parish_data)
        operation_result = import_public_submission(
            parish_data,
            {'submission': public_submission, 'year': selected_year},
        )
        if operation_result.get('ok'):
            with transaction.atomic():
                parish_data_service.save(parish_data)
                if public_submission.get('type') in {
                    'krstenje', 'prijava-krsenje',
                } or public_submission.get('formType') in {
                    'krstenje', 'prijava-krsenje',
                }:
                    newest_baptism = parish_data.get('baptisms', [])[-1]
                    synchronize_baptism_record(
                        parish_data_service.parish,
                        newest_baptism,
                        actor=request.user,
                    )
            messages.success(request, 'Prijava uvezena u evidenciju.')
        else:
            messages.error(request, 'Uvoz nije uspio.')
        return True

    if (
        action_name in {
            'mark_submission_imported',
            'archive_submission',
            'mark_submission_duplicate',
            'reopen_submission',
        }
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
            submission_statuses = {
                'mark_submission_imported': 'preuzeto',
                'archive_submission': 'arhivirano',
                'mark_submission_duplicate': 'duplikat',
                'reopen_submission': 'nova',
            }
            public_submission['status'] = submission_statuses[action_name]
            parish_data_service.save(parish_data)
            status_messages = {
                'mark_submission_imported': 'Prijava je označena kao preuzeta.',
                'archive_submission': 'Prijava je arhivirana bez uvoza.',
                'mark_submission_duplicate': 'Prijava je označena kao duplikat.',
                'reopen_submission': 'Prijava je vraćena među nove.',
            }
            messages.success(request, status_messages[action_name])
        return True

    return False
