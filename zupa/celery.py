import os
import sys

sys.dont_write_bytecode = True

from celery import Celery

# set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zupa.settings.local')


app = Celery('zupa')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
