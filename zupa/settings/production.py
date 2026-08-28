from .base import *

DEBUG = environment.bool('DEBUG', default=False)
IS_PRODUCTION = True
TENANCY_LEGACY_FALLBACK_ENABLED = False
SECRET_KEY = environment.str('SECRET_KEY')
ALLOWED_HOSTS = environment.list('ALLOWED_HOSTS')
CSRF_TRUSTED_ORIGINS = environment.list(
    'CSRF_TRUSTED_ORIGINS',
    default=[],
)

STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/static/media/'

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = environment.bool('SECURE_SSL_REDIRECT', default=True)
SECURE_HSTS_SECONDS = environment.int('SECURE_HSTS_SECONDS', default=31_536_000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = environment.str('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = environment.str('EMAIL_HOST_PASSWORD', default='')
