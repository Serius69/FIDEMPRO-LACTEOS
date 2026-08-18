#!/bin/bash
# docker-entrypoint.sh — FINDEMPRO
# Ejecutado al iniciar el container. Espera DB, migra, collectstatic, luego inicia el proceso.

set -euo pipefail

# ─────────────────────────────────────────────
# Colores para logs
# ─────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[ENTRYPOINT]${NC} $1"; }
log_success() { echo -e "${GREEN}[ENTRYPOINT]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[ENTRYPOINT]${NC} $1"; }
log_error()   { echo -e "${RED}[ENTRYPOINT]${NC} $1"; }

# ─────────────────────────────────────────────
# Esperar PostgreSQL
# ─────────────────────────────────────────────
wait_for_postgres() {
    local host="${DB_HOST:-db}"
    local port="${DB_PORT:-5432}"
    local max_retries=30
    local retry=0

    log_info "Esperando PostgreSQL en ${host}:${port}..."
    while ! pg_isready -h "${host}" -p "${port}" -q 2>/dev/null; do
        retry=$((retry + 1))
        if [ $retry -ge $max_retries ]; then
            log_error "PostgreSQL no disponible después de ${max_retries} intentos. Saliendo."
            exit 1
        fi
        log_warn "PostgreSQL no disponible, reintentando (${retry}/${max_retries})..."
        sleep 2
    done
    log_success "PostgreSQL disponible."
}

# ─────────────────────────────────────────────
# Esperar Redis
# ─────────────────────────────────────────────
wait_for_redis() {
    local redis_url="${REDIS_URL:-redis://redis:6379/0}"
    # Quitar el esquema Y las credenciales antes de parsear. Con una URL con
    # password (redis://:SECRETO@host:6379/1) el parseo viejo dejaba el host
    # vacío, el puerto en basura y —peor— imprimía el SECRETO en los logs del
    # contenedor en cada arranque. Además el wait nunca funcionaba: caía
    # siempre por timeout al "Redis no disponible, continuando sin cache".
    local authority="${redis_url#*://}"   # host:puerto/db  (o user:pass@host:puerto/db)
    authority="${authority##*@}"          # descarta credenciales si las hay
    authority="${authority%%/*}"          # descarta /db
    local host="${authority%%:*}"
    local port="${authority##*:}"
    [ "$port" = "$host" ] && port=6379
    local max_retries=20
    local retry=0

    log_info "Esperando Redis en ${host}:${port}..."
    while ! nc -z "${host}" "${port}" 2>/dev/null; do
        retry=$((retry + 1))
        if [ $retry -ge $max_retries ]; then
            log_warn "Redis no disponible. Continuando sin cache..."
            return 0
        fi
        sleep 1
    done
    log_success "Redis disponible."
}

# ─────────────────────────────────────────────
# Crear directorios necesarios
# ─────────────────────────────────────────────
create_dirs() {
    log_info "Creando directorios..."
    mkdir -p /app/logs /app/media /app/staticfiles /app/media/chart_images
    log_success "Directorios listos."
}

# ─────────────────────────────────────────────
# Correr migraciones Django
# ─────────────────────────────────────────────
run_migrations() {
    log_info "Corriendo migraciones Django..."
    python manage.py migrate --noinput
    log_success "Migraciones completadas."
}

# ─────────────────────────────────────────────
# Colectar archivos estáticos
# ─────────────────────────────────────────────
collect_static() {
    if [ "${SKIP_COLLECTSTATIC:-false}" != "true" ]; then
        log_info "Colectando archivos estáticos..."
        python manage.py collectstatic --noinput --clear
        log_success "Static files colectados."
    else
        log_warn "SKIP_COLLECTSTATIC=true — omitiendo collectstatic."
    fi
}

# ─────────────────────────────────────────────
# Crear superusuario si es necesario
# ─────────────────────────────────────────────
create_superuser() {
    if [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
        log_info "Creando superusuario..."
        python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
email = '${DJANGO_SUPERUSER_EMAIL}'
password = '${DJANGO_SUPERUSER_PASSWORD}'
username = email.split('@')[0]
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superusuario creado: {email}')
else:
    print(f'Superusuario ya existe: {email}')
" 2>/dev/null || true
        log_success "Superusuario listo."
    fi
}

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
main() {
    log_info "Iniciando FINDEMPRO en modo: ${DJANGO_ENV:-production}"

    create_dirs

    # Solo esperar DB/Redis si no es el worker de Celery sin DB
    case "${1:-gunicorn}" in
        celery*)
            wait_for_postgres
            wait_for_redis
            log_info "Iniciando Celery: $*"
            exec "$@"
            ;;
        gunicorn*|python*|uwsgi*)
            wait_for_postgres
            wait_for_redis
            run_migrations
            collect_static
            create_superuser
            log_success "Sistema listo. Iniciando: $*"
            exec "$@"
            ;;
        manage.py*|migrate|shell*)
            wait_for_postgres
            exec python "$@"
            ;;
        *)
            log_info "Ejecutando: $*"
            exec "$@"
            ;;
    esac
}

main "$@"
