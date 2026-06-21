"""
============================================================================
SIBO ERP — Settings BASE (común a todos los entornos)
============================================================================
Aquí vive la configuración compartida. development.py y production.py heredan
de este archivo (`from .base import *`) y solo sobreescriben lo específico.

NÚCLEO DEL BLOQUE 0.2: configuración multitenant con django-tenants.
  - SHARED_APPS  -> viven en el schema `public` (plataforma comercial).
  - TENANT_APPS  -> se replican, un schema por tenant (negocio aislado).

Los secretos y la config por entorno se leen del archivo .env vía
python-decouple. NADA sensible va hardcodeado aquí.
----------------------------------------------------------------------------
"""
from pathlib import Path

from decouple import Csv, config

# ----------------------------------------------------------------------------
# Rutas base
# ----------------------------------------------------------------------------
# Este archivo: backend/config/settings/base.py
#   parent      -> settings/
#   parent.parent -> config/
#   parent.parent.parent -> backend/  (BASE_DIR)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ----------------------------------------------------------------------------
# Seguridad / entorno (desde .env)
# ----------------------------------------------------------------------------
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())

# ----------------------------------------------------------------------------
# Apps — distribución multitenant (ver §3.2 del Documento Fundacional)
# ----------------------------------------------------------------------------
# SHARED_APPS: schema `public`. El "cerebro" comercial de la plataforma.
#
# NOTA sobre el stack de admin en SHARED: auth/sessions/messages/admin se listan
# AQUÍ además de en TENANT_APPS (apps "dual-listadas", patrón estándar de
# django-tenants). Razón: el "Admin de plataforma" (§3.4 del Documento
# Fundacional) gestiona tenants/planes desde el admin de Django sobre el schema
# `public` (al que resuelve el dominio raíz/localhost). Para que ese admin
# funcione, sus tablas (auth_user, sesiones, etc.) deben existir en `public`.
# Cada tenant, además, tiene su PROPIO stack en su schema (ver TENANT_APPS).
SHARED_APPS = [
    "django_tenants",            # framework multitenant (debe ir primero)
    "apps.plataforma",           # Tenant, Dominio, Plan, Suscripcion, ModuloCatalogo
    # --- Django contrib (compartidas: habilitan el admin de PLATAFORMA en public) ---
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.admin",
    "django.contrib.staticfiles",
]

# TENANT_APPS: se materializan en CADA schema de tenant (datos aislados).
#
# NOTA (Bloque 0.2): solo se listan las apps que YA existen como código en este
# bloque (accounts, core) más las apps estándar de Django que el admin requiere.
# Las apps de negocio (clientes, ordenes, inventario, produccion, mantenimiento,
# portafolio, reportes, notificaciones) se IRÁN DESCOMENTANDO sprint por sprint,
# a medida que se creen. Si se dejaran activas ahora, Django no arrancaría
# (ImportError por módulo inexistente). Los DIFERIDOS (facturacion, asistente_ia)
# quedan comentados por decisión de alcance.
TENANT_APPS = [
    # --- Django estándar (requeridas por el admin) ---
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",   # requerida por django.contrib.admin
    "django.contrib.admin",
    # --- Apps SIBO ya existentes en este bloque ---
    "apps.accounts",             # RBAC: usuarios, roles, permisos (Bloque 0.4)
    "apps.core",                 # AuditLog, ModuloConfig, event bus (Bloque 0.4)
    # --- Apps de negocio (se descomentan en sprints siguientes) ---
    # "apps.clientes",
    # "apps.ordenes",
    # "apps.inventario",
    # "apps.produccion",
    # "apps.mantenimiento",
    # "apps.portafolio",
    # "apps.reportes",
    # "apps.notificaciones",
    # --- Diferidos (fuera del desarrollo actual, espacio reservado) ---
    # "apps.facturacion",        # Facturación DIAN (más allá de Fase II)
    # "apps.asistente_ia",       # Asistente IA (plan Full, post-estabilización)
]

# INSTALLED_APPS = SHARED_APPS + (TENANT_APPS no duplicadas), como en §3.2.
INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

# Modelos que django-tenants usa para resolver schema y dominio.
# (Los modelos Tenant/Dominio se definen en apps.plataforma — Bloque 0.3.)
TENANT_MODEL = "plataforma.Tenant"
TENANT_DOMAIN_MODEL = "plataforma.Dominio"

# ----------------------------------------------------------------------------
# Middleware — TenantMainMiddleware PRIMERO (ver §3.3)
# ----------------------------------------------------------------------------
# Debe resolver el tenant (por el Host header) antes que nada: branding,
# sesión y autenticación dependen de saber QUÉ tenant atiende la request.
MIDDLEWARE = [
    "django_tenants.middleware.main.TenantMainMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ----------------------------------------------------------------------------
# Templates
# ----------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ----------------------------------------------------------------------------
# Base de datos — backend de django-tenants (schema-per-tenant)
# ----------------------------------------------------------------------------
# ENGINE especial de django-tenants: gestiona el search_path por schema.
# HOST = "db" (nombre del servicio en docker-compose), no localhost.
DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": config("POSTGRES_DB"),
        "USER": config("POSTGRES_USER"),
        "PASSWORD": config("POSTGRES_PASSWORD"),
        "HOST": config("POSTGRES_HOST", default="db"),
        "PORT": config("POSTGRES_PORT", default="5432"),
    }
}

# Router que dirige cada modelo a su schema (shared -> public, tenant -> schema).
DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

# ----------------------------------------------------------------------------
# Cache — Redis (el contenedor redis ya está disponible)
# ----------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://redis:6379/0"),
    }
}

# ----------------------------------------------------------------------------
# Validadores de contraseña
# ----------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ----------------------------------------------------------------------------
# Internacionalización — Colombia
# ----------------------------------------------------------------------------
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# ----------------------------------------------------------------------------
# Archivos estáticos y media
# ----------------------------------------------------------------------------
# Coherente con nginx (0.1): sirve /static/ desde /app/staticfiles y
# /media/ desde /app/media (volúmenes compartidos web <-> nginx).
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Storage por defecto (Django 5.x usa el dict STORAGES).
#
# DECISIÓN (Bloque 0.2): por ahora MEDIA se guarda en disco local (volumen
# media_volume). El backend MinIO (django-minio-storage) se DIFIERE a un bloque
# posterior, cuando existan modelos con FileField/ImageField y se implemente el
# aislamiento por tenant (prefijo <schema_name>/). Justificación: en 0.2 no hay
# uploads que ejercitar, y atar el storage a un servicio externo ahora solo
# añadiría una dependencia de arranque sin beneficio. El contenedor minio sigue
# levantado y listo; solo no está cableado todavía como storage de Django.
#
# Para activarlo más adelante, reemplazar "default" por:
#   "default": {"BACKEND": "minio_storage.storage.MinioMediaStorage"},
# y añadir las MINIO_STORAGE_* leyendo de .env.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ----------------------------------------------------------------------------
# Otros
# ----------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
