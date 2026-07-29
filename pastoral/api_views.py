import json
import re

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from pastoral.forms import LoginForm
from pastoral.services.otp import (
    create_otp_challenge,
    dispatch_otp_email,
    store_otp_session,
)

from pastoral.services.api_actions import dispatch_action
from pastoral.services.data import ParishDataService
from pastoral.services.liturgical import LiturgicalService

ISO_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


@require_http_methods(['POST'])
def send_otp_api(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid_json'}, status=400)

    form = LoginForm({
        'email': (payload.get('email') or '').strip(),
        'role': payload.get('role') or '',
        'gdpr_consent': payload.get('gdpr_consent') in (True, 'true', '1', 1, 'on'),
    })
    if not form.is_valid():
        return JsonResponse({
            'ok': False,
            'error': 'invalid_input',
            'details': form.errors,
        }, status=400)

    email = form.cleaned_data['email'].lower()
    role = form.cleaned_data['role']
    code = create_otp_challenge(email, role)

    mail_ok, mail_result = dispatch_otp_email(code, email, role)
    if not mail_ok:
        return JsonResponse({
            'ok': False,
            'error': mail_result.get('error', 'mail_failed'),
            'detail': mail_result.get('detail', ''),
            'recipient': mail_result.get('recipient', getattr(settings, 'OTP_RECIPIENT', '')),
        }, status=502)

    store_otp_session(request, email=email, role=role)

    recipient = mail_result.get('recipient', getattr(settings, 'OTP_RECIPIENT', ''))
    return JsonResponse({
        'ok': True,
        'recipient': recipient,
        'ttl_minutes': getattr(settings, 'OTP_TTL_MINUTES', 10),
    })


@login_required
@require_http_methods(['GET'])
def parish_data_api(request):
    svc = ParishDataService()
    return JsonResponse(svc.load())


@login_required
@require_http_methods(['GET'])
def liturgical_year_api(request, year: int):
    days = LiturgicalService().get_year_days(year, with_hilp=False)
    return JsonResponse({
        'year': year,
        'days': days,
        'translated': True,
        'source': 'litcal-va+hr-glossary',
    })


@login_required
@require_http_methods(['GET'])
def liturgical_day_api(request, iso: str):
    if not ISO_RE.match(iso):
        return JsonResponse({'error': 'invalid_date'}, status=400)
    day = LiturgicalService().get_day(iso)
    return JsonResponse(day)


@login_required
@require_http_methods(['POST'])
def parish_action_api(request):
    try:
        body = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid_json'}, status=400)
    action = body.get('action')
    if not action:
        return JsonResponse({'ok': False, 'error': 'missing_action'}, status=400)
    payload = body.get('payload') or {}
    svc = ParishDataService()
    if action == 'reset_demo':
        svc.reset_demo()
        return JsonResponse({'ok': True, 'data': svc.load()})
    result = dispatch_action(action, payload, svc)
    status = 200 if result.get('ok') else 400
    return JsonResponse(result, status=status)


@login_required
@require_http_methods(['GET'])
def search_api(request):
    from pastoral.services.global_search import global_search
    q = request.GET.get('q', '')
    results = global_search(ParishDataService().load(), q)
    return JsonResponse({'ok': True, 'results': results})


@login_required
@require_http_methods(['GET'])
def liturgical_month_api(request, year: int, month: int):
    if month < 1 or month > 12:
        return JsonResponse({'error': 'invalid_month'}, status=400)
    days = LiturgicalService().get_month_days(year, month)
    return JsonResponse({
        'year': year,
        'month': month,
        'days': days,
        'translated': True,
        'source': 'litcal-va+hr-glossary',
    })
