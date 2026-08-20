from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent
environment = environ.Env()
environment.read_env(BASE_DIR / '.env')

SECRET_KEY = environment.str(
    'WEBSITE_SECRET_KEY',
    default='django-insecure-website-development-only',
)
DEBUG = environment.bool('WEBSITE_DEBUG', default=False)
ALLOWED_HOSTS = environment.list(
    'WEBSITE_ALLOWED_HOSTS',
    default=['localhost', '127.0.0.1'],
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'public_site.apps.PublicSiteConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'website_config.urls'
WSGI_APPLICATION = 'website_config.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

website_database_host = environment.str('WEBSITE_DB_HOST', default='')
if website_database_host:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': environment.str('WEBSITE_DB_NAME', default='parish_website'),
            'USER': environment.str('WEBSITE_DB_USER', default='parish_website'),
            'PASSWORD': environment.str('WEBSITE_DB_PASSWORD', default=''),
            'HOST': website_database_host,
            'PORT': environment.str('WEBSITE_DB_PORT', default='5432'),
        },
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'website.sqlite3',
        },
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
]

LANGUAGE_CODE = 'hr'
TIME_ZONE = 'Europe/Zagreb'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
MIGRATION_MODULES = {'public_site': 'standalone_migrations.public_site'}

SESSION_COOKIE_NAME = 'parish_website_session'
CSRF_COOKIE_NAME = 'parish_website_csrf'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = environment.bool('WEBSITE_SECURE_SSL_REDIRECT', default=True)
    SECURE_HSTS_SECONDS = environment.int('WEBSITE_HSTS_SECONDS', default=31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
