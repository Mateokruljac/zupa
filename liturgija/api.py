"""Ninja API misnih nakana — session + CSRF, tenant schema preko ORM managera."""
import logging
from uuid import UUID

from django.conf import settings
from ninja import NinjaAPI, Router
from ninja.errors import AuthorizationError, HttpError, ValidationError
from ninja.security import SessionAuth

from liturgija.models import MassIntention
from liturgija.schemas import (
    ErrorOut,
    IntentionMutationOut,
    MassIntentionOut,
    MassIntentionWriteSchema,
    OkOut,
)
from liturgija.services.mass_intentions import (
    MassIntentionRejected,
    create_mass_intention,
    update_mass_intention,
)
from pastoral.services.permissions import can_access_page

logger = logging.getLogger(__name__)


class LiturgySessionAuth(SessionAuth):
    """Prijava + CSRF (SessionAuth) i pristup modulu Liturgija."""

    def authenticate(self, request, key):
        if not request.user.is_authenticated:
            return None
        if not can_access_page('nakane', getattr(request.user, 'role', '')):
            raise AuthorizationError()
        return request.user


intentions_api = NinjaAPI(
    title='Misne nakane',
    version='1.0.0',
    urls_namespace='liturgija_intentions',
    auth=LiturgySessionAuth(),
    docs_url='/docs' if settings.DEBUG else None,
)
intentions_router = Router(tags=['nakane'])


@intentions_api.exception_handler(ValidationError)
def invalid_intention_payload(request, exc):
    logger.warning('intentions: nevaljan unos: %s', exc.errors)
    return intentions_api.create_response(
        request,
        {'ok': False, 'error': 'invalid'},
        status=422,
    )


@intentions_api.exception_handler(HttpError)
def intention_http_error(request, exc):
    logger.warning('intentions: %s', exc)
    return intentions_api.create_response(
        request,
        {'ok': False, 'error': str(exc)},
        status=exc.status_code,
    )


def _write_or_raise(operation, payload: MassIntentionWriteSchema, **kwargs):
    try:
        return operation(
            **kwargs,
            intention_date=payload.date,
            mass_time=payload.mass_time,
            intention_for=payload.intention_for,
            stipend=payload.stipend,
            is_paid=payload.paid,
            notes=payload.notes,
        )
    except MassIntentionRejected as error:
        raise HttpError(error.status_code, error.code) from error


@intentions_router.post(
    '/',
    response={201: IntentionMutationOut, 400: ErrorOut},
)
def create_intention(request, payload: MassIntentionWriteSchema):
    intention = _write_or_raise(create_mass_intention, payload)
    return 201, IntentionMutationOut(item=MassIntentionOut.from_intention(intention))


@intentions_router.patch(
    '/{intention_id}/',
    response={200: IntentionMutationOut, 400: ErrorOut, 404: ErrorOut},
)
def update_intention(request, intention_id: UUID, payload: MassIntentionWriteSchema):
    intention = _write_or_raise(
        update_mass_intention,
        payload,
        intention_id=intention_id,
    )
    return 200, IntentionMutationOut(item=MassIntentionOut.from_intention(intention))


@intentions_router.delete('/{intention_id}/', response={200: OkOut, 404: ErrorOut})
def delete_intention(request, intention_id: UUID):
    intention = MassIntention.objects.filter(pk=intention_id).first()
    if intention is None:
        logger.warning('nakana: nije pronađena id=%s', intention_id)
        raise HttpError(404, 'not_found')
    intention.delete()
    return 200, OkOut()


intentions_api.add_router('', intentions_router)
