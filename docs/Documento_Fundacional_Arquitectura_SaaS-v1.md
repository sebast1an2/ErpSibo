# Documento Fundacional de Arquitectura — SIBO ERP (SaaS Multitenant)
## Troquelería y Corte Láser · v1 — Decisiones Core Pre-Sprint 0

> **Producto:** SIBO ERP
> **Estado:** Aprobado para inicio de desarrollo. Estas decisiones afectan el modelo de datos base y son costosas de revertir una vez iniciado el desarrollo.
> **Reemplaza/extiende:** el supuesto single-tenant de `Estructura_aplicativo.md` (v4). Los modelos funcionales descritos ahí (OTs, Inventario, Mantenimiento, Portafolio, etc.) se mantienen; lo que cambia es **dónde viven** (schema compartido vs. schema por tenant) y **cómo se activan** según plan.

---

## 0. Alcance del desarrollo actual

> ⚠️ **Importante — qué se construye ahora y qué no.**

El desarrollo actual cubre los planes **Esencial** y **Profesional**. El plan **Full/Empresarial queda diferido**: se aborda solo cuando SIBO ERP tenga sus primeras versiones funcionando, esté estabilizado y probado en uso real.

**En alcance ahora (Esencial + Profesional):**
- Multitenancy (schema-per-tenant) y resolución por subdominio.
- Gestión de planes y suscripciones **de forma 100% manual** (un Admin de plataforma asigna plan, fechas y estado a mano — sin pasarelas, sin webhooks, sin cobro automático).
- Módulos de negocio: Clientes, Órdenes de Trabajo, Inventario, Producción, Mantenimiento, Portafolio público, Reportes/Dashboards, Notificaciones (WhatsApp + interno + email).
- RBAC, auditoría, branding por tenant, estado de cuenta (informativo).

**Diferido — fuera del desarrollo actual (plan Full, futuro post-estabilización):**
- **Asistente IA** (LLM por tenant). No se implementa ahora. La arquitectura de módulos activables deja el espacio listo (módulo desactivado, sin servicio backend corriendo).
- **Facturación electrónica DIAN.** Va más allá de Fase II. No se implementa ahora; a lo sumo se podrá maquetar UI sin lógica de negocio, respetando el principio de módulos activables.

El modelo de datos se diseña de modo que estos dos módulos puedan **añadirse después sin reescribir el core** — esa es la única exigencia que imponen sobre el desarrollo actual.

---

## 1. Resumen ejecutivo de decisiones

| Decisión | Resolución |
|---|---|
| Nombre del producto | **SIBO ERP** |
| Modelo de negocio | SaaS multi-empresa (multitenant), no instalación dedicada por cliente |
| Patrón de aislamiento | **Schema-per-tenant** sobre PostgreSQL, vía `django-tenants` |
| Routing | Subdominio por tenant (`cliente.dominio.com`) → resolución automática de schema |
| Activación de módulos | Catálogo de módulos en schema público + flag de activación por tenant (`ModuloConfig`), derivado del plan asignado |
| Gestión de planes y pagos | **Manual** — Admin de plataforma administra plan, fechas y estado. Sin pasarela ni cobro automático en esta etapa |
| Asistente IA | **Diferido** (plan Full, post-estabilización). Espacio reservado vía módulos activables |
| Facturación DIAN | **Diferido** (más allá de Fase II). Espacio reservado vía módulos activables |

---

## 2. Alcance y posicionamiento

SIBO ERP nace para el vertical de **troquelería y corte láser** (modelos funcionales ya definidos en v3/v4), pero se construye desde el día uno como **SaaS multi-tenant**: cada empresa cliente (tenant) es una instancia lógica aislada dentro de la misma infraestructura, accesible por su propio subdominio.

No se generaliza el dominio de negocio a otros sectores (RRHH, contabilidad, etc. — fuera de alcance). Lo que se generaliza es la **capa de plataforma**: alta de tenants, planes y módulos activables. El modelo de datos de negocio (OTs, Inventario, Mantenimiento) permanece específico del vertical, replicado por tenant.

---

## 3. Arquitectura Multitenant

### 3.1 Patrón elegido: schema-per-tenant

**Decisión:** `django-tenants` (mantenimiento activo, sucesor de `django-tenant-schemas`) sobre un único clúster PostgreSQL.

Justificación frente a las alternativas:

| Criterio | Schema-per-tenant | Row-level (`tenant_id`) | DB-per-tenant |
|---|---|---|---|
| Aislamiento de datos | Alto — a nivel de motor de BD | Medio — depende de manager/middleware en cada query | Máximo |
| Mapeo a subdominio | Directo (1 schema = 1 subdominio) | Requiere filtro manual en cada request | Directo |
| Riesgo de fuga entre tenants | Bajo (un `search_path` mal puesto falla, no filtra de más) | Alto si se olvida `.filter(tenant=...)` en algún query | Nulo |
| Costo operativo (1 cluster) | Medio | Bajo | Alto (N conexiones, N backups) |
| Migraciones | `migrate_schemas` — 1 comando para todos los tenants | Estándar | N migraciones independientes |
| Backup/restore por cliente | Por schema (`pg_dump -n`) | No trivial (hay que filtrar) | Trivial |

El aislamiento "duro" es relevante porque algunos datos son sensibles (datos personales de clientes finales bajo Habeas Data; en el futuro, facturación). Row-level es viable pero traslada el riesgo a disciplina de código (un solo manager mal usado expone datos de otro tenant). Schema-per-tenant convierte ese riesgo en un error de configuración detectable, no en una fuga silenciosa en producción.

**Límite conocido:** PostgreSQL maneja bien hasta unos pocos miles de schemas por instancia antes de que el catálogo (`pg_catalog`) empiece a degradar el rendimiento de herramientas. Para el horizonte actual (decenas a cientos de tenants PYME) no es un problema; si se proyectan >2,000 tenants activos, evaluar particionamiento por clúster — **no requiere cambio de patrón, solo de topología**.

### 3.2 Distribución de apps: `SHARED_APPS` vs `TENANT_APPS`

```python
# config/settings/base.py

SHARED_APPS = [
    "django_tenants",          # framework multitenant
    "apps.plataforma",         # Tenant, Dominio, Plan, ModuloCatalogo, Suscripcion
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
]

TENANT_APPS = [
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.admin",
    "apps.accounts",
    "apps.clientes",
    "apps.ordenes",
    "apps.inventario",
    "apps.produccion",
    "apps.mantenimiento",
    "apps.portafolio",
    "apps.reportes",
    "apps.notificaciones",
    "apps.core",               # AuditLog, ModuloConfig (instancia local), EventLog
    # --- Diferidos (estructura reservada, sin lógica en el desarrollo actual) ---
    # "apps.facturacion",      # DIAN — más allá de Fase II
    # "apps.asistente_ia",     # IA — plan Full, post-estabilización
]

INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

TENANT_MODEL = "plataforma.Tenant"
TENANT_DOMAIN_MODEL = "plataforma.Dominio"

DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)
```

**Regla práctica:** todo lo de `core/` y los apps funcionales de v4 va a `TENANT_APPS`. Lo nuevo es `apps.plataforma`, que vive en el schema `public` y contiene el "cerebro" comercial. Las apps `facturacion` y `asistente_ia` se dejan comentadas/reservadas: el código no se escribe ahora, pero el lugar en la arquitectura está definido.

```python
# apps/plataforma/models.py
from django_tenants.models import TenantMixin, DomainMixin

class Tenant(TenantMixin):
    nombre_comercial = models.CharField(max_length=120)
    nit = models.CharField(max_length=20)
    plan = models.ForeignKey("Plan", on_delete=models.PROTECT)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    auto_create_schema = True
    auto_drop_schema = False  # nunca borrar automáticamente: solo desactivar


class Dominio(DomainMixin):
    """cliente.miapp.com (subdominio) o dominio propio en el futuro"""
    pass


class ModuloCatalogo(models.Model):
    codigo = models.CharField(max_length=40, unique=True)  # "inventario", "portafolio"
    nombre = models.CharField(max_length=80)
    descripcion = models.TextField(blank=True)


class Plan(models.Model):
    # Alcance actual: solo "esencial" y "profesional". "full" reservado para el futuro.
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=40)
    usuarios_incluidos = models.PositiveIntegerField()
    precio_mensual_cop = models.DecimalField(max_digits=10, decimal_places=2)
    modulos_incluidos = models.ManyToManyField(ModuloCatalogo)


class Suscripcion(models.Model):
    # Gestión MANUAL: un Admin de plataforma crea/edita estos registros a mano.
    ESTADOS = [("activa", "Activa"), ("mora", "En mora"),
               ("suspendida", "Suspendida"), ("cancelada", "Cancelada")]

    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    usuarios_adicionales = models.PositiveIntegerField(default=0)
    fecha_inicio = models.DateField()
    fecha_proximo_pago = models.DateField()   # informativo; se administra a mano
    estado = models.CharField(max_length=12, choices=ESTADOS, default="activa")
    notas = models.TextField(blank=True)      # registro manual de pagos/observaciones
```

`ModuloConfig` (en cada tenant) refleja qué módulos están activos para ese tenant según su plan. Se sincroniza desde `Suscripcion` cuando el Admin de plataforma cambia el plan.

```python
# apps/core/models.py (vive en TENANT_APPS, una copia por schema)
class ModuloConfig(models.Model):
    codigo = models.CharField(max_length=40, unique=True)  # matchea ModuloCatalogo.codigo
    activo = models.BooleanField(default=False)
```

```python
# apps/plataforma/tasks.py  (o función síncrona — no requiere Celery para esto)
def sincronizar_modulos(tenant_id: int) -> None:
    """Refleja los módulos del Plan en ModuloConfig del schema del tenant."""
    tenant = Tenant.objects.get(id=tenant_id)
    codigos_activos = set(
        tenant.plan.modulos_incluidos.values_list("codigo", flat=True)
    )
    with schema_context(tenant.schema_name):
        ModuloConfig.objects.update(activo=False)
        ModuloConfig.objects.filter(codigo__in=codigos_activos).update(activo=True)
```

### 3.3 Resolución de tenant (subdominio → schema)

`django-tenants` resuelve el schema activo en `TenantMainMiddleware`, basado en el `Host` header. Debe ser el **primer** middleware de la cadena, porque el branding (logo, paleta) y el contexto de autenticación dependen de saber **qué tenant** sirve la request antes de tocar sesión o templates.

```python
MIDDLEWARE = [
    "django_tenants.middleware.main.TenantMainMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # ... resto del stack (auditoría, RBAC)
]
```

DNS: wildcard `*.dominio.com` apuntando al mismo Nginx. Dominio propio del cliente (futuro) se resuelve agregando una fila adicional en `Dominio` — no requiere cambios de arquitectura.

### 3.4 Alta de tenants (manual)

En esta etapa el alta de un tenant la ejecuta un **Admin de plataforma**, no un flujo automático disparado por pago. Pasos:

1. Admin de plataforma crea el `Tenant` (nombre, NIT) y asigna `Plan` desde el admin de Django de `apps.plataforma`.
2. `Tenant.save()` → `django-tenants` crea el schema y corre `migrate_schemas` automáticamente (`auto_create_schema = True`).
3. Rutina `seed_tenant` (puede ejecutarse desde un management command o un signal post-creación):
   - Crea `Rol` por defecto (Developer/Admin/Operario/Consulta/Cliente — RBAC de v4).
   - Crea usuario Admin inicial del tenant (credenciales temporales, forzar cambio en primer login).
   - Crea `InfoEmpresa` placeholder.
   - Crea filas `ModuloConfig` para todos los códigos del catálogo, en `activo=False`.
4. `sincronizar_modulos` activa los módulos del plan asignado.
5. Admin de plataforma entrega subdominio y credenciales al cliente.

> Cuando el producto madure, este flujo manual puede automatizarse (self-service + pasarela). Hoy se mantiene manual a propósito, para no construir infraestructura de cobro antes de validar el producto.

### 3.5 Migraciones y backups

- **Migraciones:** `python manage.py migrate_schemas --shared` (apps de `public`) y `migrate_schemas` (apps de tenant, aplica a todos los schemas). Una migración que rompe en un tenant rompe en todos: probar contra varios schemas antes de aplicar en producción.
- **Backups:** `pg_dump -n <schema>` permite backup/restore por tenant. Backup completo del cluster como red de seguridad principal.
- **Datos por tenant vs. plataforma:** datos de negocio y auditables (OTs, inventario, AuditLog) viven en el schema del tenant. Solo lo "de plataforma" (planes, suscripciones, catálogo de módulos) vive en `public`.

### 3.6 Almacenamiento de archivos (MinIO)

Bucket único con prefijo `<schema_name>/...` por tenant — evita escalar la gestión de buckets linealmente con tenants; las presigned URLs aíslan por prefijo.

### 3.7 Pooling de conexiones

Con varios tenants y Gunicorn multi-worker, **pgbouncer en modo `transaction`** desde el inicio — sin esto, el número de conexiones a Postgres escala con `workers × tenants concurrentes` y se agota. (Si en arranque local con pocos tenants resulta sobredimensionado, puede posponerse, pero debe quedar previsto antes de producción.)

---

## 4. Modelo Comercial — Planes y Módulos

Modelos `Plan`, `Suscripcion`, `ModuloCatalogo` ya definidos en §3.2. Puntos de operación en esta etapa:

- **Gestión manual:** el Admin de plataforma crea/edita suscripciones, registra pagos como notas, y cambia estados a mano desde el admin de Django.
- **Estado de cuenta (informativo):** dentro del tenant, una vista muestra plan vigente, fecha de próximo pago y módulos incluidos. No cobra ni bloquea por pasarela; refleja lo que el Admin de plataforma haya registrado.
- **Cambio de plan:** Admin de plataforma actualiza `Suscripcion.plan` → se ejecuta `sincronizar_modulos`. Un downgrade que desactiva un módulo **no borra datos**: solo oculta la UI y apaga el servicio (principio de módulos activables de v4).
- **Planes en esta etapa:** Esencial y Profesional. El registro `Plan` con código "full" puede existir como placeholder, pero sus módulos diferenciales (IA) no están implementados.

---

## 5. Espacios reservados para módulos diferidos

Estos módulos **no se desarrollan ahora**. Se documenta únicamente cómo la arquitectura les deja espacio, para que añadirlos después no obligue a reescribir el core.

### 5.1 Facturación electrónica DIAN (más allá de Fase II)

- App `apps.facturacion` reservada (comentada en `TENANT_APPS`).
- Cuando se implemente: la factura se emite **a nombre del tenant** (su NIT, su resolución DIAN, su certificado), no de la plataforma. Cada tenant tendrá su propia configuración fiscal y, normalmente, su propio contrato con un PTC (Proveedor Tecnológico Certificado).
- Gancho previsto: el evento `ot.entregada` del event bus interno (ya contemplado en v4) será el disparador del borrador de factura. Ese evento ya existirá por el módulo de OTs, así que no hay que añadir nada al core para soportarlo después.
- **No se construye modelo, UI con lógica, ni integración PTC en esta etapa.**

### 5.2 Asistente IA (plan Full, post-estabilización)

- App `apps.asistente_ia` reservada (comentada en `TENANT_APPS`).
- Cuando se implemente: el módulo será **activable/desactivable** por tenant; con el módulo inactivo, ningún servicio de IA corre y la UI no aparece (igual que cualquier otro módulo inactivo).
- Principio de diseño a respetar desde ya: las acciones del asistente deberán pasar por los **mismos permisos RBAC** del usuario y operar dentro del `schema_context` del tenant. Nada en el core actual impide esto; solo hay que no acoplar lógica de negocio de forma que dependa de la existencia del asistente.
- **No se construye integración con ningún LLM, ni modelo de costos/cuotas, en esta etapa.** (El análisis de costos de IA se retomará cuando este módulo entre en alcance.)

---

## 6. Seguridad y Cumplimiento Transversal

- **RBAC (v4) sin cambios de diseño** — vive dentro de cada schema de tenant, por lo que ya está aislado.
- **AuditLog** por tenant (en su schema) + un AuditLog de plataforma en `public` para eventos cross-tenant (alta de tenant, cambios de plan).
- **Habeas Data (Ley 1581/2012):** la plataforma es **encargado del tratamiento**; cada tenant es **responsable del tratamiento** de los datos de sus propios clientes/empleados. Implicación contractual (acuerdo de tratamiento entre plataforma y cada tenant) además de técnica; condiciona qué se loguea y cuánto se retiene.
- Seguridad técnica OWASP (Django ORM, CSRF, cookies `HttpOnly`/`Secure`, validación de uploads) según lo ya definido en v4.

---

## 7. Decisiones Abiertas

| # | Tema | Pendiente |
|---|---|---|
| 1 | Dominio raíz de producción | Definir el dominio sobre el que cuelga el wildcard `*.dominio.com` |
| 2 | Política de retención de `AuditLog` | Relevante para Habeas Data y para no inflar la BD indefinidamente |
| 3 | pgbouncer en local | Decidir si se incluye desde el arranque o se añade antes de producción |
| 4 | Precios COP de planes Esencial / Profesional | Valores comerciales finales |

---

## 8. Próximos pasos

1. **Sprint 0 — Cimientos y plataforma:** Docker Compose (Django + PostgreSQL + Redis + MinIO) + `django-tenants` configurado + `apps.plataforma` (Tenant, Dominio, Plan, Suscripcion, ModuloCatalogo) + RBAC base (`apps.accounts`, `apps.core`). Todo lo demás depende de esto.
2. **Sprint 1+** según el plan de v4: Clientes y OTs → Inventario y Mantenimiento → Notificaciones y Portafolio → Reportes y Configuración.
3. Módulos diferidos (DIAN, IA) se retoman solo tras estabilizar y probar las primeras versiones.

> **Nota de proceso:** los módulos `facturacion` y `asistente_ia` permanecen como espacios reservados. No deben implementarse hasta que el producto base esté validado en uso real, por decisión explícita de alcance.
