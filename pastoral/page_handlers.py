"""Shell kontekst admin stranica — zajednički omotač + domain registry."""
from pastoral.page_context_registry import (
    get_page_context_builder,
    page_title_subtitle,
)
from pastoral.services.data import ParishDataService
from pregled.services.dashboard import build_dashboard_context


def dashboard_context(request, parish_data_service: ParishDataService) -> dict:
    return build_dashboard_context(parish_data_service)


def build_page_context(request, page_slug: str) -> dict:
    parish_data_service = ParishDataService.for_request(request)
    page_title, page_subtitle = page_title_subtitle(page_slug)
    page_context = {
        'page_slug': page_slug,
        'page_title': page_title,
        'page_subtitle': page_subtitle,
    }
    parish_data = parish_data_service.load()
    request._pastoral_parish_data = parish_data
    page_context['baptism_data_source'] = 'relational'

    context_builder = get_page_context_builder(page_slug)
    if context_builder is not None:
        page_context.update(
            context_builder(request, parish_data, parish_data_service)
        )
    return page_context
