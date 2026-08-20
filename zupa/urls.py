from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from pastoral import views as pastoral_views

handler404 = 'zupa.error_views.page_not_found'
handler500 = 'zupa.error_views.server_error'

admin.site.site_header = 'Pastoral — tehnička administracija'
admin.site.site_title = 'Pastoral admin'
admin.site.index_title = 'Kontrola sustava i podatkovne jezgre'
admin.site.site_url = '/app/'

urlpatterns = [
    path('', include('pastoral.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path(
        'admin/login/',
        pastoral_views.admin_login_redirect_view,
        name='unified_admin_login',
    ),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # Koristi staticfiles findere kako bi razvojni server poslužio i assets iz
    # pojedinih Django aplikacija, ne samo iz projektnog static direktorija.
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))
