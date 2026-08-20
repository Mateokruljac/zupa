from .base import *

DEBUG = environment.bool('DEBUG', default=False)
IS_PRODUCTION = True
TENANCY_LEGACY_FALLBACK_ENABLED = False
ALLOWED_HOSTS = ['*']

STATIC_ROOT = BASE_DIR / 'static'
MEDIA_URL = '/static/media/'

print("************************************************************")
print("NOTE: Running in production environment.")
print("************************************************************")

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = environment.str('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = environment.str('EMAIL_HOST_PASSWORD', default='')

