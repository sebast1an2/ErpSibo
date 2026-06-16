# Guía de Estructura de Carpetas — SIBO ERP
## Qué es cada archivo y carpeta, y por qué existe

> Pensado para alguien que viene de Java/MVC tradicional y se está familiarizando con un proyecto Django contenedorizado.

---

## Vista general

```
sibo-erp/                      ← RAÍZ del proyecto (esto es lo que abres en VS Code)
├── docker-compose.yml         ← Orquestador: define todos los servicios (Django, Postgres, etc.)
├── .env.example               ← Plantilla de variables de entorno (sin secretos reales)
├── .env                       ← Variables reales (NO se sube a git; lo creas tú a partir de .env.example)
├── .gitignore                ← Qué archivos git debe IGNORAR (no versionar)
├── Makefile                   ← Atajos de comandos (make up, make migrate, etc.)
├── nginx/
│   └── nginx.conf             ← Configuración del servidor web Nginx
├── docs/                      ← Tu documentación (documento fundacional, manuales, prompts)
└── backend/                   ← TODO el código Django vive aquí dentro
```

La distinción mental clave: **la raíz contiene infraestructura** (cómo se levanta y orquesta todo), y **`backend/` contiene el código de la aplicación** (Django). En Java sería como separar la configuración del servidor/contenedor de tu código fuente.

---

## Archivos de la RAÍZ (infraestructura)

### `docker-compose.yml`
El archivo más importante de la infraestructura. Declara cada servicio (contenedor) que compone el sistema: la base de datos, Redis, MinIO, Django, Nginx. Define cómo se conectan entre sí, qué puertos exponen y qué volúmenes (almacenamiento persistente) usan.
- **Analogía:** como un script que en vez de instalar y arrancar Postgres, Redis, etc. a mano en tu PC, lo declara y Docker lo levanta todo con `docker compose up`.

### `.env.example` y `.env`
Las **variables de entorno**: configuración que cambia entre entornos (tu PC vs. producción) y datos sensibles (contraseñas de BD, claves secretas).
- `.env.example` es la **plantilla** (se sube a git, sin valores reales) — sirve de referencia de qué variables existen.
- `.env` es tu copia con los **valores reales** (NO se sube a git, por seguridad).
- **Analogía Java:** como un `application.properties`, pero separando explícitamente lo público de lo secreto.

### `.gitignore`
Lista de archivos/carpetas que git debe **ignorar** (no versionar). Aquí van: `.env`, archivos compilados de Python (`__pycache__`), entornos virtuales, archivos de IDE, etc.
- **Por qué importa:** evita subir secretos (`.env`) y basura generada al repositorio.

### `Makefile`
Una colección de **atajos de comandos**. En vez de escribir comandos Docker largos, defines alias cortos:
- `make up` en vez de `docker compose up -d`
- `make migrate` en vez de los dos comandos de `migrate_schemas`
- `make logs` para ver los logs, etc.
- **Por qué:** ahorra tipeo y estandariza los comandos del equipo.

### `nginx/nginx.conf`
Configuración de **Nginx**, el servidor web que se pone "delante" de Django.
- **Qué hace Nginx:** recibe las peticiones del navegador, sirve archivos estáticos (CSS, JS, imágenes) de forma eficiente, y pasa las peticiones "dinámicas" a Django (que corre con Gunicorn).
- **Analogía:** como un Apache/Tomcat al frente, pero Nginx solo enruta y sirve estáticos; la lógica la ejecuta Django.

### `docs/`
Tu documentación del proyecto. No es código; es material de referencia (documento fundacional, manuales, prompts de cada sprint).

---

## Carpeta `backend/` (el código Django)

```
backend/
├── Dockerfile                 ← Receta para construir la imagen del contenedor de Django
├── requirements.txt           ← Lista de librerías Python que el proyecto necesita
├── manage.py                  ← Punto de entrada de comandos Django
├── config/                    ← Configuración del PROYECTO Django (no de una app)
└── apps/                      ← Las APLICACIONES Django (los módulos del sistema)
```

### `Dockerfile`
La **receta** para construir la imagen del contenedor de Django: qué versión de Python usar, qué librerías instalar (`requirements.txt`), cómo arrancar la app.
- **Diferencia con docker-compose.yml:** el Dockerfile construye UNA imagen (la de Django). El docker-compose ORQUESTA varios contenedores juntos (Django + Postgres + Redis...). Postgres y Redis usan imágenes oficiales ya hechas, por eso solo Django necesita Dockerfile propio.

### `requirements.txt`
Lista de **dependencias Python** con sus versiones (Django, django-tenants, etc.).
- **Analogía Java:** es el equivalente al `pom.xml` (Maven) o `build.gradle` (Gradle), pero más simple: solo una lista de librerías y versiones.

### `manage.py`
El **punto de entrada** de los comandos de Django. Con él corres migraciones, creas usuarios, levantas el servidor de desarrollo, ejecutas comandos personalizados (como el `seed_tenant`).
- Ejemplo: `python manage.py migrate`. (En este proyecto se corre dentro del contenedor: `docker compose exec web python manage.py migrate`.)

---

## Carpeta `config/` (configuración del proyecto)

```
config/
├── __init__.py                ← Marca la carpeta como "paquete Python" (archivo vacío)
├── settings/
│   ├── base.py                ← Configuración común a todos los entornos
│   ├── development.py         ← Config específica de desarrollo (hereda de base)
│   └── production.py          ← Config específica de producción (hereda de base)
├── urls.py                    ← Enrutador raíz: qué URL va a qué app
├── wsgi.py                    ← Punto de entrada para servidor web tradicional (Gunicorn)
└── asgi.py                    ← Punto de entrada para servidor async (WebSockets, futuro)
```

### `__init__.py`
Un archivo (normalmente vacío) que le dice a Python "esta carpeta es un paquete importable". Verás muchos por todo el proyecto. No tienen contenido relevante; son una señalización técnica de Python.

### `settings/` (dividido en base/development/production)
La **configuración de todo el proyecto Django**: base de datos, apps instaladas, middleware, idioma, etc.
- Se divide en tres porque la config de tu PC (development) y la del servidor (production) difieren (ej. `DEBUG=True` solo en desarrollo). `base.py` tiene lo común; los otros dos heredan y sobreescriben lo específico.
- **Aquí vive la configuración crítica de django-tenants** (SHARED_APPS, TENANT_APPS, middleware).
- **Analogía Java:** como tener perfiles de Spring (`application-dev.properties` vs `application-prod.properties`).

### `urls.py`
El **enrutador raíz**: mapea URLs a las vistas/apps que las atienden.
- **Analogía:** como el mapeo de rutas de tu controlador en MVC, pero centralizado.

### `wsgi.py` / `asgi.py`
Puntos de entrada que el servidor (Gunicorn) usa para "hablar" con Django.
- `wsgi.py`: para peticiones HTTP normales (lo que usarás ahora).
- `asgi.py`: para cosas asíncronas como WebSockets (lo necesitarás más adelante para actualizaciones en tiempo real del Kanban; por eso ya queda creado).
- No los editarás casi nunca; son plomería estándar.

---

## Carpeta `apps/` (los módulos del sistema)

Aquí vive la lógica de negocio, **dividida en aplicaciones** (las "apps" de Django). Cada app es un módulo autónomo del ERP.

```
apps/
├── plataforma/                ← SHARED: tenants, planes, suscripciones (schema público)
├── core/                      ← TENANT: auditoría, config de módulos, event bus
├── accounts/                  ← TENANT: usuarios, roles, permisos (RBAC)
│
│   --- Se añaden en sprints posteriores: ---
├── clientes/                  ← (Sprint 1)
├── ordenes/                   ← (Sprint 1) Órdenes de Trabajo
├── inventario/                ← (Sprint 2)
├── mantenimiento/             ← (Sprint 2)
├── produccion/                ← (Sprint 1-2)
├── portafolio/                ← (Sprint 3)
├── notificaciones/            ← (Sprint 3)
└── reportes/                  ← (Sprint 4)
```

> **Importante:** en el Sprint 0 solo se implementan `plataforma`, `core` y `accounts`. Las demás aparecen mencionadas en los settings pero vacías o ausentes — se llenan sprint por sprint. Esto explica por qué "faltan" Inventario y OTs ahora: están planificadas para sprints siguientes.

### Estructura interna de cada app
Cada app de Django tiene una estructura interna estándar:

```
una_app/
├── __init__.py
├── models.py                  ← Modelos de datos (tablas de BD). Como tus @Entity de Java
├── views.py                   ← Lógica que responde a las peticiones. Como tus controladores
├── urls.py                    ← Rutas específicas de esta app
├── serializers.py             ← Convierte modelos ↔ JSON (para las APIs REST)
├── admin.py                   ← Configura cómo se ven los modelos en el admin de Django
├── apps.py                    ← Config de la app (autogenerado, casi no se toca)
├── permissions.py             ← Reglas de permisos RBAC de esta app
├── migrations/                ← Historial de cambios al esquema de BD (autogenerado)
└── tests/                     ← Pruebas automatizadas
```

**Mapa mental rápido viniendo de Java/MVC:**
| Django | Equivalente Java/MVC aproximado |
|---|---|
| `models.py` | Entidades / `@Entity` |
| `views.py` | Controladores |
| `serializers.py` | DTOs / mapeo a JSON |
| `urls.py` | Mapeo de rutas |
| `admin.py` | (no tiene equivalente directo) panel CRUD autogenerado |
| `migrations/` | Scripts de migración de BD (tipo Flyway/Liquibase, pero autogenerados) |

### El concepto de "app" en Django
En Django, una "app" no es "la aplicación completa" — es un **módulo funcional reutilizable**. El proyecto entero (SIBO ERP) se compone de muchas apps (plataforma, ordenes, inventario...). Cada una agrupa los modelos, vistas y lógica de un dominio concreto.
- **Analogía:** como dividir un monolito Java en paquetes/módulos bien separados por dominio, donde cada paquete trae sus entidades, su lógica y sus rutas.

---

## Lo más importante de recordar

1. **Raíz = infraestructura** (Docker, Nginx, Make). **`backend/` = código Django.**
2. **`config/` = configuración del proyecto** (settings, urls, multitenancy).
3. **`apps/` = los módulos del sistema**, uno por dominio de negocio.
4. **Los `__init__.py` vacíos** son solo señalización de Python; ignóralos.
5. **`migrations/`** se genera solo cuando cambias modelos; no se escribe a mano.
6. **Muchas apps están "reservadas"** y se implementan sprint por sprint — no todo se construye de una vez.
