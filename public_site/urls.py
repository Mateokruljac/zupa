from django.urls import path

from . import views

app_name = 'public_site'

urlpatterns = [
    path('<slug:subdomain>/obrasci/<slug:form>/', views.parish_public_form_view, name='public_form'),
    path('<slug:subdomain>/pregled/', views.preview_website_view, name='preview'),
    path('<slug:subdomain>/', views.public_website_view, name='website'),
]
