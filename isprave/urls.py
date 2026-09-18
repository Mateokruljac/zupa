"""URL-ovi za Isprave.

Uključuju se u `zupa/urls.py` ispod `pages/`. Javni put ostaje
`/pages/<slug>/`, a `pastoral:page` i dalje radi za reverse.
"""
from django.urls import path

from isprave import views

app_name = 'isprave'

urlpatterns = [
    path('potvrde/', views.potvrde, name='potvrde'),
    path('maticne-knjige/', views.maticne_knjige, name='maticne_knjige'),
]
