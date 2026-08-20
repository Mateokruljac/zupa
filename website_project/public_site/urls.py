from django.urls import path

from . import views


app_name = 'public_site'

urlpatterns = [
    path('<slug:subdomain>/', views.public_website_view, name='website'),
    path(
        '<slug:subdomain>/preview/',
        views.preview_website_view,
        name='preview',
    ),
]
