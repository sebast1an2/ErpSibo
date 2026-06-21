"""
SIBO ERP — WSGI entrypoint.
Lo usa Gunicorn (producción) y el runserver de desarrollo para "hablar" HTTP
síncrono con Django. Por defecto, settings de desarrollo.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

application = get_wsgi_application()
