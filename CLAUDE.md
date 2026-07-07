# CLAUDE.md — FindemproAI

Guía rápida para agentes que trabajen en este repo.

## Stack

- **Backend:** Django 4.2 + Django REST Framework 3.15, en `findempro/`. Python 3.12. Celery 5.3 + django-celery-beat para tareas async (motor de simulación Monte Carlo). PostgreSQL 16, Redis 7 (cache/broker), Gunicorn, Nginx.
- **Frontend:** SPA React 18 + TypeScript + Vite, en `frontend/`. Router: react-router-dom. Formularios: react-hook-form. Gráficos: recharts. UI: Radix UI.
- Producción: Kubernetes (namespace `public`, worker4), Cloudflare Tunnel, ingress-nginx.

## Estructura

```
findempro/          # Proyecto Django (apps: business, dashboards, finance, simulate, report, ...)
  requirements/      # base.txt / development.txt / production.txt
  Dockerfile         # multi-stage, runtime no-root (appuser)
  docker-compose.dev.yml / docker-compose.prod.yml
frontend/            # SPA Vite, build a frontend/dist/
  Dockerfile          # multi-stage: builder node:20-alpine -> nginx-unprivileged
.github/workflows/ci.yml
```

## Comandos clave

Backend (desde `findempro/`):
```
python manage.py runserver
python manage.py migrate
python manage.py test
pip install -r requirements/development.txt   # dev
pip install -r requirements/production.txt    # prod
```

Frontend (desde `frontend/`):
```
npm ci
npm run dev       # vite --port 5177
npm run build     # tsc -b && vite build (incluye typecheck)
npm run preview
```

Docker Compose (desde `findempro/`):
```
docker compose -f docker-compose.dev.yml up
docker compose -f docker-compose.prod.yml config -q   # validar sintaxis
```

## CI

`.github/workflows/ci.yml` corre: job `test` (Django), job `docker-build` (smoke test de imagen), job `frontend` (npm ci + npm run build), y `deploy` que depende de `[test, docker-build, frontend]`.

---

## Sesión 2026-07-07 (claude/audit-modernize)

Cambios aplicados en esta sesión (rama `claude/audit-modernize-2026-07-07`), sobre auditoría previa ya realizada:

1. **`.gitignore`**: reforzado con patrones explícitos `**/node_modules/`, `**/__pycache__/`, `*.pyc`, `frontend/dist/`, `.env`/`.env.*` (con excepciones para `.example`), además de los patrones genéricos ya existentes (`node_modules/`, `__pycache__/`, `.venv/`, `venv/`, `dist/`). Se inicializó `git` en este subárbol (antes sin control de versiones local).
2. **CI (`.github/workflows/ci.yml`)**: añadido job `frontend` (Node 20, `npm ci` + `npm run build`, que incluye `tsc -b` como typecheck) y agregado como dependencia (`needs`) del job `deploy`, para que un build roto del frontend bloquee el despliegue a producción.
3. **`findempro/simulate/tasks.py`**: eliminada la tarea Celery muerta `generate_simulation_report` (stub que siempre lanzaba `NotImplementedError` por depender de un módulo inexistente `simulate/utils/report_generator.py`, sin ninguna referencia real en el resto del código). Archivo es CRLF; se preservaron los finales de línea originales.
4. **Docker**: se auditaron `findempro/Dockerfile` y `frontend/Dockerfile`. Ya cumplían las buenas prácticas esperadas (multi-stage, base images pineadas por versión — sin `latest` —, usuario no-root en ambos runtimes, `.dockerignore` completos en cada contexto, sin `COPY` de secretos). **No se requirieron cambios.** Se validó `docker compose config -q` para `docker-compose.dev.yml` y `docker-compose.prod.yml` (ambos OK).

Notas/dudas abiertas (no bloqueantes):
- Las imágenes base usan tags de versión mayor/menor (`python:3.12-slim-bookworm`, `node:20-alpine`, `nginxinc/nginx-unprivileged:1.27-alpine`) en vez de digests SHA256 exactos. Es una práctica común y aceptable, pero si se busca reproducibilidad estricta, considerar pinear por digest.
- `frontend/Dockerfile` hace fallback `npm ci || npm install` en el build — funcional, pero puede enmascarar drift del lockfile; no se tocó por no ser un problema de seguridad.
