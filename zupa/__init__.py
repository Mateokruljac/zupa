try:
    from .celery import app as celery_app
except ImportError:  # lokalno bez Celeryja
    celery_app = None

__all__ = ('celery_app',)
