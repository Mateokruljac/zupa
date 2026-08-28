"""
ASGI config for the zupa project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import sys

sys.dont_write_bytecode = True

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zupa.settings.local')

application = get_asgi_application()
