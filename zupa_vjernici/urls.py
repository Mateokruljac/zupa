from django.urls import path
from zupa_vjernici import views

app_name = 'zupa_vjernici'

urlpatterns = [
    path('obitelji/', views.obitelji, name='obitelji'),
    path('ulice/', views.ulice, name='ulice'),
    path('posjete/', views.posjete, name='posjete'),
]
