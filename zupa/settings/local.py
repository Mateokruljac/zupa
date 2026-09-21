from .base import *

INSTALLED_APPS.append('debug_toolbar')
SHARED_APPS.append('debug_toolbar')
MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')

DEBUG = environment.bool('DEBUG', default=True)
ALLOWED_HOSTS = ['*']
SHOW_PUBLIC_IF_NO_TENANT_FOUND = True
STATIC_ROOT = BASE_DIR / 'staticfiles'

INTERNAL_IPS = ['127.0.0.1', 'localhost','.localhost']


CELERY_BROKER_URL = environment.str(
    'CELERY_BROKER_URL',
    default='redis://:password@127.0.0.1:6379/0',
)
CELERY_RESULT_BACKEND = environment.str('CELERY_RESULT_BACKEND', default=CELERY_BROKER_URL)
CELERY_TASK_ALWAYS_EAGER = environment.bool('CELERY_TASK_ALWAYS_EAGER', default=True)

