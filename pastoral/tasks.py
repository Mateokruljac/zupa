from celery import shared_task
from django.conf import settings

from pastoral.services.mail import send_public_submission_email


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
