import random

from django.conf import settings

from pastoral.models import OtpChallenge
from pastoral.services.data import ParishDataService
from pastoral.tasks import send_otp_email_task
from users.models import User


def generate_otp_code() -> str:
    return f'{random.randint(0, 999999):06d}'


def role_label_for(role: str) -> str:
    return dict(User.ROLE_CHOICES).get(role, role)


def store_otp_session(request, *, email: str, role: str) -> None:
    request.session['otp_pending'] = {'email': email, 'role': role}


def create_otp_challenge(email: str, role: str) -> str:
    code = generate_otp_code()
    OtpChallenge.objects.create(email=email, code=code, role=role)
    return code


def dispatch_otp_email(code: str, email: str, role: str, *, timeout: int = 20) -> tuple[bool, dict]:
    parish_data_service = ParishDataService()
    parish_settings = parish_data_service.load_settings()
    recipient = getattr(settings, 'OTP_RECIPIENT', '') or parish_settings.get('email', '')

    try:
        email_task_result = send_otp_email_task.delay(
            to_email=recipient,
            otp_code=code,
            user_email=email,
            role_label=role_label_for(role),
            parish_name=(
                parish_settings.get('shortName')
                or parish_settings.get('name')
                or 'Pastoral'
            ),
            ttl_minutes=getattr(settings, 'OTP_TTL_MINUTES', 10),
            primary_color=parish_settings.get('primaryColor', '#5c2e3a'),
            accent_color=parish_settings.get('accentColor', '#b8922a'),
            parish_email=parish_settings.get('email', ''),
        )
    except Exception as exception:
        return False, {
            'error': 'mail_queue_unavailable',
            'detail': str(exception),
            'recipient': recipient,
        }

    try:
        email_result = email_task_result.get(timeout=timeout)
    except Exception as exception:
        return False, {
            'error': 'mail_timeout',
            'detail': str(exception),
            'recipient': recipient,
        }

    if not email_result.get('ok'):
        return False, email_result

    return True, email_result
