# ============================================================================
# SIBO ERP — Makefile (atajos de comandos Docker Compose)
# ============================================================================
# Uso: "make <target>", por ejemplo "make up".
# Los targets de Django (migrate, seed, shell, ...) se agregan en el Bloque 0.2.
# ----------------------------------------------------------------------------

# .PHONY: estos nombres no son archivos, son comandos. Evita conflictos si
# alguna vez existiera un archivo llamado "build", "up", etc.
.PHONY: build up down logs ps

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
