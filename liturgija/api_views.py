"""HTTP API liturgijskog kalendara (login obavezan, tenant schema).

Rute su u `pastoral/urls.py` pod `/api/liturgical/`.
"""
import re

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from django_multitenant.schema import with_tenant_schema
from liturgija.services.liturgical import LiturgicalService

# Strogi ISO datum; inače bi "2024-13-40" otišao u ValueError dublje.
ISO_DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')


@login_required
@require_http_methods(['GET'])
@with_tenant_schema
def liturgical_year_api(request, year: int):
    """JSON: svi uvezeni dani godine. Bez HILP-a (previše poziva)."""
    return JsonResponse({
        'year': year,
        'days': LiturgicalService().get_year_days(year, with_hilp=False),
        'source': 'database',
    })


@login_required
@require_http_methods(['GET'])
@with_tenant_schema
def liturgical_day_api(request, iso: str):
    """JSON jednog dana, s HILP čitanjima ako mreža radi."""
    if not ISO_DATE_PATTERN.match(iso):
        return JsonResponse({'error': 'invalid_date'}, status=400)
    return JsonResponse(LiturgicalService().get_day(iso))


@login_required
@require_http_methods(['GET'])
@with_tenant_schema
def liturgical_month_api(request, year: int, month: int):
    """JSON dana u mjesecu (kalendar u uredu)."""
    if month < 1 or month > 12:
        return JsonResponse({'error': 'invalid_month'}, status=400)
    return JsonResponse({
        'year': year,
        'month': month,
        'days': LiturgicalService().get_month_days(year, month),
        'source': 'database',
    })
