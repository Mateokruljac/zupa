"""HTTP API za liturgijski kalendar."""
import re

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from liturgija.services.liturgical import LiturgicalService
from liturgija.services.liturgical_romcal import (
    RomcalLiturgicalService,
    compare_liturgical_days,
)

ISO_DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')

@login_required
@require_http_methods(['GET'])
def liturgical_raw_year_api(request, year: int):
    """Sirovi LitCal bundle (zamjena za static/data/litcal/<year>.json)."""
    from liturgija.litcal_fixture_data import litcal_bundle_for_year

    bundle = litcal_bundle_for_year(year)
    if not bundle:
        return JsonResponse({'error': 'year_unavailable'}, status=404)
    return JsonResponse(bundle)


@login_required
@require_http_methods(['GET'])
def liturgical_year_api(request, year: int):
    liturgical_days = LiturgicalService().get_year_days(
        year,
        with_hilp=False,
    )
    return JsonResponse({
        'year': year,
        'days': liturgical_days,
        'translated': True,
        'source': next(iter(liturgical_days.values()), {}).get(
            'source',
            'unknown',
        ),
    })


@login_required
@require_http_methods(['GET'])
def liturgical_day_api(request, iso: str):
    if not ISO_DATE_PATTERN.match(iso):
        return JsonResponse({'error': 'invalid_date'}, status=400)
    liturgical_day = LiturgicalService().get_day(iso)
    return JsonResponse(liturgical_day)


@login_required
@require_http_methods(['GET'])
def liturgical_romcal_day_api(request, iso: str):
    """Izolirani lokalni Romcal rezultat za ručno testiranje."""
    if not ISO_DATE_PATTERN.match(iso):
        return JsonResponse({'error': 'invalid_date'}, status=400)
    return JsonResponse(RomcalLiturgicalService().get_day(iso))


@login_required
@require_http_methods(['GET'])
def liturgical_compare_api(request, iso: str):
    """Usporedba postojećeg LitCala i Romcala bez promjene aktivnog izvora."""
    if not ISO_DATE_PATTERN.match(iso):
        return JsonResponse({'error': 'invalid_date'}, status=400)
    litcal_day = LiturgicalService().get_day_litcal(iso)
    romcal_day = RomcalLiturgicalService().get_day(iso)
    comparison = compare_liturgical_days(litcal_day, romcal_day)
    comparison['hybrid'] = LiturgicalService().get_day(iso, with_hilp=False)
    return JsonResponse(comparison)


@login_required
@require_http_methods(['GET'])
def liturgical_v1_day_api(request, iso: str):
    """Stabilni projektni format inspiriran liturgy.day, bez vanjske ovisnosti."""
    if not ISO_DATE_PATTERN.match(iso):
        return JsonResponse({'error': 'invalid_date'}, status=400)
    liturgical_day = LiturgicalService().get_day(iso)
    return JsonResponse({
        'schemaVersion': '1.0',
        'locale': 'hr-HR',
        'timezone': 'Europe/Zagreb',
        'provider': liturgical_day.get('source'),
        'date': iso,
        'data': liturgical_day,
    })


@login_required
@require_http_methods(['GET'])
def liturgical_v1_info_api(request):
    return JsonResponse({
        'schemaVersion': '1.0',
        'locale': 'hr-HR',
        'timezone': 'Europe/Zagreb',
        'primaryProvider': getattr(settings, 'LITURGICAL_PRIMARY_PROVIDER', 'hybrid'),
        'providers': {
            'romcal': 'Hrvatski kalendar, slavlja, rang i boja',
            'litcal-va': 'Liturgijski vremenski dan i strukturirani podaci',
            'hilp': 'Hrvatska misna čitanja i poveznica na puni tekst',
        },
        'dayEndpoint': '/api/liturgical/v1/day/YYYY-MM-DD/',
    })


@login_required
@require_http_methods(['GET'])
def liturgical_month_api(request, year: int, month: int):
    if month < 1 or month > 12:
        return JsonResponse({'error': 'invalid_month'}, status=400)
    liturgical_days = LiturgicalService().get_month_days(year, month)
    return JsonResponse({
        'year': year,
        'month': month,
        'days': liturgical_days,
        'translated': True,
        'source': next(iter(liturgical_days.values()), {}).get(
            'source',
            'unknown',
        ),
    })

