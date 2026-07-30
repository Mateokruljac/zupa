from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DEBUG = os.environ.get('DEBUG', True)
ALLOWED_HOSTS = ['*']
STATIC_ROOT = BASE_DIR / 'staticfiles'

INTERNAL_IPS = ['127.0.0.1', 'localhost']

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True,
}

# Izvan Dockera: SMTP ide na 127.0.0.1:1025 (Mailhog mapiran s kontejnera)
# Web sučelje za pregled mailova: http://localhost:8025 — NE koristiti za slanje!
IN_DOCKER = os.path.exists('/.dockerenv')
if not IN_DOCKER and EMAIL_HOST in ('mailhog', 'localhost'):
    EMAIL_HOST = '127.0.0.1'
    MAILHOG_SMTP_HOST = '127.0.0.1'

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://:password@127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_TASK_ALWAYS_EAGER = os.environ.get('CELERY_TASK_ALWAYS_EAGER', 'True') == 'True'
