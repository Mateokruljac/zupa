import re

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from pastoral.services.data import ParishDataService
from pastoral.services.admin_interface_theme import (
    synchronize_admin_interface_theme,
)
from pastoral.services.permissions import (
    filter_nav,
    group_nav_sections,
    nav_badges_from_stats,
)
from control_plane.models import ParishMembership


THEME_COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')


def _valid_theme_color(color_value, fallback_color):
    normalized_color = str(color_value or '').strip()
    if THEME_COLOR_PATTERN.fullmatch(normalized_color):
        return normalized_color
    return fallback_color


def _technical_admin_theme(request):
    from pastoral.models import Parish

    selected_parish = None
    if request.user.is_authenticated:
        current_date_time = timezone.now()
        active_memberships = list(
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
            )[:2]
        )
        if len(active_memberships) == 1:
            selected_parish = active_memberships[0].parish

    if selected_parish is None:
        selected_parish = (
            Parish.objects
            .filter(slug=settings.PARISH_DEFAULT_SLUG)
            .first()
        )

    parish_settings = selected_parish.settings if selected_parish else {}
    legacy_theme = parish_settings.get('theme') or {}
    technical_admin_theme = {
        'primary_color': _valid_theme_color(
            parish_settings.get('primaryColor') or legacy_theme.get('primary'),
            '#5c2e3a',
        ),
        'accent_color': _valid_theme_color(
            parish_settings.get('accentColor') or legacy_theme.get('accent'),
            '#b8922a',
        ),
    }
    synchronize_admin_interface_theme(
        technical_admin_theme['primary_color'],
        technical_admin_theme['accent_color'],
    )
    return technical_admin_theme


def pastoral_globals(request):
    is_technical_admin = (
        request.resolver_match
        and request.resolver_match.namespace == 'admin'
    )
    if is_technical_admin:
        return {'technical_admin_theme': _technical_admin_theme(request)}
    if not request.user.is_authenticated:
        return {}
    parish_data_service = ParishDataService()
    current_page = getattr(request.resolver_match, 'kwargs', {}).get(
        'page',
        'dashboard',
    )
    if request.resolver_match and request.resolver_match.url_name == 'app':
        current_page = 'dashboard'
    parish_settings = parish_data_service.load_settings()
    parish_data = parish_data_service.load()
    office_statistics = parish_data_service.office_statistics(parish_data)
    tenant_context = getattr(request, 'tenant_context', None)
    active_role = tenant_context.role if tenant_context else request.user.role
    navigation_items = filter_nav(active_role, current_page)
    return {
        'parish_settings': parish_settings,
        'nav_items': navigation_items,
        'nav_sections': group_nav_sections(navigation_items),
        'nav_badges': nav_badges_from_stats(office_statistics),
        'current_page': current_page,
        'active_role_label': dict(ParishMembership.Role.choices).get(
            active_role,
            request.user.role_label,
        ),
    }
