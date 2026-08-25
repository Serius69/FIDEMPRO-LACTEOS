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
    PATH="/home/appuser/.local/bin:$PATH"

# Instalar solo runtime libs necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    netcat-openbsd \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# El pip que trae python:3.12-slim-bookworm (25.0.1) arrastra 6 CVEs propias
# (PYSEC-2026-196/1795/1796/2875/2876). No lo usamos en runtime, pero queda
# instalado en la imagen y pip-audit contra la imagen lo reporta. Se actualiza
# SOLO en runtime: el builder resuelve las dependencias con su propio pip, así
# que el grafo de paquetes de la app no cambia.
RUN pip install --no-cache-dir --upgrade "pip>=26.1.2" \
    && pip --version

# Usuario no-root
RUN useradd -m -u 1000 -s /bin/bash appuser

WORKDIR /app

# Copiar dependencias Python del builder
COPY --from=builder /root/.local /home/appuser/.local

# Copiar código de la aplicación
COPY --chown=appuser:appuser . .

# Crear directorios necesarios con permisos correctos
RUN mkdir -p \
        /app/staticfiles \
        /app/media \
        /app/media/chart_images \
        /app/logs \
    && chown -R appuser:appuser /app \
    && chown -R appuser:appuser /home/appuser/.local

# Copiar y configurar entrypoint
COPY --chown=appuser:appuser docker-entrypoint.sh /docker-entrypoint.sh
RUN sed -i 's/\r$//' /docker-entrypoint.sh && chmod +x /docker-entrypoint.sh

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health/live/ || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "-c", "gunicorn.conf.py", "findempro.wsgi:application"]

# ─────────────────────────────────────────────
# STAGE 3: builder-dev — deps de producción + development.txt (pytest, etc.)
# Solo se construye si algo pide el target `runtime-dev` de abajo — no afecta
# `docker build` sin --target ni docker-compose.prod.yml (target: runtime).
# ─────────────────────────────────────────────
FROM builder AS builder-dev

COPY requirements/development.txt requirements/development.txt
RUN pip install --user --no-cache-dir -r requirements/development.txt

# ─────────────────────────────────────────────
# STAGE 4: runtime-dev — imagen runtime + tooling de dev/test (pytest,
# pytest-django, factory-boy, ...). Usada SOLO por docker-compose.dev.yml
# (`make test` execa pytest dentro de este contenedor). La imagen de
# producción (target: runtime, arriba) nunca incluye estas dependencias.
# ─────────────────────────────────────────────
FROM runtime AS runtime-dev

COPY --from=builder-dev --chown=appuser:appuser /root/.local /home/appuser/.local
