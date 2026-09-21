from pathlib import Path

import environ

from .admin_sidebar import ADMIN_REORDER

BASE_DIR = Path(__file__).resolve().parent.parent.parent
environment = environ.Env()
environment.read_env(BASE_DIR / '.env')

SECRET_KEY = environment.str(
    'SECRET_KEY',
    default='django-insecure-dev-only-change-in-production',
)

DEBUG = False
ALLOWED_HOSTS = ['*']

SHARED_APPS = [
    'django_tenants',
    'django_multitenant',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'django_celery_beat',
]

TENANT_APPS = [
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'pastoral',
    'pregled',
    'zupa_vjernici',
    'sakramenti',
    'financije',
    'isprave',
    'ured',
    'liturgija',
]

INSTALLED_APPS = SHARED_APPS + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'zupa.middleware.request_tenant.RequestMiddleware',
]

ROOT_URLCONF = 'zupa.urls'
PUBLIC_SCHEMA_URLCONF = 'zupa.urls_public'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': [BASE_DIR / 'templates'],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'pastoral.context_processors.pastoral_globals',
            ],
        },
    },
]

WSGI_APPLICATION = 'zupa.wsgi.application'

# Iste zadane vjerodajnice kao `db` servis u docker-compose.yml.
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': environment.str('DB_NAME', default='zupa'),
        'USER': environment.str('DB_USER', default='zupa'),
        'PASSWORD': environment.str('DB_PASS', default='zupa'),
        'HOST': environment.str('DB_HOST', default='db'),
        'PORT': environment.str('DB_PORT', default='5432'),
        'CONN_MAX_AGE': environment.int('DB_CONN_MAX_AGE', default=60),
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

DATABASE_ROUTERS = ('django_tenants.routers.TenantSyncRouter',)

TENANT_MODEL = 'django_multitenant.Tenant'
TENANT_DOMAIN_MODEL = 'django_multitenant.Domain'
SHOW_PUBLIC_IF_NO_TENANT_FOUND = False

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'hr'
LANGUAGES = (
    ('hr', 'Hrvatski'),
)
TIME_ZONE = 'Europe/Zagreb'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'static' / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


AUTH_USER_MODEL = 'django_multitenant.User'

LOGIN_URL = 'pastoral:login'
LOGOUT_REDIRECT_URL = 'pastoral:login'

DEFAULT_FROM_EMAIL = environment.str('DEFAULT_FROM_EMAIL', default='noreply@pastoral.local')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
OTP_RECIPIENT = environment.str('OTP_RECIPIENT', default='mateokruljac123@gmail.com')
OTP_TTL_MINUTES = environment.int('OTP_TTL_MINUTES', default=10)
OTP_MAX_ATTEMPTS = environment.int('OTP_MAX_ATTEMPTS', default=5)
OTP_RESEND_COOLDOWN_SECONDS = environment.int(
    'OTP_RESEND_COOLDOWN_SECONDS',
    default=60,
)

# Mailhog SMTP (slanje maila): port 1025
# Mailhog web sučelje (pregled mailova): http://localhost:8025
MAILHOG_SMTP_HOST = environment.str(
    'MAILHOG_SMTP_HOST',
    default=environment.str('EMAIL_HOST', default='mailhog'),
)
MAILHOG_SMTP_PORT = environment.int(
    'MAILHOG_SMTP_PORT',
    default=environment.int('EMAIL_PORT', default=1025),
)
if MAILHOG_SMTP_PORT == 8025:
    MAILHOG_SMTP_PORT = 1025

EMAIL_BACKEND = environment.str(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = MAILHOG_SMTP_HOST
EMAIL_PORT = MAILHOG_SMTP_PORT
EMAIL_USE_TLS = environment.bool('EMAIL_USE_TLS', default=False)
EMAIL_USE_SSL = environment.bool('EMAIL_USE_SSL', default=False)
EMAIL_TIMEOUT = environment.int('EMAIL_TIMEOUT', default=10)

REDIS_PASSWORD = environment.str('REDIS_PASSWORD', default='password')
REDIS_HOST = environment.str('REDIS_HOST', default='cache')
REDIS_PORT = environment.str('REDIS_PORT', default='6379')
CELERY_BROKER_URL = environment.str(
    'CELERY_BROKER_URL',
    default=f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0',
)
CELERY_RESULT_BACKEND = environment.str('CELERY_RESULT_BACKEND', default=CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_ALWAYS_EAGER = environment.bool('CELERY_TASK_ALWAYS_EAGER', default=False)
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

CACHES = {
    'default': environment.cache(
        'CACHE_URL',
        default='locmemcache://pastoral-default',
    ),
}
CACHES['default']['KEY_FUNCTION'] = 'django_tenants.cache.make_key'
CACHES['default']['REVERSE_KEY_FUNCTION'] = 'django_tenants.cache.reverse_key'

DATA_UPLOAD_MAX_NUMBER_FIELDS = None
DATA_UPLOAD_MAX_NUMBER_FILES = None
ADMIN_ACTION_CELERY_THRESHOLD = 10_000

X_FRAME_OPTIONS = 'SAMEORIGIN'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 8 * 60 * 60
SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_DOMAIN = None
CSRF_COOKIE_SAMESITE = 'Lax'

PARISH_DEFAULT_SLUG = 'bdm-slavonski-brod'
TENANCY_LEGACY_FALLBACK_ENABLED = False
LICENSE_ENFORCEMENT_ENABLED = False
