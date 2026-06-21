from django.apps import AppConfig


class CoreConfig(AppConfig):
    """TENANT_APP: núcleo por tenant (AuditLog, ModuloConfig, event bus).
    Una copia por schema. Modelos: Bloque 0.4."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"
