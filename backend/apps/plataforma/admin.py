"""
SIBO ERP — Admin de plataforma (schema `public`).

Registro mínimo (Bloque 0.2) para que el "Admin de plataforma" pueda ver/crear
Tenants y Dominios desde el admin de Django. La configuración rica (inlines,
Plan/Suscripcion, sincronización de módulos) llega en el Bloque 0.3.
"""
from django.contrib import admin

from .models import Dominio, Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("schema_name", "nombre", "creado_en")
    search_fields = ("schema_name", "nombre")
    readonly_fields = ("creado_en",)


@admin.register(Dominio)
class DominioAdmin(admin.ModelAdmin):
    list_display = ("domain", "tenant", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("domain",)
