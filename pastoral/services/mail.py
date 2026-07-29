from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_html_email(
    *,
    subject: str,
    to: list[str],
    html_template: str,
    context: dict,
    text_template: str | None = None,
    from_email: str | None = None,
) -> None:
    """Send HTML e-mail with optional plain-text alternative."""
    ctx = dict(context)
    text_body = render_to_string(text_template or html_template.replace('.html', '.txt'), ctx)
    html_body = render_to_string(html_template, ctx)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        to=to,
    )
    message.attach_alternative(html_body, 'text/html')
    message.send(fail_silently=False)


def send_public_submission_email(
    *,
    to: str | list[str],
    subject: str,
    template_base: str,
    context: dict,
    from_email: str | None = None,
) -> None:
    """Send priest notification for a public sacrament form submission."""
    recipients = [to] if isinstance(to, str) else to
    send_html_email(
        subject=subject,
        to=recipients,
        html_template=f'{template_base}.html',
        text_template=f'{template_base}.txt',
        context=context,
        from_email=from_email,
    )


def send_otp_login_email(
    *,
    to_email: str,
    otp_code: str,
    user_email: str,
    role_label: str,
    parish_name: str,
    ttl_minutes: int,
    primary_color: str,
    accent_color: str,
    parish_email: str = '',
) -> None:
    context = {
        'otp_code': otp_code,
        'user_email': user_email,
        'role_label': role_label,
        'parish_name': parish_name,
        'ttl_minutes': ttl_minutes,
        'primary_color': primary_color,
        'accent_color': accent_color,
        'parish_email': parish_email,
    }
    subject = f'Pastoral — kod za prijavu: {otp_code}'
    send_html_email(
        subject=subject,
        to=[to_email],
        html_template='email/otp_login.html',
        text_template='email/otp_login.txt',
        context=context,
    )
