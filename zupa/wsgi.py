"""
WSGI config for the zupa project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys

sys.dont_write_bytecode = True

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zupa.settings.local')

application = get_wsgi_application()
