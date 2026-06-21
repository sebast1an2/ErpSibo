# ============================================================================
# SIBO ERP — Makefile (atajos de comandos Docker Compose + Django)
# ============================================================================
# Uso: "make <target>", por ejemplo "make up".
# ----------------------------------------------------------------------------

# .PHONY: estos nombres no son archivos, son comandos. Evita conflictos si
# alguna vez existiera un archivo llamado "build", "up", etc.
.PHONY: build up down logs ps \
        manage migrate makemigrations shell createsuperuser bootstrap

# Construye (o reconstruye) las imágenes del stack, principalmente la de "web".
build:
	docker compose build

# Levanta todos los servicios en segundo plano (-d = detached).
up:
	docker compose up -d

# Detiene y elimina los contenedores (los volúmenes/datos se conservan).
down:
	docker compose down

# Muestra los logs de todos los servicios en vivo (-f = follow).
# Para uno solo: make logs s=web  ->  docker compose logs -f web
logs:
	docker compose logs -f $(s)

# Lista el estado de los contenedores del proyecto.
ps:
	docker compose ps

# ----------------------------------------------------------------------------
# Targets de Django (se ejecutan DENTRO del contenedor web).
# ----------------------------------------------------------------------------

# Comando genérico de manage.py. Uso:
#   make manage cmd="check"
#   make manage cmd="collectstatic --noinput"
manage:
	docker compose exec web python manage.py $(cmd)

# Crea (idempotente) el tenant `public` y el dominio localhost. Necesario para
# que django-tenants resuelva el dominio raíz en desarrollo. Correr DESPUÉS de
# `make migrate`. Dominio alterno: make bootstrap dom="midominio.com"
bootstrap:
	docker compose exec web python manage.py bootstrap_public_tenant $(if $(dom),--domain $(dom),)

# Migraciones multitenant (django-tenants), en el orden correcto:
#   1) --shared : apps de SHARED_APPS sobre el schema public (plataforma).
#   2) (tenant) : apps de TENANT_APPS sobre CADA schema de tenant existente.
# Si aún no hay tenants creados, el segundo paso simplemente no aplica nada.
migrate:
	docker compose exec web python manage.py migrate_schemas --shared
	docker compose exec web python manage.py migrate_schemas

# Genera migraciones a partir de los cambios en los modelos.
#   make makemigrations            -> todas las apps
#   make makemigrations app=core   -> solo una app
makemigrations:
	docker compose exec web python manage.py makemigrations $(app)

# Shell de Django (con el ORM cargado).
shell:
	docker compose exec web python manage.py shell

# Crea un superusuario.
#
# OJO (django-tenants): los usuarios viven en el schema del TENANT, no en
# `public`. createsuperuser a secas falla o crea el usuario en el schema activo.
# La forma correcta es indicar el schema con tenant_command:
#   docker compose exec web python manage.py tenant_command createsuperuser --schema=<schema_name>
# Este atajo crea el superusuario en el schema que se le pase:
#   make createsuperuser schema=cliente1
createsuperuser:
	docker compose exec web python manage.py tenant_command createsuperuser --schema=$(schema)
