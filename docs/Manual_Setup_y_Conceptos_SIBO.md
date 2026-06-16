# Manual de Setup y Conceptos Base — SIBO ERP
## Guía de entorno de desarrollo (WSL2 + Ubuntu + Docker + VS Code + Git/GitHub)

> Pensado para reproducir el entorno desde cero y para entender *por qué* funciona así.
> Audiencia: desarrollador con background en Java/MVC tradicional, nuevo en contenedores y Linux.

---

# PARTE A — Manual reproducible (paso a paso)

## A.1 Instalar Git en Windows
1. Descargar de https://git-scm.com/download/win y ejecutar el instalador.
2. Opciones: editor por defecto el que uses; PATH = "Git from the command line and also from 3rd-party software"; line endings = "Checkout Windows-style, commit Unix-style".
3. Verificar en PowerShell: `git --version`.

> Nota: este Git es el de Windows. Como el proyecto vivirá en Ubuntu, también se usa el Git *de Ubuntu* (ver A.5). Son instalaciones separadas.

## A.2 Instalar WSL2 + Ubuntu
1. PowerShell **como administrador**: `wsl --install`
   - Esto activa WSL2 + Virtual Machine Platform e instala Ubuntu por defecto.
2. Reiniciar el PC.
3. Al volver, Ubuntu termina su instalación ("Downloading... Ubuntu") y pide:
   - **Usuario y contraseña de Ubuntu** (independientes de Windows; el usuario tendrá sudo).
   - **Telemetría de Canonical** ("opt-in to platform metrics"): responder **No** (opcional, sin impacto).
4. Verificar desde PowerShell: `wsl -l -v` → Ubuntu debe figurar como `Default` y versión `2`.

## A.3 Instalar Docker Desktop
1. Descargar de https://www.docker.com/products/docker-desktop/ e instalar.
2. Durante la instalación, dejar marcado "Use WSL 2 instead of Hyper-V".
3. Abrir Docker Desktop → **Settings → Resources → WSL integration**:
   - Activar "Enable integration with my default WSL distro".
   - Activar el toggle de **Ubuntu**.
   - **Apply & restart**.
4. **Cerrar y reabrir la terminal de Ubuntu** y verificar:
   ```bash
   docker --version
   docker compose version
   docker run hello-world
   ```
5. Si sale `permission denied ... docker.sock`:
   ```bash
   sudo usermod -aG docker $USER
   ```
   Luego, desde PowerShell: `wsl --shutdown`. Reabrir Ubuntu y reintentar `docker run hello-world`.
   (El `wsl --shutdown` es necesario para que la sesión recargue los grupos.)

## A.4 Instalar VS Code + extensión WSL
1. Instalar VS Code en Windows (normal).
2. En VS Code → Extensions (`Ctrl+Shift+X`) → instalar **WSL** (publisher: Microsoft).

## A.5 Crear el proyecto DENTRO de Ubuntu y abrirlo
1. Terminal de Ubuntu:
   ```bash
   cd ~
   mkdir -p proyectos/sibo-erp
   cd proyectos/sibo-erp
   ```
2. Configurar Git de Ubuntu (primera vez):
   ```bash
   git --version    # si falla: sudo apt update && sudo apt install git -y
   git config --global user.name "Tu Nombre"
   git config --global user.email "tu@email.com"
   git config --global init.defaultBranch main
   ```
3. Abrir el proyecto en VS Code conectado a WSL:
   ```bash
   code .
   ```
   La primera vez instala "VS Code Server" dentro de Ubuntu.
4. **Confirmar conexión:** abajo a la izquierda debe verse la etiqueta **"WSL: Ubuntu"**.

## A.6 Habilitar extensiones en WSL
Con VS Code conectado a WSL, en Extensions instalar "en WSL: Ubuntu":
- Python (Microsoft)
- GitLens
- Docker (Microsoft)

(Las extensiones de UI pura —temas, iconos— corren del lado Windows y no requieren reinstalarse.)

## A.7 Inicializar repo y conectar GitHub
1. En la terminal integrada de VS Code (ya está dentro de Ubuntu):
   ```bash
   git init
   ```
2. Al primer `push` desde el panel de Source Control, VS Code abrirá el navegador para autorizar GitHub. Aceptar; las credenciales quedan guardadas.

## A.8 Checklist de "entorno listo"
- [ ] `wsl -l -v` → Ubuntu, Default, v2
- [ ] `docker run hello-world` corre sin sudo
- [ ] Proyecto en `~/proyectos/sibo-erp` (NO en `/mnt/c/...`)
- [ ] VS Code muestra "WSL: Ubuntu"
- [ ] `git config --global user.name/email` configurados en Ubuntu
- [ ] Extensiones Python/GitLens/Docker instaladas "en WSL"

---

# PARTE B — Conceptos (el "por qué")

## B.1 ¿Qué es WSL2 y por qué Ubuntu?
WSL2 (Windows Subsystem for Linux v2) es una **máquina virtual ligera de Linux** integrada en Windows. No es un emulador: corre un kernel Linux real. Ubuntu es la distribución (el "sabor" de Linux) que se instaló dentro de WSL2.

¿Por qué lo necesitas? Porque el stack del proyecto (Django, Gunicorn, Celery, Postgres) y Docker corren de forma **nativa y eficiente en Linux**. Forzarlos en Windows puro da problemas de compatibilidad y lentitud.

**Analogía Java:** es como tener una JVM Linux dentro de tu Windows. Tu código corre en el "entorno Linux" aunque tu escritorio siga siendo Windows.

## B.2 ¿Por qué el código NO va en C:\ ?
Windows y Linux tienen sistemas de archivos distintos. Cuando el código está en `C:\` y Linux lo lee vía `/mnt/c/...`, cada lectura cruza una "frontera" entre ambos mundos:
- **Lento:** I/O degradado, muy notable con Django (muchos archivos + recarga automática).
- **Conflictos:** permisos Unix y fin de línea (CRLF de Windows vs LF de Unix).

Por eso el código vive en `/home/tu-usuario/...` (filesystem Linux nativo): velocidad nativa y cero conflictos.

## B.3 ¿Qué es Docker y cómo encaja?
Docker empaqueta cada servicio en un **contenedor**: una unidad aislada que incluye el programa y todo lo que necesita para correr (librerías, versión exacta, config).

**El problema que resuelve (muy familiar viniendo de Java):**
"En mi máquina funciona, en el servidor no." Diferencias de versión de Postgres, de Python, de librerías del sistema. Docker elimina eso: el contenedor lleva su entorno consigo, idéntico en tu PC y en el servidor.

**Conceptos clave:**
| Término | Qué es | Analogía |
|---|---|---|
| **Imagen** | Plantilla inmóvil de un servicio (ej. "postgres:16") | Una clase |
| **Contenedor** | Instancia en ejecución de una imagen | Un objeto (`new`) |
| **Volumen** | Almacenamiento que sobrevive aunque el contenedor se borre | Persistencia/BD en disco |
| **Red Docker** | Red interna por la que los contenedores se hablan por nombre | Servicios que se llaman entre sí |

**Diferencia con una máquina virtual:** una VM virtualiza un sistema operativo completo (pesada). Un contenedor comparte el kernel de Linux y solo aísla el proceso (ligero, arranca en segundos). Por eso puedes correr 7 contenedores a la vez sin fundir el PC.

## B.4 ¿Qué es Docker Compose?
Un proyecto real no es un solo contenedor: SIBO ERP necesita Django + Postgres + Redis + Celery + MinIO + Nginx, todos coordinados.

**Docker Compose** es un archivo (`docker-compose.yml`) donde declaras todos esos servicios y cómo se conectan. Un solo comando los levanta todos juntos:
```bash
docker compose up        # levanta todo el stack
docker compose down      # lo apaga
docker compose logs -f web   # ve los logs del servicio "web" (Django)
```

**Analogía:** es como un orquestador que arranca tu app, tu base de datos y tus servicios auxiliares con un solo botón, ya conectados entre sí. Sin esto, tendrías que instalar y arrancar Postgres, Redis, etc., a mano en tu sistema (justo lo que querías evitar).

## B.5 Cómo se verá tu día a día
- **Abrir el proyecto:** terminal Ubuntu → `cd ~/proyectos/sibo-erp` → `code .`
- **Editar:** VS Code (conectado a WSL).
- **Terminal de trabajo:** la integrada de VS Code (ya abre en Ubuntu). Ahí corres:
  - `docker compose up` para levantar el entorno.
  - Comandos de Django **dentro del contenedor**, por ejemplo:
    ```bash
    docker compose exec web python manage.py migrate
    docker compose exec web python manage.py createsuperuser
    ```
    (`exec web` = "ejecuta esto dentro del contenedor llamado web")
  - `git add/commit/push` para versionar.
- **Ver la app:** en el navegador de Windows, en `http://localhost:8000` (Docker expone el puerto del contenedor hacia tu Windows).

## B.6 Punto mental importante (viniendo de Java manual)
En tu mundo Java/MVC instalabas todo en tu máquina y corrías el servidor directo. Aquí el cambio de chip es:
> **Tú no instalas Postgres, Redis ni Python en tu máquina. Los "instala" Docker dentro de contenedores, definidos en `docker-compose.yml`.** Tu máquina solo necesita Docker.

Tu código fuente sí vive en tu disco (en Ubuntu) y se "monta" dentro del contenedor de Django, de modo que cuando editas un archivo en VS Code, el contenedor lo ve al instante. Tienes lo mejor de ambos: editas cómodo en VS Code, pero ejecuta en el entorno aislado y reproducible.

---

# PARTE C — Antes del Sprint 0 (checklist final)
- [ ] Entorno verificado (checklist A.8).
- [ ] Documento fundacional corregido colocado en `docs/`.
- [ ] Repo `git init` hecho; remoto de GitHub creado (puede hacerse al primer push).
- [ ] Entendido el flujo: editar en VS Code → comandos en terminal WSL → `docker compose` levanta el stack.
