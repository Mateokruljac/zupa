import json
import re

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from pastoral.forms import LoginForm
from users.models import User
from pastoral.services.otp import (
    create_otp_challenge,
    dispatch_otp_email,
    store_otp_session,
)

from pastoral.services.api_actions import dispatch_action
from pastoral.services.data import ParishDataService
from pastoral.services.liturgical import LiturgicalService
from pastoral.services.liturgical_romcal import (
    RomcalLiturgicalService,
    compare_liturgical_days,
)

ISO_DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')


@require_http_methods(['POST'])
def send_otp_api(request):
    try:
        request_payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid_json'}, status=400)

    login_form = LoginForm({
        'email': (request_payload.get('email') or '').strip(),
        'gdpr_consent': request_payload.get('gdpr_consent') in (
            True,
            'true',
            '1',
            1,
            'on',
        ),
    })
    if not login_form.is_valid():
        return JsonResponse({
            'ok': False,
            'error': 'invalid_input',
            'details': login_form.errors,
        }, status=400)

    email_address = login_form.cleaned_data['email'].lower()
    user_role = (
        User.objects.filter(email__iexact=email_address)
        .values_list('role', flat=True)
        .first()
        or User._meta.get_field('role').default
    )
    verification_code = create_otp_challenge(email_address, user_role)

    email_was_sent, email_result = dispatch_otp_email(
        verification_code,
        email_address,
        user_role,
    )
    if not email_was_sent:
        return JsonResponse({
            'ok': False,
            'error': email_result.get('error', 'mail_failed'),
            'detail': email_result.get('detail', ''),
            'recipient': email_result.get(
                'recipient',
                getattr(settings, 'OTP_RECIPIENT', ''),
            ),
        }, status=502)

    store_otp_session(
        request,
        email=email_address,
        role=user_role,
    )

    recipient = email_result.get(
        'recipient',
        getattr(settings, 'OTP_RECIPIENT', ''),
    )
    return JsonResponse({
        'ok': True,
        'recipient': recipient,
        'ttl_minutes': getattr(settings, 'OTP_TTL_MINUTES', 10),
    })


@login_required
@require_http_methods(['GET'])
def parish_data_api(request):
    parish_data_service = ParishDataService()
    return JsonResponse(parish_data_service.load())


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
@require_http_methods(['POST'])
def parish_action_api(request):
    try:
        request_body = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid_json'}, status=400)
    action_name = request_body.get('action')
    if not action_name:
        return JsonResponse({'ok': False, 'error': 'missing_action'}, status=400)
    action_payload = request_body.get('payload') or {}
    parish_data_service = ParishDataService()
    if action_name == 'reset_demo':
        parish_data_service.reset_demo()
        return JsonResponse({
            'ok': True,
            'data': parish_data_service.load(),
        })
    action_result = dispatch_action(
        action_name,
        action_payload,
        parish_data_service,
    )
    response_status = 200 if action_result.get('ok') else 400
    return JsonResponse(action_result, status=response_status)


@login_required
@require_http_methods(['GET'])
def search_api(request):
    from pastoral.services.global_search import global_search
    search_query = request.GET.get('q', '')
    search_results = global_search(
        ParishDataService().load(),
        search_query,
    )
    return JsonResponse({'ok': True, 'results': search_results})


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
