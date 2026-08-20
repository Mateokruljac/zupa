from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils import timezone

from control_plane.models import ParishMembership
from control_plane.tenant_context import TenantContext


def resolve_request_tenant(request):
    if not request.user.is_authenticated:
        return None

    current_date_time = timezone.now()
    memberships = (
        ParishMembership.objects
        .select_related('parish')
        .filter(
            user=request.user,
            status=ParishMembership.Status.ACTIVE,
            valid_from__lte=current_date_time,
        )
        .filter(
            Q(valid_until__isnull=True)
            | Q(valid_until__gte=current_date_time)
        )
    )

    membership_candidates = list(memberships[:2])
    membership = (
        membership_candidates[0]
        if len(membership_candidates) == 1
        else None
    )

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

    raise PermissionDenied('Morate imati točno jedno aktivno članstvo u župi.')
