"""URL-ovi za Pregled.

Nadzorna ploča živi na `/app/`. Uključuje se u `zupa/urls.py` ispred
pastoral shella. `pastoral:app` ostaje kompatibilni reverse alias.
"""
from django.urls import path

from pregled import views

app_name = 'pregled'

urlpatterns = [
    path('app/', views.dashboard, name='dashboard'),
]
