"""
SIBO ERP — Servicios de plataforma (lógica síncrona, sin Celery).

`sincronizar_modulos` refleja los módulos del Plan del tenant en las filas
ModuloConfig de su schema (§3.2 del Documento Fundacional).

ESTADO (Bloque 0.3): la lógica está COMPLETA, pero `ModuloConfig` vive en
apps.core, que todavía NO existe (Bloque 0.4). Por eso el import de ModuloConfig
es DIFERIDO (dentro de la función) y, si core aún no está disponible, la función
falla de forma controlada con un mensaje claro. En cuanto exista
apps.core.models.ModuloConfig, esta función funcionará sin cambios.
"""
from django_tenants.utils import schema_context

from .models import Tenant


def sincronizar_modulos(tenant_id: int) -> None:
    """Activa en el schema del tenant los módulos incluidos en su Plan.

    Un downgrade que quita un módulo NO borra datos: solo pone activo=False
    (principio de módulos activables, §4). Si el tenant no tiene plan asignado
    (p.ej. el tenant `public`), se desactivan todos los módulos.
    """
    tenant = Tenant.objects.get(id=tenant_id)

    if tenant.plan_id is None:
        codigos_activos: set[str] = set()
    else:
        codigos_activos = set(
            tenant.plan.modulos_incluidos.values_list("codigo", flat=True)
        )

    # Import DIFERIDO: apps.core.ModuloConfig se crea en el Bloque 0.4.
    try:
        from apps.core.models import ModuloConfig
    except (ImportError, LookupError) as exc:
        raise NotImplementedError(
            "sincronizar_modulos requiere apps.core.ModuloConfig (Bloque 0.4). "
            "La lógica ya está implementada; se activará cuando exista apps.core."
        ) from exc

    with schema_context(tenant.schema_name):
        ModuloConfig.objects.update(activo=False)
        ModuloConfig.objects.filter(codigo__in=codigos_activos).update(activo=True)
