"""
SIBO ERP — Modelos de plataforma (schema `public`).

ALCANCE (Bloque 0.2 — bootstrap mínimo):
Solo se definen los modelos que django-tenants EXIGE para arrancar y resolver
schema/dominio: Tenant y Dominio. Se incluye un campo `nombre` y la fecha de
creación, nada más.

El modelo comercial completo (Plan, Suscripcion, ModuloCatalogo, NIT, FK a plan,
flag `activo`, etc.) se implementa en el Bloque 0.3 — NO va aquí todavía.
"""
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin


class Tenant(TenantMixin):
    """Una empresa cliente = un schema PostgreSQL aislado.

    TenantMixin aporta `schema_name` y la maquinaria de creación de schema.
    """

    nombre = models.CharField(max_length=120)
    creado_en = models.DateTimeField(auto_now_add=True)

    # Al guardar un Tenant nuevo, django-tenants crea su schema y corre
    # migrate_schemas automáticamente. (Para el schema `public` no crea nada:
    # ya existe.)
    auto_create_schema = True
    # Nunca borrar un schema automáticamente: solo se desactiva (ver doc §3.2).
    auto_drop_schema = False

    def __str__(self):
        return f"{self.nombre} ({self.schema_name})"


class Dominio(DomainMixin):
    """Subdominio que enruta a un tenant (cliente1.localhost, ...).

    DomainMixin aporta `domain`, FK a tenant e `is_primary`.
    """

    def __str__(self):
        return self.domain
