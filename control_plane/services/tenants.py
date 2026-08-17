from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils import timezone

from control_plane.models import ParishMembership
from control_plane.tenant_context import TenantContext


def resolve_request_tenant(request):
    if not request.user.is_authenticated:
        return None

    now = timezone.now()
    memberships = (
        ParishMembership.objects
        .select_related('parish')
        .filter(
            user=request.user,
            status=ParishMembership.Status.ACTIVE,
            valid_from__lte=now,
        )
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=now))
    )

    requested_tenant_id = request.session.get('active_tenant_id')
    membership = None
    if requested_tenant_id:
        membership = memberships.filter(parish__tenant_id=requested_tenant_id).first()
        if membership is None:
            request.session.pop('active_tenant_id', None)

    if membership is None:
        candidates = list(memberships[:2])
        if len(candidates) == 1:
            membership = candidates[0]
            request.session['active_tenant_id'] = str(membership.parish.tenant_id)

    if membership is not None:
        tenant_database = getattr(membership.parish, 'tenant_database', None)
        return TenantContext(
            tenant_id=membership.parish.tenant_id,
            parish_pk=membership.parish_id,
            database_alias=tenant_database.alias if tenant_database else None,
            membership_id=membership.id,
            actor_id=request.user.id,
            role=membership.role,
        )

    if getattr(settings, 'TENANCY_LEGACY_FALLBACK_ENABLED', False):
        from pastoral.services.data import ParishDataService
        parish = ParishDataService.get_or_create_parish()
        if parish:
            return TenantContext(
                tenant_id=parish.tenant_id,
                parish_pk=parish.pk,
                database_alias=None,
                membership_id=None,
                actor_id=request.user.id,
                role=request.user.role,
                used_legacy_fallback=True,
            )

    raise PermissionDenied('Nemate aktivno članstvo ni odabranu župu.')
