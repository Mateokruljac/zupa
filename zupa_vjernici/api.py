"""Ninja API kartice obitelji — session + CSRF, samo otvorena obitelj."""
import logging
from datetime import date

from django.conf import settings
from ninja import NinjaAPI, Router
from ninja.errors import AuthorizationError, HttpError, ValidationError
from ninja.security import SessionAuth

from pastoral.services.permissions import can_access_page
from zupa_vjernici.schemas import (
    FamilyBasicsWrite,
    FamilyCardErrorOut,
    FamilyCardMutationOut,
    FamilyCardOut,
    FamilyContributionWrite,
    FamilyMemberWrite,
    FamilyNotesWrite,
)
from zupa_vjernici.services.family_card import (
    FamilyCardRejected,
    save_family_basics,
    save_family_contribution_card,
    save_family_member_card,
    save_family_notes_card,
)

logger = logging.getLogger(__name__)

CARD_RESPONSES = {
    200: FamilyCardMutationOut,
    400: FamilyCardErrorOut,
    404: FamilyCardErrorOut,
    422: FamilyCardErrorOut,
}


class FamilyCardSessionAuth(SessionAuth):
    """Prijava + CSRF i pristup stranici Obitelji."""

    def authenticate(self, request, key):
        if not request.user.is_authenticated:
            return None
        if not can_access_page('obitelji', getattr(request.user, 'role', '')):
            raise AuthorizationError()
        return request.user


families_api = NinjaAPI(
    title='Kartica obitelji',
    version='1.0.0',
    urls_namespace='zupa_families',
    auth=FamilyCardSessionAuth(),
    docs_url='/docs' if settings.DEBUG else None,
)
families_router = Router(tags=['obitelji'])


@families_api.exception_handler(ValidationError)
def invalid_family_card_payload(request, exc):
    logger.warning('kartica obitelji: nevaljan unos')
    return families_api.create_response(
        request,
        {'ok': False, 'error': 'invalid', 'fields': {}},
        status=422,
    )


@families_api.exception_handler(HttpError)
def family_card_http_error(request, exc):
    logger.warning('kartica obitelji: %s', exc)
    return families_api.create_response(
        request,
        {'ok': False, 'error': str(exc), 'fields': {}},
        status=exc.status_code,
    )


def _iso(value: date | None) -> str:
    return value.isoformat() if value else ''


def _number(value) -> str:
    return '' if value is None else str(value)


def _saved(card: dict, message: str):
    return 200, FamilyCardMutationOut(message=message, card=FamilyCardOut(**card))


def _rejected(error: FamilyCardRejected):
    logger.info('kartica obitelji: %s', error.code)
    return error.status_code, FamilyCardErrorOut(error=error.code, fields=error.fields)


@families_router.patch('/{family_id}/', response=CARD_RESPONSES)
def update_family_basics(request, family_id: str, payload: FamilyBasicsWrite):
    try:
        card = save_family_basics(request, family_id, {
            'surname': payload.surname,
            'street_id': payload.street_id,
            'address': payload.address,
            'phone': payload.phone,
            'email': payload.email,
            'status': payload.status,
        })
    except FamilyCardRejected as error:
        return _rejected(error)
    return _saved(card, 'Podaci obitelji su spremljeni.')


@families_router.put('/{family_id}/members/', response=CARD_RESPONSES)
def save_member(request, family_id: str, payload: FamilyMemberWrite):
    try:
        card = save_family_member_card(request, family_id, {
            'given_name': payload.given_name,
            'surname': payload.surname,
            'relation': payload.relation,
            'birth_date': _iso(payload.birth_date),
            'member_id': payload.member_id,
        })
    except FamilyCardRejected as error:
        return _rejected(error)
    message = (
        'Član obitelji je spremljen.'
        if payload.member_id
        else 'Član obitelji je dodan.'
    )
    return _saved(card, message)


@families_router.put('/{family_id}/contributions/', response=CARD_RESPONSES)
def save_contribution(request, family_id: str, payload: FamilyContributionWrite):
    form_data = {
        'year': _number(payload.year),
        'lukno_amount': _number(payload.lukno_amount),
        'lukno_paid_at': _iso(payload.lukno_paid_at),
        'church_donation': _number(payload.church_donation),
        'donation_date': _iso(payload.donation_date),
        'notes': payload.notes,
    }
    if payload.lukno_paid:
        form_data['lukno_paid'] = 'on'
    try:
        card = save_family_contribution_card(request, family_id, form_data)
    except FamilyCardRejected as error:
        return _rejected(error)
    return _saved(card, 'Lukno i darovi su spremljeni.')


@families_router.patch('/{family_id}/notes/', response=CARD_RESPONSES)
def save_notes(request, family_id: str, payload: FamilyNotesWrite):
    try:
        card = save_family_notes_card(request, family_id, {
            'pastoral_notes': payload.pastoral_notes,
        })
    except FamilyCardRejected as error:
        return _rejected(error)
    return _saved(card, 'Bilješka je spremljena.')


families_api.add_router('', families_router)
