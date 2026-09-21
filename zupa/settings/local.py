from .base import *

INSTALLED_APPS.append('debug_toolbar')
MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')

DEBUG = environment.bool('DEBUG', default=True)
ALLOWED_HOSTS = ['*']
STATIC_ROOT = BASE_DIR / 'staticfiles'

INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Baza je uvijek PostgreSQL (servis `db` u docker-compose.yml).
# Izvan kontejnera host `db` nije DNS ime — koristi objavljeni port na localhostu.
IN_DOCKER = Path('/.dockerenv').exists()
if not IN_DOCKER:
    if DATABASES['default']['HOST'] in ('db', 'postgres'):
        DATABASES['default']['HOST'] = '127.0.0.1'
    if EMAIL_HOST in ('mailhog', 'localhost'):
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
