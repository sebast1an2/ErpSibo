from django.apps import AppConfig


class PlataformaConfig(AppConfig):
    """SHARED_APP: plataforma comercial (Tenant, Dominio, Plan, Suscripcion,
    ModuloCatalogo). Vive en el schema `public`. Modelos: Bloque 0.3."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.plataforma"
    verbose_name = "Plataforma"
