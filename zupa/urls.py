from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

admin.site.site_header = 'Pastoral — tehnička administracija'
admin.site.site_title = 'Pastoral admin'
admin.site.index_title = 'Kontrola sustava i podatkovne jezgre'
admin.site.site_url = '/app/'

urlpatterns = [
    path('', include('pastoral.urls')),
    path('zupa/', include('public_site.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # Koristi staticfiles findere kako bi razvojni server poslužio i assets iz
    # pojedinih Django aplikacija, ne samo iz projektnog static direktorija.
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))
