import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from pastoral.forms import LoginForm
from pastoral.models import User
from pastoral.services.otp import send_login_code
from pastoral.services.api_actions import dispatch_action
from pastoral.services.data import ParishDataService


@require_http_methods(['POST'])
@ratelimit(key='ip', rate='3/m', method='POST', block=False)
def send_otp_api(request):
    if getattr(request, 'limited', False):
        return JsonResponse({
            'ok': False,
            'error': 'rate_limited',
            'detail': 'Previše pokušaja. Pričekajte minutu pa pokušajte ponovno.',
        }, status=429)

    try:
        request_payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid_json'}, status=400)
    if not isinstance(request_payload, dict):
        return JsonResponse({'ok': False, 'error': 'invalid_payload'}, status=400)

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
    email_was_sent, email_result = send_login_code(
        request,
        email=email_address,
        role=user_role,
    )
    if not email_was_sent:
        if email_result.get('error') == 'cooldown':
            return JsonResponse({
                'ok': False,
                'error': 'otp_resend_cooldown',
                'retry_after_seconds': email_result['retry_after_seconds'],
            }, status=429)
        return JsonResponse({
            'ok': False,
            'error': email_result.get('error', 'mail_failed'),
            'detail': email_result.get('detail', ''),
            'recipient': email_result.get(
                'recipient',
                getattr(settings, 'OTP_RECIPIENT', ''),
            ),
        }, status=502)

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
    parish_data_service = ParishDataService.for_request(request)
    return JsonResponse(parish_data_service.load())


@login_required
@require_http_methods(['POST'])
def parish_action_api(request):
    try:
        request_body = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid_json'}, status=400)
    if not isinstance(request_body, dict):
        return JsonResponse({'ok': False, 'error': 'invalid_payload'}, status=400)
    action_name = request_body.get('action')
    if not action_name:
        return JsonResponse({'ok': False, 'error': 'missing_action'}, status=400)
    if action_name == 'reset_demo' and not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)
    action_payload = request_body.get('payload') or {}
    parish_data_service = ParishDataService.for_request(request)
    if action_name == 'reset_demo':
        from sakramenti.services.baptism_records import reconcile_baptism_records

        with transaction.atomic():
            baptism_records = parish_data_service.reset_demo()
            reconcile_baptism_records(
                parish_data_service.parish,
                baptism_records,
                actor=request.user,
            )
        return JsonResponse({
            'ok': True,
            'data': parish_data_service.load(),
        })
    action_result = dispatch_action(
        action_name,
        action_payload,
        parish_data_service,
        actor=request.user,
    )
    response_status = 200 if action_result.get('ok') else 400
    return JsonResponse(action_result, status=response_status)
