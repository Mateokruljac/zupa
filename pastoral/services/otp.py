import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone

from pastoral.models import OtpChallenge
from pastoral.services.data import ParishDataService
from pastoral.tasks import send_otp_email_task
from users.models import User


class OtpCooldownError(Exception):
    """Novi kod je zatražen prije isteka sigurnosnog razmaka."""

    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds
        super().__init__('otp_resend_cooldown')


def generate_otp_code() -> str:
    """Generiraj kriptografski siguran šesteroznamenkasti kod."""
    return f'{secrets.randbelow(1_000_000):06d}'


def role_label_for(role: str) -> str:
    return dict(User.ROLE_CHOICES).get(role, role)


def store_otp_session(request, *, email: str, role: str) -> None:
    request.session['otp_pending'] = {'email': email, 'role': role}


@transaction.atomic
def create_otp_challenge(email: str, role: str) -> str:
    normalized_email = email.strip().lower()
    current_time = timezone.now()
    cooldown_seconds = getattr(settings, 'OTP_RESEND_COOLDOWN_SECONDS', 60)
    latest_challenge = (
        OtpChallenge.objects.select_for_update()
        .filter(email=normalized_email, role=role, used=False)
        .order_by('-created_at')
        .first()
    )
    if latest_challenge:
        retry_at = latest_challenge.created_at + timedelta(seconds=cooldown_seconds)
        if retry_at > current_time:
            remaining_seconds = max(1, int((retry_at - current_time).total_seconds()) + 1)
            raise OtpCooldownError(remaining_seconds)

    OtpChallenge.objects.filter(
        email=normalized_email,
        role=role,
        used=False,
    ).update(used=True)

    verification_code = generate_otp_code()
    OtpChallenge.objects.create(
        email=normalized_email,
        code=make_password(verification_code),
        role=role,
        expires_at=current_time + timedelta(
            minutes=getattr(settings, 'OTP_TTL_MINUTES', 10),
        ),
    )
    return verification_code


@transaction.atomic
def verify_otp_challenge(email: str, role: str, submitted_code: str) -> tuple[bool, str]:
    """Provjeri najnoviji kod uz rok valjanosti i ograničen broj pokušaja."""
    challenge = (
        OtpChallenge.objects.select_for_update()
        .filter(
            email=email.strip().lower(),
            role=role,
            used=False,
        )
        .order_by('-created_at')
        .first()
    )
    if challenge is None:
        return False, 'missing'

    current_time = timezone.now()
    if challenge.expires_at <= current_time:
        challenge.used = True
        challenge.save(update_fields=['used'])
        return False, 'expired'

    maximum_attempts = getattr(settings, 'OTP_MAX_ATTEMPTS', 5)
    if challenge.locked_at or challenge.failed_attempts >= maximum_attempts:
        return False, 'locked'

    if not check_password(submitted_code, challenge.code):
        challenge.failed_attempts += 1
        updated_fields = ['failed_attempts']
        if challenge.failed_attempts >= maximum_attempts:
            challenge.locked_at = current_time
            challenge.used = True
            updated_fields.extend(['locked_at', 'used'])
        challenge.save(update_fields=updated_fields)
        return False, 'locked' if challenge.used else 'invalid'

    challenge.used = True
    challenge.save(update_fields=['used'])
    return True, 'verified'


def invalidate_latest_otp_challenge(email: str, role: str) -> None:
    OtpChallenge.objects.filter(
        email=email.strip().lower(),
        role=role,
        used=False,
    ).update(used=True)


def request_otp_delivery(
    request,
    *,
    email: str,
    role: str,
    timeout: int = 20,
) -> tuple[bool, dict]:
    """Kreiraj izazov, pošalji kod i spremi sesiju kao jednu operaciju."""
    verification_code = create_otp_challenge(email, role)
    email_was_sent, email_result = dispatch_otp_email(
        verification_code,
        email,
        role,
        timeout=timeout,
    )
    if not email_was_sent:
        invalidate_latest_otp_challenge(email, role)
        return False, email_result

    store_otp_session(request, email=email, role=role)
    return True, email_result


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
