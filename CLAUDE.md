# CLAUDE.md — FindemproAI

Guía rápida para agentes que trabajen en este repo.

## Stack

- **Backend:** Django 4.2 + Django REST Framework 3.15, en `findempro/`. Python 3.12. Celery 5.3 + django-celery-beat para tareas async (motor de simulación Monte Carlo). PostgreSQL 16, Redis 7 (cache/broker), Gunicorn, Nginx.
- **Frontend:** SPA React 18 + TypeScript + Vite, en `frontend/`. Router: react-router-dom. Formularios: react-hook-form. Gráficos: recharts. UI: Radix UI.
- Producción: Kubernetes (namespace `public`), Cloudflare Tunnel, ingress-nginx. **Cluster en
  migración (2026-07-08):** el K8s de 8 nodos en Docker Desktop/Windows (worker `desktop-worker4`)
  fue abandonado; el cluster nuevo en Ubuntu Server (k3s/kubeadm) está pendiente de instalar,
  así que `infra/k8s/public/findemproai/` no tiene dónde aplicarse por ahora.

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

## Sesión 2026-07-12 (GBM — proceso de demanda con memoria)

Se añadió el **Movimiento Browniano Geométrico** como proceso de demanda opcional del motor
Monte Carlo (cerró el gap "GBM real" del puente MAE-IA→producción,
`dev/datasets/data_MAE_IA/docs/APLICACION_PRODUCCION.md`):

- **`simulate/core/gbm.py`** (NUEVO, puro NumPy, sin imports de Django/proyecto; backend `xp`
  GPU/CPU inyectado): `calibrar_gbm()` (MLE + corrección de Itô), `calibrar_gbm_desde_niveles()`,
  `params_gbm_desde_momentos()` (relación log-normal CV→σ), `simular_gbm_grid()` (trayectorias
  T×N con `cumsum` sobre el eje de períodos) y `gbm_marginal()`. Portado del notebook de la
  maestría (`Monte Carlo + GBM + derivados/`).
- **Integración aditiva** (no cambia el comportamiento por defecto): nueva opción
  `distribution='gbm'` (o `distribution_type=7`). `MonteCarloConfig` gana campos `gbm_drift`/
  `gbm_volatility`/`gbm_s0` y el método `resolve_gbm_params()`; `from_simulation()` calibra
  deriva/vol desde los **log-retornos** de la demanda histórica. Enganchado en el motor escalar
  (`ScenarioGenerator.generate_time_series`/`generate_for_period`) y en el vectorizado
  (`_sample_demand_grid`, branch `gbm`). Las distribuciones i.i.d. existentes quedan intactas.
- **Diferencia clave vs. el muestreo previo:** i.i.d. por período (sin deriva ni memoria) →
  trayectoria log-normal con deriva y volatilidad calibradas y **memoria temporal** (precios
  siempre positivos).
- **Tests:** `simulate/tests/test_gbm.py` (18 casos: calibración, positividad, memoria,
  marginal, integración escalar+vectorizada, regresión de i.i.d.) en verde;
  `test_vectorized_engine.py` (12) y `test_core_engine.py` (107) sin regresión.
- **Pendiente:** exponer el modo GBM en la UI de configuración de simulación y desplegar.
  Sin commitear/desplegar todavía.

## Sesión 2026-07-08 (GPU Monte Carlo)

Aceleración del motor de simulación con backend **CuPy (GPU) / NumPy (CPU) y fallback automático**:

- **`simulate/core/gpu_backend.py`** — selección de backend (`FINDEMPRO_GPU=auto|on|off`),
  probe seguro de GPU, warmup (evita `KeyError '__import__'` de CuPy en eval restringido),
  namespace matemático vectorizado.
- **`simulate/core/vectorized_engine.py`** — `VectorizedMonteCarlo` evalúa las mismas
  ecuaciones sobre la grilla T×N con arrays; `can_vectorize()` valida vs el motor escalar.
- **`simulate/services/simulation_service.py`** — `run_full_pipeline()` usa el motor
  vectorizado (flag `FINDEMPRO_MC_ENGINE=vectorized`, default ON) con fallback al escalar.
- **Rendimiento**: ~1.000–2.000× sobre el bucle anterior (vectorización, sirve en CPU K8s);
  +~3× end-to-end en GPU (RTX 5070 Ti). Equivalencia numérica exacta validada.
- **Deploy**: manifests K8s a `v20260708` (drift `:latest` corregido). `Dockerfile.gpu`,
  `docker-compose.gpu.yml`, `requirements/gpu.txt`, `docs/GPU_DEPLOY.md` (worker GPU opcional
  en host Linux — el cluster Docker Desktop/Windows no expone GPU).
- **Blackwell/sm_120**: CuPy necesita NVRTC ≥ 12.8 (fijado en gpu.txt) o falla con
  `CUDA_ERROR_NO_BINARY_FOR_GPU`.

**Pendiente del usuario** (no automatizable desde Linux): build + `docker save | ctr import`
de `kapitalya/findemproai:v20260708` en Windows + `kubectl apply -f infra/k8s/public/findemproai/`
(ver `docs/GPU_DEPLOY.md`).

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
