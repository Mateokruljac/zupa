import os
from pathlib import Path

from .admin_sidebar import ADMIN_REORDER

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-dev-only-change-in-production',
)

DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'pastoral',
    'users',
    'control_plane.apps.ControlPlaneConfig',
    'public_site.apps.PublicSiteConfig',
    'debug_toolbar',
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'control_plane.middleware.TenantContextMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'zupa.urls'

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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASS'),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'hr'
TIME_ZONE = 'Europe/Zagreb'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'static' / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


AUTH_USER_MODEL = "users.User"

LOGIN_URL = 'pastoral:login'
LOGOUT_REDIRECT_URL = 'pastoral:login'

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@pastoral.local')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
OTP_RECIPIENT = os.environ.get('OTP_RECIPIENT', 'mateokruljac123@gmail.com')
OTP_TTL_MINUTES = int(os.environ.get('OTP_TTL_MINUTES', '10'))

# Mailhog SMTP (slanje maila): port 1025
# Mailhog web sučelje (pregled mailova): http://localhost:8025
MAILHOG_SMTP_HOST = os.environ.get('MAILHOG_SMTP_HOST', os.environ.get('EMAIL_HOST', 'mailhog'))
MAILHOG_SMTP_PORT = int(os.environ.get('MAILHOG_SMTP_PORT', os.environ.get('EMAIL_PORT', '1025')))
if MAILHOG_SMTP_PORT == 8025:
    MAILHOG_SMTP_PORT = 1025

EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = MAILHOG_SMTP_HOST
EMAIL_PORT = MAILHOG_SMTP_PORT
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'False') == 'True'
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False') == 'True'
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', '10'))

CELERY_BROKER_URL = os.environ.get(
    'CELERY_BROKER_URL',
    f"redis://:{os.environ.get('REDIS_PASSWORD', 'password')}@{os.environ.get('REDIS_HOST', 'cache')}:{os.environ.get('REDIS_PORT', '6379')}/0",
)
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_ALWAYS_EAGER = os.environ.get('CELERY_TASK_ALWAYS_EAGER', 'False') == 'True'

X_FRAME_OPTIONS = 'SAMEORIGIN'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 8 * 60 * 60

PARISH_DEFAULT_SLUG = 'bdm-slavonski-brod'
TENANCY_LEGACY_FALLBACK_ENABLED = False
LICENSE_ENFORCEMENT_ENABLED = False
PUBLIC_WEBSITE_DEMO_AUTO_ACTIVATE = False

# Romcal se najprije može testirati usporednim API-jem. Postojeći LitCal ostaje
# oba izvora rade paralelno; vrijednosti litcal i romcal ostaju za dijagnostiku.
LITURGICAL_PRIMARY_PROVIDER = os.environ.get(
    'LITURGICAL_PRIMARY_PROVIDER',
    'hybrid',
).strip().lower()
LITURGICAL_ROMCAL_ENABLED = os.environ.get('LITURGICAL_ROMCAL_ENABLED', 'True') == 'True'
