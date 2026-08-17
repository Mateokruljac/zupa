from .base import *

DEBUG = os.environ.get("DEBUG", False)
IS_PRODUCTION = True
TENANCY_LEGACY_FALLBACK_ENABLED = False
ALLOWED_HOSTS = ['*']

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_URL = '/static/media/'

print("************************************************************")
print("NOTE: Running in production environment.")
print("************************************************************")

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

