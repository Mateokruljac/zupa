import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from pastoral.forms import PUBLIC_FORM_CLASSES, PUBLIC_FORM_INTROS
from pastoral.services.data import ParishDataService
from pastoral.services.public_forms import build_submission_payload, dispatch_public_submission_email
from control_plane.models import ParishMembership

from .models import ParishWebsite
from .snapshots import build_public_snapshot


PUBLIC_FORM_LABELS = {
    'prijava-krizma': 'Prijava za krizmu',
    'prijava-krsenje': 'Prijava za krštenje',
    'prijava-pricest': 'Prijava za prvu pričest',
    'prijava-ukop': 'Dogovor pogreba i ukopa',
}


def _live_website(subdomain):
    website = (
        ParishWebsite.objects
        .select_related('parish')
        .filter(subdomain=subdomain, status=ParishWebsite.Status.LIVE)
        .first()
    )
    if website is None:
        raise Http404()
    return website


def public_website_view(request, subdomain):
    website = _live_website(subdomain)
    configuration = website.published_configuration or {}
    website_view = {
        'subdomain': website.subdomain,
        'template_key': configuration.get('template_key', website.template_key),
        'primary_color': configuration.get('primary_color', website.primary_color),
        'accent_color': configuration.get('accent_color', website.accent_color),
    }
    return render(request, 'public_site/website.html', {
        'website': website_view,
        'snapshot': build_public_snapshot(website, configuration=configuration),
        'preview_mode': False,
    })


@login_required(login_url='pastoral:login')
def preview_website_view(request, subdomain):
    website = (
        ParishWebsite.objects.select_related('parish')
        .filter(subdomain=subdomain)
        .first()
    )
    if website is None:
        raise Http404()
    has_membership = ParishMembership.objects.filter(
        parish=website.parish,
        user=request.user,
        status=ParishMembership.Status.ACTIVE,
    ).exists()
    if not (request.user.is_superuser or has_membership):
        raise Http404()
    return render(request, 'public_site/website.html', {
        'website': website,
        'snapshot': build_public_snapshot(website, preview=True),
        'preview_mode': True,
    })


@require_http_methods(['GET', 'POST'])
def parish_public_form_view(request, subdomain, form):
    if form not in PUBLIC_FORM_CLASSES:
        raise Http404()
    website = _live_website(subdomain)
    svc = ParishDataService(website.parish)
    parish_settings = svc.load_settings()
    form_kwargs = {
        'streets': svc.load().get('streets', []),
        'parish_email': website.contact_email or parish_settings.get('email', ''),
        'parish_phone': website.phone or parish_settings.get('phone', ''),
    }
    form_class = PUBLIC_FORM_CLASSES[form]
    if request.method == 'POST':
        bound_form = form_class(request.POST, **form_kwargs)
        if bound_form.is_valid():
            payload = build_submission_payload(form, bound_form)
            data = svc.load()
            payload['id'] = f'ps_{uuid.uuid4().hex[:8]}'
            data.setdefault('publicSubmissions', []).insert(0, payload)
            svc.save(data)
            mail_ok, mail_result = dispatch_public_submission_email(form, payload)
            if mail_ok:
                messages.success(request, 'Prijava je zaprimljena. Župni ured će vas kontaktirati.')
            else:
                detail = mail_result.get('detail') or mail_result.get('error', 'mail_failed')
                messages.warning(request, f'Prijava je spremljena; slanje e-maila nije uspjelo ({detail}).')
            return redirect(f"{reverse('public_site:website', args=[subdomain])}#obrasci")
    else:
        bound_form = form_class(**form_kwargs)
    return render(request, 'pastoral/public/form.html', {
        'form_slug': form,
        'form_title': PUBLIC_FORM_LABELS[form],
        'form_intro': PUBLIC_FORM_INTROS.get(form, ''),
        'form': bound_form,
        'parish_settings': {
            **parish_settings,
            'email': website.contact_email or parish_settings.get('email', ''),
            'phone': website.phone or parish_settings.get('phone', ''),
        },
        'street_not_listed': '__other__',
        'public_site_url': reverse('public_site:website', args=[subdomain]),
    })
