"""URL-ovi Liturgije. Uključeni u `zupa/urls.py` ispod `pages/`."""
from django.urls import path

from liturgija import views

app_name = 'liturgija'

urlpatterns = [
    path('nakane/', views.nakane, name='nakane'),
    path('mise/', views.mise, name='mise'),
    path('zupni-listic/', views.zupni_listic, name='zupni_listic'),
]
