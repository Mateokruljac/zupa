"""URL-ovi public scheme: upravljanje tenantima, ne župni ured.

Župna aplikacija ide na domenu tenanta (`ROOT_URLCONF`).
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path

admin.site.site_header = 'e-Župa — tenanti'
admin.site.site_title = 'Tenanti'
admin.site.index_title = 'Public schema'


def public_index(request):
    tenant = getattr(request, 'tenant', None)
    host = request.get_host()
    return HttpResponse(
        'Public schema (control plane).\n'
        f'Host: {host}\n'
        f'Tenant: {getattr(tenant, "schema_name", "public")}\n'
        'Župni ured otvara se na domeni tenanta. Admin tenanata: /admin/\n',
        content_type='text/plain; charset=utf-8',
    )


urlpatterns = [
    path('', public_index),
    path('admin/', admin.site.urls),
]
