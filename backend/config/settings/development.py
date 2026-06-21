"""
SIBO ERP — Settings de DESARROLLO.
Hereda de base.py y relaja lo necesario para trabajar en local.
"""
from .base import *  # noqa: F401,F403

DEBUG = True

# Permisivo para el desarrollo multitenant local: el dominio raíz y CUALQUIER
# subdominio *.localhost (cliente1.localhost, cliente2.localhost, ...).
ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".localhost"]
