"""
SIBO ERP — Comando: seed_planes

Crea (IDEMPOTENTE) los datos comerciales base de plataforma:
  - El catálogo de módulos del sistema (ModuloCatalogo).
  - Los planes del alcance actual: 'esencial' y 'profesional'
    (+ 'full' como placeholder de registro futuro, SIN módulos de IA).

Reglas de alcance:
  - Gestión MANUAL: no hay pasarela. Precios son PLACEHOLDER editables en el
    admin (los valores COP definitivos son una decisión abierta, doc §7).
  - El plan 'full' solo se diferencia por el Asistente IA, que está DIFERIDO;
    por eso hoy incluye los mismos módulos que 'profesional' (sin IA).

Uso:
    docker compose exec web python manage.py seed_planes
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.plataforma.models import ModuloCatalogo, Plan

# Catálogo de módulos del sistema. `codigo` matchea los módulos del resto del
# sistema (y a futuro las filas ModuloConfig de cada tenant, Bloque 0.4).
MODULOS = [
    ("clientes", "Clientes"),
    ("ordenes", "Órdenes de Trabajo"),
    ("inventario", "Inventario"),
    ("produccion", "Producción"),
    ("mantenimiento", "Mantenimiento"),
    ("portafolio", "Portafolio público"),
    ("reportes", "Reportes y Dashboards"),
    ("notificaciones", "Notificaciones"),
]

# Mapeo plan -> módulos incluidos (decidido con el dev en 0.3).
#   esencial    = núcleo operativo.
#   profesional = esencial + el resto (incluye produccion y mantenimiento).
#   full        = placeholder; mismos módulos que profesional (su único
#                 diferencial, el Asistente IA, está diferido).
ESENCIAL = ["clientes", "ordenes", "inventario"]
PROFESIONAL = ESENCIAL + [
    "produccion",
    "mantenimiento",
    "notificaciones",
    "reportes",
    "portafolio",
]
FULL = list(PROFESIONAL)  # diferencial IA pendiente (Bloque diferido)

# Definición de planes. precio_mensual_cop = PLACEHOLDER (editar en admin).
PLANES = [
    {
        "codigo": "esencial",
        "nombre": "Esencial",
        "usuarios_incluidos": 3,
        "precio_mensual_cop": Decimal("0.00"),  # TBD (doc §7)
        "modulos": ESENCIAL,
    },
    {
        "codigo": "profesional",
        "nombre": "Profesional",
        "usuarios_incluidos": 6,
        "precio_mensual_cop": Decimal("0.00"),  # TBD (doc §7)
        "modulos": PROFESIONAL,
    },
    {
        "codigo": "full",
        "nombre": "Full (placeholder)",
        "usuarios_incluidos": 12,
        "precio_mensual_cop": Decimal("0.00"),  # TBD (doc §7)
        "modulos": FULL,
    },
]


class Command(BaseCommand):
    help = "Crea/actualiza (idempotente) el catálogo de módulos y los planes base."

    @transaction.atomic
    def handle(self, *args, **options):
        # 1) Catálogo de módulos.
        modulos_por_codigo = {}
        for codigo, nombre in MODULOS:
            modulo, created = ModuloCatalogo.objects.update_or_create(
                codigo=codigo,
                defaults={"nombre": nombre},
            )
            modulos_por_codigo[codigo] = modulo
            self.stdout.write(
                ("  + " if created else "  = ") + f"módulo {codigo}"
            )

        # 2) Planes. NO se pisa el precio si el plan ya existe (puede haber sido
        #    editado a mano en el admin); solo se fija al crearlo.
        for definicion in PLANES:
            plan, created = Plan.objects.get_or_create(
                codigo=definicion["codigo"],
                defaults={
                    "nombre": definicion["nombre"],
                    "usuarios_incluidos": definicion["usuarios_incluidos"],
                    "precio_mensual_cop": definicion["precio_mensual_cop"],
                },
            )
            if not created:
                # Refrescar nombre/usuarios (datos estructurales), NO el precio.
                plan.nombre = definicion["nombre"]
                plan.usuarios_incluidos = definicion["usuarios_incluidos"]
                plan.save(update_fields=["nombre", "usuarios_incluidos"])

            # Asignación de módulos (idempotente con .set()).
            plan.modulos_incluidos.set(
                [modulos_por_codigo[c] for c in definicion["modulos"]]
            )
            self.stdout.write(
                ("  + " if created else "  = ")
                + f"plan {plan.codigo} ({plan.modulos_incluidos.count()} módulos)"
            )

        self.stdout.write(self.style.SUCCESS("Seed de planes/módulos completado."))
