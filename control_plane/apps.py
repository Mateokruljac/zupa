from django.apps import AppConfig


class ControlPlaneConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'control_plane'
    verbose_name = 'SaaS control plane'

    def ready(self):
        from . import checks  # noqa: F401

