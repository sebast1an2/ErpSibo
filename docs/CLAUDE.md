# CLAUDE.md — Contexto del Proyecto para Claude Code

## Qué es este proyecto

ERP web modular para una empresa colombiana de **troquelería y corte láser**. Gestiona el ciclo completo: clientes → órdenes de trabajo (OT) → producción → inventario → notificaciones WhatsApp → entrega. Incluye vista pública (portafolio + seguimiento de OT por token).

**Documentos fuente (LEER ANTES DE GENERAR CÓDIGO):**
- `docs/especificacion_v4.md` → Especificación completa: modelos, permisos, flujos, fórmulas. **Es la fuente de verdad.**
- `docs/plan_desarrollo_v1.md` → Plan por sprints y bloques de tareas
- `docs/CHANGELOG_DECISIONES.md` → Decisiones que difieren de la especificación
- `docs/estado_proyecto.md` → Qué está hecho y qué sigue

## Stack (NO cambiar sin autorización explícita)

- Python 3.11+ · Django 5.x · PostgreSQL 16 · Django ORM (nunca SQL raw sin parámetros)
- Django REST Framework (APIs internas) · Django Channels + Redis (tiempo real)
- Celery + Redis (tareas async) · Celery Beat (programadas)
- Frontend: Django Templates + **HTMX + Alpine.js** (NO React, NO Vue) · Tailwind CSS (build local, NO CDN)
- Archivos: MinIO (S3-compatible) vía django-storages
- Docker Compose: nginx, web, db, redis, celery_worker, celery_beat, minio
- Config: python-decouple + `.env` (NUNCA valores hardcoded)

## Arquitectura

```
backend/
├── config/            # settings/ (base, development, production), urls, asgi, celery
├── core/              # AuditLog, ModuloConfig, EventLog, middleware, permissions RBAC, signals (event bus)
├── apps/
│   ├── accounts/      # Usuario(AbstractUser), Rol, Permiso — RBAC propio
│   ├── clientes/
│   ├── ordenes/       # MÓDULO CENTRAL — OTs, estados, costos, token seguimiento
│   ├── inventario/
│   ├── produccion/
│   ├── mantenimiento/
│   ├── portafolio/    # incluye vista pública
│   ├── reportes/
│   ├── facturacion/   # Fase I: SOLO UI maquetada, sin lógica
│   ├── notificaciones/
│   └── asistente_ia/  # desactivado por defecto
└── templates/         # base.html (interna), base_public.html (pública), components/
```

Cada app sigue la misma estructura: `models.py, views.py, urls.py, forms.py, serializers.py, permissions.py, admin.py, services/, tests/`

## Reglas de oro (OBLIGATORIAS)

1. **RBAC propio, no el de Django.** Usamos modelos `Rol` y `Permiso` propios. Toda vista nueva DEBE:
   - Tener su permiso atómico con formato `<modulo>.<accion>_<recurso>` (ej: `ordenes.crear_ot`)
   - Registrar el permiso en una data migration del módulo
   - Protegerse con el decorador `@permiso_requerido("codigo")` o mixin `PermisoRequeridoMixin`
2. **Lógica de negocio en `services/`,** nunca en views ni models. Views delgadas.
3. **Eventos, no acoplamiento:** la comunicación entre módulos va por el event bus (`core/signals.py` → `emitir_evento("ot.estado_cambiado", payload)`). Si nadie consume el evento, se guarda en `EventLog`.
4. **Módulos activables:** antes de ejecutar lógica de un módulo secundario (WhatsApp, IA), verificar `ModuloConfig.esta_activo("nombre")`.
5. **Tests obligatorios:** pytest-django, cobertura ≥ 70% en accounts, ordenes, inventario. No cerrar bloque con tests rotos.
6. **Auditoría:** acciones de escritura quedan en `AuditLog` (lo maneja el middleware — no duplicar).
7. **Seguridad:** CSRF en todo form (HTMX incluido via header), cookies HttpOnly+Secure, validación MIME en uploads, nunca exponer costos en vistas públicas.
8. **No modificar módulos ya terminados** salvo que el prompt lo pida explícitamente.
9. **No agregar dependencias** a requirements.txt sin justificarlo en el resultado.

## Estándares de código

- PEP 8 estricto (ruff + black) · Type hints obligatorios · Docstrings Google-style
- Nombres de modelos/campos en **español** (dominio del negocio): `OrdenTrabajo`, `costo_final`
- Código de infraestructura/comentarios técnicos en español
- Commits: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`)
- Ramas: `main`, `develop`, `feature/<nombre>`, `fix/<nombre>`

## Comandos

```bash
make run        # docker compose up
make migrate    # makemigrations + migrate
make shell      # shell_plus dentro del contenedor
make test       # pytest
make logs       # logs del servicio web
```

## Convenciones de dominio importantes

- Número de OT: `OT-<año>-<secuencial de 4 dígitos>` (ej: `OT-2026-0001`), generación atómica
- Estados de OT: NUEVA → COTIZADA → APROBADA → EN_COLA → EN_PROCESO → CONTROL_CALIDAD → LISTA → ENTREGADA (+ PAUSADA, CANCELADA, RECHAZADA). Las transiciones válidas están en la sección 4.3.2 de la especificación.
- Token de seguimiento público: UUID, se desactiva al pasar a ENTREGADA
- Moneda: COP, sin decimales en presentación
- Fórmulas de costos: sección 4.3.4 de la especificación — implementadas en `ordenes/services/costos.py`

## Al terminar cada tarea

1. Listar archivos creados/modificados
2. Indicar comandos de verificación (migrate, test, URL a probar)
3. Si tomaste una decisión no contemplada en la spec, anotarla para `docs/CHANGELOG_DECISIONES.md`
