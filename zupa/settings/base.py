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
    'django_celery_beat',
    'pastoral',
    'pregled.apps.PregledConfig',
    'zupa_vjernici.apps.ZupaVjerniciConfig',
    'liturgija.apps.LiturgijaConfig',
    'sakramenti.apps.SakramentiConfig',
    'financije.apps.FinancijeConfig',
    'isprave.apps.IspraveConfig',
    'ured.apps.UredConfig',
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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
        'NAME': environment.str('DB_NAME', default=None),
        'USER': environment.str('DB_USER', default=None),
        'PASSWORD': environment.str('DB_PASS', default=None),
        'HOST': environment.str('DB_HOST', default='db'),
        'PORT': environment.str('DB_PORT', default='5432'),
    }
}


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


AUTH_USER_MODEL = "pastoral.User"

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

CACHES = {
    'default': environment.cache(
        'CACHE_URL',
        default='locmemcache://pastoral-default',
    ),
}

X_FRAME_OPTIONS = 'SAMEORIGIN'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 8 * 60 * 60

PARISH_DEFAULT_SLUG = 'bdm-slavonski-brod'
TENANCY_LEGACY_FALLBACK_ENABLED = False
LICENSE_ENFORCEMENT_ENABLED = False
# Funkcionalnosti s višom fazom ostaju u kodu i podacima, ali nisu dostupne u
# redovnom radu dok se planski ne aktivira sljedeća faza proizvoda.
PASTORAL_PRODUCT_PHASE = environment.int('PASTORAL_PRODUCT_PHASE', default=1)

if PASTORAL_PRODUCT_PHASE >= 2:
    phase_two_templates = BASE_DIR / 'phase_two' / 'templates'
    phase_two_static = BASE_DIR / 'phase_two' / 'static'
    if phase_two_templates.is_dir():
        TEMPLATES[0]['DIRS'].append(phase_two_templates)
    if phase_two_static.is_dir():
        STATICFILES_DIRS.append(phase_two_static)

# Romcal se najprije može testirati usporednim API-jem. Postojeći LitCal ostaje
# oba izvora rade paralelno; vrijednosti litcal i romcal ostaju za dijagnostiku.
LITURGICAL_PRIMARY_PROVIDER = environment.str(
    'LITURGICAL_PRIMARY_PROVIDER',
    default='hybrid',
).strip().lower()
LITURGICAL_ROMCAL_ENABLED = environment.bool('LITURGICAL_ROMCAL_ENABLED', default=True)
