"""
SIBO ERP — Settings de PRODUCCIÓN.
Hereda de base.py. DEBUG apagado + hardening básico de seguridad.
(No exhaustivo: es la base; se endurece más al desplegar de verdad.)

Arranque en producción: Gunicorn con estos settings, p.ej.
    DJANGO_SETTINGS_MODULE=config.settings.production \
        gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
"""
from .base import *  # noqa: F401,F403

DEBUG = False

# Hosts reales se definen por entorno (.env de producción).
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())  # noqa: F405

# --- Hardening básico ---
# La terminación TLS la hace nginx; Django confía en el header del proxy.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)  # noqa: F405

# Cookies solo por HTTPS y no accesibles desde JS.
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# Cabeceras de seguridad.
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"
