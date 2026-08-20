from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST
from django_ratelimit.decorators import ratelimit

from pastoral.forms import LoginForm, OtpVerifyForm
from pastoral.services.data import ParishDataService
from pastoral.services.otp import (
    OtpCooldownError,
    request_otp_delivery,
    verify_otp_challenge,
)
from users.models import User


def index_view(request):
    return redirect('pastoral:login')


def _render_login_page(request, context, *, status=200):
    requested_destination = request.GET.get('next', '')
    login_context = {
        'parish_settings': ParishDataService().load_settings(),
        'technical_admin_login': requested_destination.startswith('/admin/'),
        **context,
    }
    return render(request, 'pastoral/login.html', login_context, status=status)


def _login_destination(request, authenticated_user):
    requested_destination = (
        request.GET.get('next')
        or request.POST.get('next')
        or ''
    )
    destination_is_safe = url_has_allowed_host_and_scheme(
        requested_destination,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )
    if not destination_is_safe:
        return reverse('pastoral:app')
    if requested_destination.startswith('/admin/') and not authenticated_user.is_staff:
        messages.warning(
            request,
            'Nemate ovlasti za tehničku administraciju.',
        )
        return reverse('pastoral:app')
    return requested_destination


@require_http_methods(['GET'])
def admin_login_redirect_view(request):
    requested_destination = request.GET.get('next') or reverse('admin:index')
    destination_is_safe_admin_path = (
        requested_destination.startswith('/admin/')
        and url_has_allowed_host_and_scheme(
            requested_destination,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )
    )
    if not destination_is_safe_admin_path:
        requested_destination = reverse('admin:index')
    login_url = reverse('pastoral:login')
    return redirect(
        f'{login_url}?{urlencode({"next": requested_destination})}',
    )


@require_http_methods(['GET', 'POST'])
@ratelimit(key='ip', rate='10/m', method='POST', block=False)
def login_view(request):
    if request.user.is_authenticated:
        return redirect(_login_destination(request, request.user))

    if getattr(request, 'limited', False):
        messages.error(request, 'Previše pokušaja. Pričekajte minutu pa pokušajte ponovno.')
        return _render_login_page(request, {
            'form': LoginForm(),
            'otp_form': OtpVerifyForm(),
        }, status=429)

    pending_login = request.session.get('otp_pending')
    if pending_login and request.method == 'POST' and 'code' in request.POST:
        verification_form = OtpVerifyForm(request.POST)
        if verification_form.is_valid():
            code_is_valid, verification_status = verify_otp_challenge(
                pending_login['email'],
                pending_login['role'],
                verification_form.cleaned_data['code'],
            )
            if code_is_valid:
                user, _ = User.objects.get_or_create(
                    email=pending_login['email'],
                    defaults={
                        'name': pending_login['email'].split('@')[0],
                        'role': pending_login['role'],
                    },
                )
                user.role = pending_login['role']
                user.save(update_fields=['role'])
                login(request, user)
                request.session.pop('otp_pending', None)
                messages.success(request, f'Dobrodošli, {user.role_label}.')
                return redirect(_login_destination(request, user))
            verification_messages = {
                'expired': 'Kod je istekao. Zatražite novi kod.',
                'locked': 'Dosegnut je najveći broj pokušaja. Zatražite novi kod.',
                'missing': 'Kod više nije aktivan. Zatražite novi kod.',
            }
            messages.error(
                request,
                verification_messages.get(
                    verification_status,
                    'Neispravan kod. Pokušajte ponovo.',
                ),
            )
        return _render_login_page(request, {
            'otp_mode': True,
            'otp_form': verification_form,
            'form': LoginForm(),
            'email': pending_login.get('email'),
            'otp_recipient': getattr(settings, 'OTP_RECIPIENT', ''),
        })

    login_form = LoginForm(request.POST or None)
    if request.method == 'POST' and login_form.is_valid():
        email_address = login_form.cleaned_data['email'].lower()
        user_role = (
            User.objects.filter(email__iexact=email_address)
            .values_list('role', flat=True)
            .first()
            or User._meta.get_field('role').default
        )
        try:
            email_was_sent, email_result = request_otp_delivery(
                request,
                email=email_address,
                role=user_role,
            )
        except OtpCooldownError as exception:
            messages.error(
                request,
                f'Pričekajte {exception.retry_after_seconds} sekundi prije slanja novog koda.',
            )
            return _render_login_page(request, {
                'form': login_form,
                'otp_form': OtpVerifyForm(),
            }, status=429)
        if not email_was_sent:
            error_detail = email_result.get('detail') or email_result.get(
                'error',
                'mail_failed',
            )
            messages.error(request, f'Nije moguće poslati e-mail: {error_detail}')
            return _render_login_page(request, {
                'form': login_form,
                'otp_form': OtpVerifyForm(),
            })

        recipient = email_result.get(
            'recipient',
            getattr(settings, 'OTP_RECIPIENT', ''),
        )
        messages.success(request, f'Kod je poslan na e-mail ({recipient}). Unesite ga ispod.')
        return _render_login_page(request, {
            'otp_mode': True,
            'otp_form': OtpVerifyForm(),
            'form': LoginForm(),
            'email': email_address,
            'otp_recipient': recipient,
        })

    return _render_login_page(request, {
        'form': login_form,
        'otp_form': OtpVerifyForm(),
    })


@require_POST
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Odjavljeni ste.')
    return redirect('pastoral:login')
