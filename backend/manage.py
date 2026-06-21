#!/usr/bin/env python
"""
SIBO ERP — Punto de entrada de comandos de Django (manage.py).
Se ejecuta dentro del contenedor "web", p.ej.:
    docker compose exec web python manage.py <comando>

Por defecto usa los settings de DESARROLLO. En producción se sobreescribe
exportando DJANGO_SETTINGS_MODULE=config.settings.production.
"""
import os
import sys


def main():
    # Settings por defecto: desarrollo. Override vía variable de entorno.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. ¿Está instalado y el entorno virtual "
            "activo? (En este proyecto Django vive dentro del contenedor 'web'.)"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
