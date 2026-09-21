"""HTTP API za liturgijski kalendar iz baze."""
import re

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from liturgija.services.liturgical import LiturgicalService

ISO_DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')


@login_required
@require_http_methods(['GET'])
def liturgical_year_api(request, year: int):
    return JsonResponse({
        'year': year,
        'days': LiturgicalService().get_year_days(year, with_hilp=False),
        'source': 'database',
    })


@login_required
@require_http_methods(['GET'])
def liturgical_day_api(request, iso: str):
    if not ISO_DATE_PATTERN.match(iso):
        return JsonResponse({'error': 'invalid_date'}, status=400)
    return JsonResponse(LiturgicalService().get_day(iso))


@login_required
@require_http_methods(['GET'])
def liturgical_month_api(request, year: int, month: int):
    if month < 1 or month > 12:
        return JsonResponse({'error': 'invalid_month'}, status=400)
    return JsonResponse({
        'year': year,
        'month': month,
        'days': LiturgicalService().get_month_days(year, month),
        'source': 'database',
    })
