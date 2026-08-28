"""Samostalne stranice za neočekivane HTTP pogreške."""
from django.http import HttpResponse
from django.template.loader import get_template
from django.urls import reverse


def _safe_home_url(request) -> str:
    return reverse('pastoral:app') if getattr(request.user, 'is_authenticated', False) else reverse('pastoral:login')


def _render_error_page(*, status_code: int, context: dict) -> HttpResponse:
    """Renderira pogrešku bez pokretanja projektnih kontekstnih procesora."""
    rendered_page = get_template('errors/error_page.html').render(context)
    return HttpResponse(rendered_page, status=status_code)


def page_not_found(request, exception):
    return _render_error_page(
        status_code=404,
        context={
            'error_code': '404',
            'page_title': 'Stranica nije pronađena',
            'error_message': (
                'Poveznica možda više nije važeća ili je adresa '
                'pogrešno unesena.'
            ),
            'home_url': _safe_home_url(request),
            'show_reload_action': False,
        },
    )


def server_error(request):
    return _render_error_page(
        status_code=500,
        context={
            'error_code': '500',
            'page_title': 'Nešto nije prošlo kako treba',
            'error_message': (
                'Podaci nisu izgubljeni. Pokušajte ponovno, a ako se '
                'problem ponovi, obratite se podršci.'
            ),
            'home_url': _safe_home_url(request),
            'show_reload_action': True,
        },
    )
