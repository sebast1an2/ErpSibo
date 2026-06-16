# ============================================================================
# SIBO ERP — Dockerfile del servicio "web" (Django)
# ============================================================================
# Una "imagen" es la plantilla a partir de la cual Docker crea el contenedor.
# Este archivo es la RECETA para construir esa imagen: qué Python usar, qué
# librerías instalar y dónde queda el código. (Postgres, Redis y MinIO NO
# necesitan Dockerfile propio: usan imágenes oficiales ya hechas.)
# ----------------------------------------------------------------------------

# 1) Imagen base: Python 3.11 en su variante "slim" (ligera, sin extras).
FROM python:3.11-slim

# 2) Variables de entorno para Python dentro del contenedor:
#    - PYTHONDONTWRITEBYTECODE: no genera archivos .pyc (basura en el volumen montado).
#    - PYTHONUNBUFFERED: la salida (logs/print) sale al instante, sin buffer.
#      Imprescindible para ver logs en tiempo real con "docker compose logs".
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3) Dependencias del SISTEMA operativo (no de Python).
#    - libpq5: librería cliente de PostgreSQL que psycopg2-binary necesita en runtime.
#    - build-essential / libpq-dev: herramientas de compilación, por si alguna
#      dependencia futura necesita compilarse. Se eliminan las listas de apt al
#      final para que la imagen quede más pequeña.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        libpq-dev \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4) Directorio de trabajo dentro del contenedor.
#    Todo comando posterior (y el código montado) vive bajo /app.
WORKDIR /app

# 5) Instalación de dependencias Python.
#    Se copia SOLO requirements.txt primero (no todo el código) para aprovechar
#    la caché de Docker: si el código cambia pero requirements no, no reinstala.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# 6) El código fuente NO se copia con COPY en desarrollo: se monta como volumen
#    desde docker-compose.yml (./backend -> /app) para tener hot-reload.
#    En producción sí se haría "COPY . /app". (Se ajustará en el Bloque 0.2.)

# 7) Puerto que el servidor de aplicaciones expondrá dentro de la red Docker.
EXPOSE 8000

# NOTA: el comando de arranque (CMD) se define en docker-compose.yml, porque
# en este Bloque 0.1 aún NO existe proyecto Django. Se completará en el 0.2.
