from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


admin.site.site_header = 'Administracija javnih župnih stranica'
admin.site.site_title = 'Župne web-stranice'
admin.site.index_title = 'Javni sadržaj i objave'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('public_site.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
