from celery import shared_task
from django.conf import settings

from pastoral.services.mail import send_otp_login_email, send_public_submission_email


@shared_task
def send_public_submission_task(
    to_email: str,
    subject: str,
    template_base: str,
    context: dict,
) -> dict:
    try:
        send_public_submission_email(
            to=to_email,
            subject=subject,
            template_base=template_base,
            context=context,
        )
        return {'ok': True, 'recipient': to_email}
    except Exception as exc:
        return {
            'ok': False,
            'error': 'send_failed',
            'detail': str(exc),
            'recipient': to_email or getattr(settings, 'OTP_RECIPIENT', ''),
        }


@shared_task
def send_otp_email_task(
    to_email: str,
    otp_code: str,
    user_email: str,
    role_label: str,
    parish_name: str,
    ttl_minutes: int,
    primary_color: str,
    accent_color: str,
    parish_email: str = '',
) -> dict:
    try:
        send_otp_login_email(
            to_email=to_email,
            otp_code=otp_code,
            user_email=user_email,
            role_label=role_label,
            parish_name=parish_name,
            ttl_minutes=ttl_minutes,
            primary_color=primary_color,
            accent_color=accent_color,
            parish_email=parish_email,
        )
        return {'ok': True, 'recipient': to_email}
    except Exception as exc:
        return {
            'ok': False,
            'error': 'send_failed',
            'detail': str(exc),
            'recipient': to_email or getattr(settings, 'OTP_RECIPIENT', ''),
        }
