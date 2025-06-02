# Dockerfile
FROM python:3.11-slim as builder

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libmariadb-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Etapa final
FROM python:3.11-slim

# Instalar solo las librerías runtime necesarias
RUN apt-get update && apt-get install -y \
    libmariadb3 \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd -m -u 1000 django

WORKDIR /app

# Copiar dependencias Python desde builder
COPY --from=builder /root/.local /home/django/.local

# Copiar código de la aplicación
COPY --chown=django:django . .

# Crear directorios necesarios
RUN mkdir -p /app/static /app/media /app/logs && \
    chown -R django:django /app

# Script de entrada
COPY --chown=django:django docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

USER django

# Asegurar que los scripts del usuario estén en PATH
ENV PATH=/home/django/.local/bin:$PATH

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "findempro.wsgi:application"]