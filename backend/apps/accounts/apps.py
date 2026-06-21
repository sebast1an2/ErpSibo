from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """TENANT_APP: RBAC (usuarios, roles, permisos). Una copia por schema.
    Modelos: Bloque 0.4."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Accounts"
