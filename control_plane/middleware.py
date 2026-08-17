from control_plane.services.tenants import resolve_request_tenant
from control_plane.tenant_context import (
    reset_current_tenant_context,
    set_current_tenant_context,
)


class TenantContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URL resolution happens inside the middleware chain, so the technical
        # control plane is excluded by its fixed server-side path, not by a
        # client-supplied tenant value.
        if request.path_info.startswith(('/admin/', '/i18n/')):
            return self.get_response(request)

        context = resolve_request_tenant(request)
        request.tenant_context = context
        request.tenant = None
        token = set_current_tenant_context(context)
        try:
            if context is not None:
                from pastoral.models import Parish
                request.tenant = Parish.objects.get(pk=context.parish_pk)
            return self.get_response(request)
        finally:
            reset_current_tenant_context(token)
