from django.conf import settings
from django.core.checks import Error, register


@register()
def production_tenancy_checks(app_configs, **kwargs):
    errors = []
    if not getattr(settings, 'IS_PRODUCTION', False):
        return errors
    if getattr(settings, 'TENANCY_LEGACY_FALLBACK_ENABLED', False):
        errors.append(Error(
            'Legacy default-tenant fallback ne smije biti uključen u produkciji.',
            id='control_plane.E001',
        ))
    return errors

