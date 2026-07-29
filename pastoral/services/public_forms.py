from django.conf import settings
from django.forms import Form
from django.utils import timezone

from pastoral.services.data import ParishDataService
from pastoral.services.mail import send_public_submission_email
from pastoral.tasks import send_public_submission_task


EMAIL_TEMPLATES = {
    'prijava-krizma': 'email/public/krizma',
    'prijava-krsenje': 'email/public/krsenje',
    'prijava-pricest': 'email/public/pricest',
    'prijava-ukop': 'email/public/ukop',
}

EMAIL_SUBJECTS = {
    'prijava-krizma': 'Nova prijava — Krizma',
    'prijava-krsenje': 'Nova prijava — Krštenje',
    'prijava-pricest': 'Nova prijava — Prva pričest',
    'prijava-ukop': 'Nova prijava — Ukop / pogreb',
}


def _format_value(value) -> str:
    if value is None or value == '':
        return '—'
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return str(value)


def build_submission_payload(form_slug: str, form: Form) -> dict:
    cd = form.cleaned_data.copy()
    address = form.resolved_address()
    cd['adresa'] = address
    cd.pop('street_id', None)
    cd.pop('house_number', None)
    cd.pop('gdpr_consent', None)

    display = []
    skip = {'street_id', 'house_number', 'gdpr_consent', 'adresa'}
    for name, field in form.fields.items():
        if name in skip:
            continue
        display.append({
            'label': field.label or name,
            'value': _format_value(cd.get(name)),
        })
    display.append({'label': 'Adresa', 'value': address})

    contact_name = (
        cd.get('ime_djeteta')
        or f"{cd.get('ime', '')} {cd.get('prezime', '')}".strip()
        or cd.get('pokojnik')
        or cd.get('kontakt')
        or '—'
    )

    return {
        'formType': form_slug,
        'type': form_slug,
        'submittedAt': timezone.now().isoformat(),
        'status': 'nova',
        'name': contact_name,
        'phone': cd.get('telefon', ''),
        'email': cd.get('email', ''),
        'address': address,
        'data': {k: _format_value(v) for k, v in cd.items()},
        'displayFields': display,
    }


def dispatch_public_submission_email(form_slug: str, payload: dict, *, timeout: int = 20) -> tuple[bool, dict]:
    svc = ParishDataService()
    parish_settings = svc.load_settings()
    recipient = parish_settings.get('email') or getattr(settings, 'OTP_RECIPIENT', '')

    template_base = EMAIL_TEMPLATES[form_slug]
    context = {
        'form_title': payload.get('name', ''),
        'submitted_at': payload.get('submittedAt', ''),
        'fields': payload.get('displayFields', []),
        'phone': payload.get('phone', ''),
        'email': payload.get('email', ''),
        'address': payload.get('address', ''),
        'parish_name': parish_settings.get('shortName') or parish_settings.get('name') or 'Pastoral',
        'parish_email': parish_settings.get('email', ''),
        'parish_phone': parish_settings.get('phone', ''),
        'primary_color': parish_settings.get('primaryColor', '#5c2e3a'),
        'accent_color': parish_settings.get('accentColor', '#b8922a'),
    }

    task = send_public_submission_task.delay(
        to_email=recipient,
        subject=EMAIL_SUBJECTS.get(form_slug, 'Nova javna prijava'),
        template_base=template_base,
        context=context,
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
