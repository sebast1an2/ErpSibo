"""
SIBO ERP — ASGI entrypoint.
Reservado para funcionalidad asíncrona futura (WebSockets: Kanban en tiempo
real). Hoy no se usa, pero queda creado. Por defecto, settings de desarrollo.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

application = get_asgi_application()
