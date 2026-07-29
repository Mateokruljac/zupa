from pastoral.services.data import ParishDataService
from pastoral.services.permissions import filter_nav, group_nav_sections, nav_badges_from_stats


def pastoral_globals(request):
    if not request.user.is_authenticated:
        return {}
    svc = ParishDataService()
    page = getattr(request.resolver_match, 'kwargs', {}).get('page', 'dashboard')
    if request.resolver_match and request.resolver_match.url_name == 'app':
        page = 'dashboard'
    settings_data = svc.load_settings()
    data = svc.load()
    stats = svc.office_stats(data)
    nav_items = filter_nav(request.user.role, page)
    return {
        'parish_settings': settings_data,
        'nav_items': nav_items,
        'nav_sections': group_nav_sections(nav_items),
        'nav_badges': nav_badges_from_stats(stats),
        'office_stats': stats,
        'current_page': page,
    }
