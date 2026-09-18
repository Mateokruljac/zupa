"""URL-ovi za Financije.

Uključuju se u `zupa/urls.py` ispod `pages/`. Javni put ostaje
`/pages/<slug>/`, a `pastoral:page` i dalje radi za reverse.
"""
from django.urls import path

from financije import views

app_name = 'financije'

urlpatterns = [
    path('dugovanja/', views.dugovanja, name='dugovanja'),
    path('blagajna/', views.blagajna, name='blagajna'),
    path('racuni/', views.racuni, name='racuni'),
    path(
        'financijska-izvjestaja/',
        views.financijska_izvjestaja,
        name='financijska_izvjestaja',
    ),
]
