from .base import *

DEBUG = os.environ.get("DEBUG", False)
IS_PRODUCTION = True
CORS_ORIGIN_ALLOW_ALL = True
ALLOWED_HOSTS = ['*']

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_URL = '/static/media/'

BACKEND_URL = os.environ.get("BACKEND_URL")
FRONTEND_URL = os.environ.get("FRONTEND_URL")

print("************************************************************")
print("NOTE: Running in production environment.")
print("************************************************************")

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

