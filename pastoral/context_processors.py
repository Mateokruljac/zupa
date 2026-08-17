from pastoral.services.data import ParishDataService
from pastoral.services.permissions import filter_nav, group_nav_sections, nav_badges_from_stats
from pastoral.services.screen_intelligence import build_screen_cockpit
from control_plane.models import ParishMembership


def pastoral_globals(request):
    if not request.user.is_authenticated:
        return {}
    if request.resolver_match and request.resolver_match.namespace == 'admin':
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
        'office_stats': office_statistics,
        'current_page': current_page,
        'active_role_label': dict(ParishMembership.Role.choices).get(
            active_role,
            request.user.role_label,
        ),
        'screen_cockpit': build_screen_cockpit(
            parish_data,
            current_page,
            parish_settings,
        ),
    }
