"""Django app Liturgija: kalendar, mise, nakane, župni listić."""
from django.apps import AppConfig


class LiturgijaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'liturgija'
    verbose_name = 'Liturgija'
