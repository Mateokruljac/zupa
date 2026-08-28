from .base import *

INSTALLED_APPS.append('debug_toolbar')
MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DEBUG = environment.bool('DEBUG', default=True)
ALLOWED_HOSTS = ['*']
STATIC_ROOT = BASE_DIR / 'staticfiles'

INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Izvan Dockera: SMTP ide na 127.0.0.1:1025 (Mailhog mapiran s kontejnera)
# Web sučelje za pregled mailova: http://localhost:8025 — NE koristiti za slanje!
IN_DOCKER = Path('/.dockerenv').exists()
if not IN_DOCKER and EMAIL_HOST in ('mailhog', 'localhost'):
    EMAIL_HOST = '127.0.0.1'
    MAILHOG_SMTP_HOST = '127.0.0.1'

CELERY_BROKER_URL = environment.str(
    'CELERY_BROKER_URL',
    default='redis://:password@127.0.0.1:6379/0',
)
CELERY_RESULT_BACKEND = environment.str('CELERY_RESULT_BACKEND', default=CELERY_BROKER_URL)
CELERY_TASK_ALWAYS_EAGER = environment.bool('CELERY_TASK_ALWAYS_EAGER', default=True)

# Privremena kompatibilnost za postojeći JSON demo. Produkcija je fail-closed.
TENANCY_LEGACY_FALLBACK_ENABLED = True
