from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404
from django.shortcuts import render

from .models import ParishWebsite
from .snapshots import build_public_snapshot


def _website_for_subdomain(subdomain, *, require_live=True):
    website_query = ParishWebsite.objects.filter(subdomain=subdomain)
    if require_live:
        website_query = website_query.filter(status=ParishWebsite.Status.LIVE)
    website = website_query.first()
    if website is None:
        raise Http404()
    return website


def public_website_view(request, subdomain):
    website = _website_for_subdomain(subdomain)
    return render(request, 'public_site/website.html', {
        'website': website,
        'snapshot': build_public_snapshot(website),
        'preview_mode': False,
    })


@staff_member_required
def preview_website_view(request, subdomain):
    website = _website_for_subdomain(subdomain, require_live=False)
    return render(request, 'public_site/website.html', {
        'website': website,
        'snapshot': build_public_snapshot(website, preview=True),
        'preview_mode': True,
    })
