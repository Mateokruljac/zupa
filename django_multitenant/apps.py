from django.apps import AppConfig


class DjangoMultitenantConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_multitenant'
    verbose_name = 'Tenanti'
