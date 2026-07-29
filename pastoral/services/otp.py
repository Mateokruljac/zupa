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
    svc = ParishDataService()
    parish_settings = svc.load_settings()
    recipient = getattr(settings, 'OTP_RECIPIENT', '') or parish_settings.get('email', '')

    task = send_otp_email_task.delay(
        to_email=recipient,
        otp_code=code,
        user_email=email,
        role_label=role_label_for(role),
        parish_name=parish_settings.get('shortName') or parish_settings.get('name') or 'Pastoral',
        ttl_minutes=getattr(settings, 'OTP_TTL_MINUTES', 10),
        primary_color=parish_settings.get('primaryColor', '#5c2e3a'),
        accent_color=parish_settings.get('accentColor', '#b8922a'),
        parish_email=parish_settings.get('email', ''),
    )

    try:
        result = task.get(timeout=timeout)
    except Exception as exc:
        return False, {
            'error': 'mail_timeout',
            'detail': str(exc),
            'recipient': recipient,
        }

    if not result.get('ok'):
        return False, result

    return True, result
