"""
SIBO ERP — Admin de plataforma (schema `public`).

Este es el panel del "Admin de plataforma" (§3.4 y §4): alta de tenants,
asignación de planes y gestión MANUAL de suscripciones (estados, fechas, notas).
"""
from django.contrib import admin

from .models import Dominio, ModuloCatalogo, Plan, Suscripcion, Tenant


class DominioInline(admin.TabularInline):
    model = Dominio
    extra = 1


@admin.register(ModuloCatalogo)
class ModuloCatalogoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre")
    search_fields = ("codigo", "nombre")
    ordering = ("codigo",)


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "usuarios_incluidos", "precio_mensual_cop")
    search_fields = ("codigo", "nombre")
    filter_horizontal = ("modulos_incluidos",)
    ordering = ("precio_mensual_cop",)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("schema_name", "nombre", "nit", "plan", "activo", "creado_en")
    list_filter = ("activo", "plan")
    search_fields = ("schema_name", "nombre", "nit")
    readonly_fields = ("creado_en",)
    inlines = [DominioInline]


@admin.register(Dominio)
class DominioAdmin(admin.ModelAdmin):
    list_display = ("domain", "tenant", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("domain",)


@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = (
        "tenant",
        "plan",
        "estado",
        "fecha_inicio",
        "fecha_proximo_pago",
        "usuarios_adicionales",
    )
    list_filter = ("estado", "plan")
    search_fields = ("tenant__nombre", "tenant__schema_name")
    autocomplete_fields = ()  # se podrá afinar cuando crezca el nº de tenants
