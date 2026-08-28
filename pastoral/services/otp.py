import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone

from pastoral.models import OtpChallenge
from pastoral.services.data import ParishDataService
from pastoral.services.mail import send_otp_login_email
from pastoral.models import User


def _role_label(role: str) -> str:
    return dict(User.ROLE_CHOICES).get(role, role)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


@transaction.atomic
def send_login_code(request, *, email: str, role: str) -> tuple[bool, dict]:
    """Generira kod, šalje ga mailom i pamti pending sesiju.

    Vraća ``(True, {recipient, ...})`` ili ``(False, {error, ...})``.
    """
    normalized_email = _normalize_email(email)
    now = timezone.now()
    cooldown_seconds = getattr(settings, 'OTP_RESEND_COOLDOWN_SECONDS', 60)

    latest = (
        OtpChallenge.objects.select_for_update()
        .filter(email=normalized_email, role=role, used=False)
        .order_by('-created_at')
        .first()
    )
    if latest is not None:
        retry_at = latest.created_at + timedelta(seconds=cooldown_seconds)
        if retry_at > now:
            return False, {
                'error': 'cooldown',
                'retry_after_seconds': max(
                    1,
                    int((retry_at - now).total_seconds()) + 1,
                ),
            }

    OtpChallenge.objects.filter(
        email=normalized_email,
        role=role,
        used=False,
    ).update(used=True)

    code = f'{secrets.randbelow(1_000_000):06d}'
    OtpChallenge.objects.create(
        email=normalized_email,
        code=make_password(code),
        role=role,
        expires_at=now + timedelta(
            minutes=getattr(settings, 'OTP_TTL_MINUTES', 10),
        ),
    )

    parish_settings = ParishDataService().load_settings()
    recipient = (
        getattr(settings, 'OTP_RECIPIENT', '')
        or parish_settings.get('email', '')
    )
    try:
        send_otp_login_email(
            to_email=recipient,
            otp_code=code,
            user_email=normalized_email,
            role_label=_role_label(role),
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
    except Exception as error:
        OtpChallenge.objects.filter(
            email=normalized_email,
            role=role,
            used=False,
        ).update(used=True)
        return False, {
            'error': 'mail_failed',
            'detail': str(error),
            'recipient': recipient,
        }

    request.session['otp_pending'] = {
        'email': normalized_email,
        'role': role,
    }
    return True, {'ok': True, 'recipient': recipient}


@transaction.atomic
def verify_login_code(email: str, role: str, submitted_code: str) -> tuple[bool, str]:
    """Provjeri kod: postoji, nije istekao, odgovara — zatim ga potroši.

    Status: ``verified`` | ``expired`` | ``invalid`` | ``missing``.
    """
    challenge = (
        OtpChallenge.objects.select_for_update()
        .filter(
            email=_normalize_email(email),
            role=role,
            used=False,
        )
        .order_by('-created_at')
        .first()
    )
    if challenge is None:
        return False, 'missing'

    if challenge.expires_at <= timezone.now():
        challenge.used = True
        challenge.save(update_fields=['used'])
        return False, 'expired'

    if not check_password(submitted_code, challenge.code):
        return False, 'invalid'

    challenge.used = True
    challenge.save(update_fields=['used'])
    return True, 'verified'
