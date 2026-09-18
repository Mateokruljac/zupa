"""URL-ovi za Župni ured.

Uključuju se u `zupa/urls.py` ispod `pages/`. Javni put ostaje
`/pages/<slug>/`, a `pastoral:page` i dalje radi za reverse.
"""
from django.urls import path

from ured import views

app_name = 'ured'

urlpatterns = [
    path('kalendar/', views.kalendar, name='kalendar'),
    path('podsjetnici/', views.podsjetnici, name='podsjetnici'),
    path('vijeca/', views.vijeca, name='vijeca'),
    path('postavke/', views.postavke, name='postavke'),
    path('javne-prijave/', views.javne_prijave, name='javne_prijave'),
]
