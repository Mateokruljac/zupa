"""URL-ovi za Sakramente.

Uključuju se u `zupa/urls.py` ispod `pages/`. Javni put ostaje
`/pages/<slug>/`, a `pastoral:page` i dalje radi za reverse.
"""
from django.urls import path

from sakramenti import views

app_name = 'sakramenti'

urlpatterns = [
    path('krsenja/', views.krsenja, name='krsenja'),
    path('vjencanja/', views.vjencanja, name='vjencanja'),
    path('pogrebi/', views.pogrebi, name='pogrebi'),
    path('pomazanje/', views.pomazanje, name='pomazanje'),
    path('krizma/', views.krizma, name='krizma'),
    path('prva-pricest/', views.prva_pricest, name='prva_pricest'),
]
