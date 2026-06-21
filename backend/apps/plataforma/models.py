"""
SIBO ERP — Modelos de plataforma (schema `public`).

ALCANCE:
- Bloque 0.2 (bootstrap mínimo): Tenant + Dominio con los campos que
  django-tenants exige (`nombre`, `creado_en`).
- Bloque 0.3 (este): se EXTIENDE Tenant (nit, plan, activo) y se añade el
  modelo comercial: ModuloCatalogo, Plan, Suscripcion. Ver §3.2 y §4 del
  Documento Fundacional.

Gestión 100% MANUAL: ni Plan ni Suscripcion tienen campos de pasarela de pago
ni de cobro automático. El "Admin de plataforma" administra todo a mano desde
el admin de Django.
"""
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin


class ModuloCatalogo(models.Model):
    """Catálogo de módulos del sistema (vive en `public`).

    `codigo` matchea el código del módulo en el resto del sistema
    (p.ej. "inventario", "ordenes") y, a futuro, las filas ModuloConfig de
    cada tenant (apps.core, Bloque 0.4).
    """

    codigo = models.CharField(max_length=40, unique=True)
    nombre = models.CharField(max_length=80)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Módulo (catálogo)"
        verbose_name_plural = "Módulos (catálogo)"
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} — {self.nombre}"


class Plan(models.Model):
    """Plan comercial. Alcance actual: 'esencial' y 'profesional'.

    'full' puede existir como placeholder, pero sus módulos diferenciales (IA)
    NO se implementan en esta etapa.
    """

    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=40)
    usuarios_incluidos = models.PositiveIntegerField()
    precio_mensual_cop = models.DecimalField(max_digits=10, decimal_places=2)
    modulos_incluidos = models.ManyToManyField(
        ModuloCatalogo, related_name="planes", blank=True
    )

    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Planes"
        ordering = ["precio_mensual_cop"]

    def __str__(self):
        return self.nombre


class Tenant(TenantMixin):
    """Una empresa cliente = un schema PostgreSQL aislado.

    TenantMixin aporta `schema_name` y la maquinaria de creación de schema.
    """

    # --- Campos del bootstrap (Bloque 0.2) — NO se modifican ---
    nombre = models.CharField(max_length=120)
    creado_en = models.DateTimeField(auto_now_add=True)

    # --- Campos comerciales añadidos en el Bloque 0.3 ---
    # NIT del cliente. blank/default="" para no romper el tenant `public`
    # existente (que no tiene NIT) ni exigirlo en la migración.
    nit = models.CharField(max_length=20, blank=True, default="")
    # Plan asignado. null/blank=True: (1) el tenant `public` es el schema de
    # plataforma, no un cliente, y queda SIN plan; (2) el alta manual (§3.4)
    # crea el Tenant y luego asigna plan; (3) evita dejar huérfano al public
    # existente en la migración. PROTECT: no se borra un Plan en uso.
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tenants",
    )
    activo = models.BooleanField(default=True)

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


class Suscripcion(models.Model):
    """Suscripción de un tenant a un plan. Gestión MANUAL.

    Sin pasarela ni webhooks: `fecha_proximo_pago` es informativa y `notas`
    sirve para registrar pagos/observaciones a mano (§4 del documento).
    """

    ESTADOS = [
        ("activa", "Activa"),
        ("mora", "En mora"),
        ("suspendida", "Suspendida"),
        ("cancelada", "Cancelada"),
    ]

    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name="suscripcion"
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="suscripciones")
    usuarios_adicionales = models.PositiveIntegerField(default=0)
    fecha_inicio = models.DateField()
    fecha_proximo_pago = models.DateField()  # informativa; se administra a mano
    estado = models.CharField(max_length=12, choices=ESTADOS, default="activa")
    notas = models.TextField(blank=True)  # registro manual de pagos/observaciones

    class Meta:
        verbose_name = "Suscripción"
        verbose_name_plural = "Suscripciones"

    def __str__(self):
        return f"{self.tenant.nombre} — {self.plan.nombre} ({self.estado})"
