"""Globalna pretraga župnog ureda (Ctrl+K, formulari)."""
from __future__ import annotations

from pastoral.services.matica import search_all
from pastoral.services.operations import build_work_queue


def global_search(
    parish_data: dict,
    search_query: str,
    result_limit: int = 20,
) -> list[dict]:
    normalized_query = (search_query or '').strip().lower()
    if len(normalized_query) < 2:
        return []

    search_results: list[dict] = []

    for household in parish_data.get('families', []):
        household_member_names = ' '.join(
            household_member.get('name', '')
            for household_member in household.get('members') or []
        )
        searchable_text = (
            f"{household.get('surname', '')} {household.get('address', '')} "
            f"{household.get('phone', '')} {household_member_names}"
        ).lower()
        if normalized_query not in searchable_text:
            continue
        search_results.append({
            'type': 'Obitelj',
            'label': household.get('surname', ''),
            'sub': (
                f"{household.get('address', '')} · {household_member_names}"
            ).strip(' ·'),
            'href': f"obitelji?family={household.get('id', '')}",
        })

    for intention in parish_data.get('intentions', []):
        searchable_text = (
            f"{intention.get('intentionFor', '')} "
            f"{intention.get('requestedBy', '')} {intention.get('date', '')}"
        ).lower()
        if normalized_query not in searchable_text:
            continue
        search_results.append({
            'type': 'Nakana',
            'label': intention.get('intentionFor', ''),
            'sub': (
                f"{intention.get('date', '')} {intention.get('massTime', '')} · "
                f"{intention.get('requestedBy', '')}"
            ),
            'href': f"nakane?date={intention.get('date', '')}",
        })

    for task in parish_data.get('tasks', []):
        searchable_text = (
            f"{task.get('title', '')} {task.get('category', '')}"
        ).lower()
        if normalized_query not in searchable_text:
            continue
        search_results.append({
            'type': 'Zadatak',
            'label': task.get('title', ''),
            'sub': f"{task.get('due', 'bez roka')} · {task.get('category', '')}",
            'href': 'kalendar',
        })

    for baptism_record in parish_data.get('baptisms', []):
        searchable_text = (
            f"{baptism_record.get('childName', '')} "
            f"{baptism_record.get('parents', '')}"
        ).lower()
        if normalized_query not in searchable_text:
            continue
        search_results.append({
            'type': 'Krštenje',
            'label': baptism_record.get('childName', ''),
            'sub': baptism_record.get('baptismDate', ''),
            'href': 'krsenja',
        })

    for public_submission in parish_data.get('publicSubmissions', []):
        if public_submission.get('status') != 'nova':
            continue
        submission_name = public_submission.get('name') or 'Prijava'
        submission_type = str(public_submission.get('formType', ''))
        if (
            normalized_query not in submission_name.lower()
            and normalized_query not in submission_type.lower()
        ):
            continue
        search_results.append({
            'type': 'Prijava',
            'label': submission_name,
            'sub': public_submission.get('formType', ''),
            'href': 'javne-prijave',
        })

    parish_names_by_identifier = {
        parish.get('id'): parish.get('name', '')
        for parish in parish_data.get('parishDirectory', [])
    }
    for interparish_request in parish_data.get('interparishRequests', []):
        searchable_text = ' '.join((
            interparish_request.get('reference', ''),
            interparish_request.get('caseReference', ''),
            interparish_request.get('subject', ''),
            interparish_request.get('personName', ''),
            parish_names_by_identifier.get(
                interparish_request.get('sourceParishId'),
                '',
            ),
            parish_names_by_identifier.get(
                interparish_request.get('targetParishId'),
                '',
            ),
        )).lower()
        if normalized_query not in searchable_text:
            continue
        search_results.append({
            'type': 'Dekanat',
            'label': (
                interparish_request.get('subject')
                or interparish_request.get('reference', '')
            ),
            'sub': (
                f"{interparish_request.get('reference', '')} · "
                f"{interparish_request.get('personName', '')}"
            ).strip(' ·'),
            'href': (
                'dekanat?view=all&request='
                f"{interparish_request.get('id', '')}"
            ),
        })

    for work_queue_item in build_work_queue(parish_data):
        searchable_text = ' '.join(
            str(work_queue_item.get(field_name, ''))
            for field_name in (
                'title',
                'meta',
                'owner',
                'contact',
                'reference',
                'nextAction',
                'linkedCase',
            )
        ).lower()
        if normalized_query not in searchable_text:
            continue
        search_results.append({
            'type': work_queue_item['categoryMeta']['label'],
            'label': work_queue_item.get('title', ''),
            'sub': (
                f"{work_queue_item.get('meta', '')} · "
                f"{work_queue_item['statusMeta']['label']}"
            ).strip(' ·'),
            'href': (
                'operativno-srediste?view=all&item='
                f"{work_queue_item.get('itemId', '')}"
            ),
        })

    if len(search_results) < result_limit:
        remaining_result_count = result_limit - len(search_results)
        for registry_record in search_all(
            parish_data,
            search_query,
            remaining_result_count,
        ):
            search_results.append({
                'type': registry_record.get('type', 'Matica'),
                'label': registry_record.get('label', ''),
                'sub': 'Matična evidencija',
                'href': (
                    'potvrde?tpl=potvrda_krsenja'
                    f"&record_type={registry_record.get('type')}"
                    f"&record_id={registry_record.get('id')}"
                ),
            })

    return search_results[:result_limit]
