# ─────────────────────────────────────────────
# STAGE 1: Builder — instala dependencias Python
# ─────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copiar requirements — usar requirements/production.txt
COPY requirements/base.txt requirements/base.txt
COPY requirements/production.txt requirements/production.txt

RUN pip install --user --no-cache-dir -r requirements/production.txt

# ─────────────────────────────────────────────
# STAGE 2: Runtime — imagen final mínima
# ─────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_ENV=production \
    DJANGO_SETTINGS_MODULE=findempro.settings.production \
    PATH="/home/django/.local/bin:$PATH"

# Instalar solo runtime libs necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    netcat-openbsd \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Usuario no-root
RUN useradd -m -u 1000 -s /bin/bash django

WORKDIR /app

# Copiar dependencias Python del builder
COPY --from=builder /root/.local /home/django/.local

# Copiar código de la aplicación
COPY --chown=django:django . .

# Crear directorios necesarios con permisos correctos
RUN mkdir -p \
        /app/staticfiles \
        /app/media \
        /app/media/chart_images \
        /app/logs \
    && chown -R django:django /app

# Copiar y configurar entrypoint
COPY --chown=django:django docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

USER django

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "-c", "gunicorn.conf.py", "findempro.wsgi:application"]
