"""URL-ovi za Liturgija.

Uključuju se u `zupa/urls.py` ispod `pages/`. Javni put ostaje
`/pages/<slug>/`, a `pastoral:page` i dalje radi za reverse.
"""
from django.urls import path

from liturgija import views

app_name = 'liturgija'

urlpatterns = [
    path('nakane/', views.nakane, name='nakane'),
    path('mise/', views.mise, name='mise'),
    path('zupni-listic/', views.zupni_listic, name='zupni_listic'),
]
