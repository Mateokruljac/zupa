import uuid

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from pastoral.forms import (
    PUBLIC_FORM_CLASSES,
    PUBLIC_FORM_INTROS,
)
from pastoral.services.data import ParishDataService
from pastoral.services.public_forms import (
    build_submission_payload,
    dispatch_public_submission_email,
)


PUBLIC_FORM_LABELS = {
    'prijava-krizma': 'Prijava za krizmu',
    'prijava-krsenje': 'Prijava za krštenje',
    'prijava-pricest': 'Prijava za prvu pričest',
    'prijava-ukop': 'Prijava za ukop',
}
PUBLIC_FORMS = set(PUBLIC_FORM_LABELS)


def public_index_view(request):
    parish_data_service = ParishDataService()
    parish_settings = parish_data_service.load_settings()
    return render(request, 'pastoral/public/index.html', {
        'parish_settings': parish_settings,
    })


@require_http_methods(['GET', 'POST'])
def public_form_view(request, form: str):
    if form not in PUBLIC_FORMS:
        raise Http404()

    parish_data_service = ParishDataService()
    parish_settings = parish_data_service.load_settings()
    parish_data = parish_data_service.load()
    streets = parish_data.get('streets', [])

    form_class = PUBLIC_FORM_CLASSES[form]
    form_kwargs = {
        'streets': streets,
        'parish_email': parish_settings.get('email', ''),
        'parish_phone': parish_settings.get('phone', ''),
    }

    if request.method == 'POST':
        public_form = form_class(request.POST, **form_kwargs)
        if public_form.is_valid():
            submission_payload = build_submission_payload(form, public_form)
            parish_data = parish_data_service.load()
            submission_payload['id'] = f'ps_{uuid.uuid4().hex[:8]}'
            parish_data.setdefault('publicSubmissions', []).insert(
                0,
                submission_payload,
            )
            parish_data_service.save(parish_data)

            email_was_sent, email_result = dispatch_public_submission_email(
                form,
                submission_payload,
            )
            if email_was_sent:
                messages.success(
                    request,
                    'Prijava je zaprimljena. Župni ured će vas kontaktirati na navedeni telefon.',
                )
            else:
                error_detail = (
                    email_result.get('detail')
                    or email_result.get('error', 'mail_failed')
                )
                messages.warning(
                    request,
                    'Prijava je spremljena, ali e-mail obavijest nije poslana '
                    f'({error_detail}). '
                    'Molimo nazovite župni ured.',
                )
            return redirect('pastoral:public_index')
    else:
        public_form = form_class(**form_kwargs)

    return render(request, 'pastoral/public/form.html', {
        'form_slug': form,
        'form_title': PUBLIC_FORM_LABELS.get(form, form),
        'form_intro': PUBLIC_FORM_INTROS.get(form, ''),
        'form': public_form,
        'parish_settings': parish_settings,
        'street_not_listed': '__other__',
    })
