"""
Celery application config for async PDF generation.
"""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'igl_project.settings')
app = Celery('igl_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
