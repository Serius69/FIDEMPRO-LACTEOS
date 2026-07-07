# FindemproAI — Simulación Financiera para PYMES con IA

> Plataforma Django de apoyo a decisiones financieras para PYMES bolivianas: simulación Monte Carlo con hasta 10.000 escenarios, métricas VaR/CVaR/Sharpe y recomendaciones automáticas por IA.

**Stack:** Django 4.2 · Celery · PostgreSQL 16 · Redis 7 · Nginx · **URL:** app.kapitalya.com.bo · **Estado:** ✅ K8s Running

---

## Qué resuelve

Las PYMES del sector productivo boliviano (lácteo, agroindustrial, manufacturero) toman decisiones financieras críticas —nivel de inventario, inversión en capacidad, financiamiento— sin herramientas cuantitativas accesibles. Contratar un asesor financiero para cada decisión es costoso y lento.

FindemproAI permite a cualquier PYME cuantificar el riesgo financiero de sus decisiones en minutos: define su modelo de operación (productos, variables, ecuaciones), carga datos históricos de demanda, y el sistema ejecuta miles de escenarios Monte Carlo de forma asíncrona para entregar VaR, CVaR, Sharpe Ratio, Sortino Ratio y recomendaciones categorizadas automáticamente.

La plataforma soporta 19 tipos de industria y 6 sectores configurables, con un canvas visual drag-and-drop (Canvas v2, Cytoscape.js) que permite modelar flujos stocks-and-flows tipo iThink sin conocimientos de programación.

## Propuesta de valor

| | |
|--|--|
| **Problema** | PYMES sin herramientas de simulación financiera accesibles |
| **Solución** | Django + Monte Carlo + IA: escenarios probabilísticos con métricas de riesgo |
| **Resultado** | Decisiones financieras cuantificadas en segundos, sin asesor externo |

---

## Stack técnico

| Componente | Tecnología |
|------------|-----------|
| Backend | Python 3.12 · Django 4.2 · Django REST Framework 3.15 |
| Tareas async | Celery 5.3 + django-celery-beat |
| Autenticación | Django Allauth + OAuth2 (Google) |
| Ciencia de datos | NumPy 1.26 · SciPy 1.13 · Pandas 2.2 · scikit-learn 1.5 · statsmodels 0.14 · SimPy 4.1 |
| Frontend | Bootstrap 5 · ApexCharts · Chart.js · ECharts · Cytoscape.js |
| Reportes | ReportLab (PDF) · openpyxl (Excel) · Matplotlib/Seaborn |
| Base de datos | PostgreSQL 16 |
| Cache / Broker | Redis 7 |
| Servidor WSGI | Gunicorn |
| Proxy | Nginx 1.25 |
| Observabilidad | Sentry · Prometheus · logs JSON estructurados |
| API docs | drf-yasg (Swagger UI + ReDoc) |

---

## Arquitectura

```
Cloudflare Tunnel
       │
  ingress-nginx (K8s namespace: public, worker4)
       │
  ┌────┴─────────────────────────────────┐
  │  4 pods K8s:                         │
  │                                      │
  │  findempro-app       (Django/Gunicorn)│
  │  findempro-celery    (worker Celery)  │
  │  findempro-beat      (scheduler)     │
  │  findempro-nginx     (proxy estático) │
  └──────────┬──────────────┬────────────┘
             │              │
       PostgreSQL 16      Redis 7
       (datos + ORM)   (cache + broker)

Motor de simulación (simulate/core/):
  DiscreteEventEngine ──► ScenarioGenerator ──► DecisionEngine
        │                       │                     │
  ecuaciones             distribuciones         VaR/CVaR/Sharpe
  topológicas         Normal/LogN/Gamma/...   + recomendaciones IA
```

**Fix K8s aplicado:** `CompressedStaticFilesStorage` (no manifest) + init container `collectstatic`. Removido `HiredisParser` (incompatible con redis-py v5). Readiness probe en `/health/ready/` (no `/api/*` — DRF tiene auth global).

---

## Apps Django

| App | Responsabilidad |
|-----|----------------|
| `findempro` | Core: settings, URLs raíz, health checks |
| `business` | Empresa y perfil (19 industrias, 6 sectores) |
| `product` | Productos y líneas de negocio |
| `variable` | Variables del modelo (parámetros configurables) |
| `simulate` | Motor MC, Canvas v2, tareas Celery, análisis OAT |
| `finance` | Datos financieros históricos |
| `questionary` | Cuestionarios de parametrización inicial |
| `report` | Generación de reportes PDF y Excel |
| `dashboards` | Dashboards analíticos interactivos |
| `pages` | Páginas estáticas y de error |
| `user` | Gestión de usuarios y perfiles |

---

## Endpoints principales

### API v1

| Endpoint | Descripción |
|----------|-------------|
| `GET /health/` | Health check general |
| `GET /health/ready/` | Readiness probe K8s |
| `GET /health/live/` | Liveness probe K8s |
| `GET /swagger/` | Swagger UI interactivo |
| `GET /redoc/` | ReDoc documentación |
| `POST /simulate/` | Ejecutar simulación Monte Carlo |
| `GET /report/` | Listado de reportes generados |
| `GET /business/` | Gestión de empresas |

### API v2 — Canvas Visual (`/api/v2/`)

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/projects/` | GET, POST | CRUD proyectos de simulación |
| `/projects/{id}/nodes/` | GET, POST | CRUD nodos del modelo |
| `/projects/{id}/edges/` | GET, POST | CRUD aristas |
| `/simulate/` | POST | Compilar grafo y ejecutar MC/DES |
| `/simulate/live-update/` | POST | Actualización en tiempo real (<500 ms) |
| `/simulate/validate/` | POST | Validar modelo antes de ejecutar |
| `/simulate/causal-diagram/` | GET | Diagrama causal Cytoscape.js |
| `/projects/{id}/simulate/sensitivity/` | POST | Análisis OAT (tornado chart) |
| `/alerts/` | GET, POST, PUT, DELETE | CRUD alertas VaR/CVaR por usuario |

---

## Motor de simulación (`simulate/core/`)

| Módulo | Responsabilidad |
|--------|----------------|
| `discrete_engine.py` | Resuelve ecuaciones en orden topológico con estado entre períodos |
| `monte_carlo.py` | Genera N escenarios; ajuste automático de distribución por test KS |
| `decision_engine.py` | VaR, CVaR, Sharpe, Sortino; función utilidad CARA; recomendaciones automáticas |
| `model_compiler.py` | Compila grafo visual Canvas v2 → `SimulationConfig` |

Distribuciones soportadas: Normal, LogNormal, Gamma, Exponencial, Uniforme, Poisson.

---

## Estructura del proyecto

```
FindemproAI/
└── findempro/
    ├── findempro/              # Core (settings/, urls.py, wsgi.py)
    │   └── settings/
    │       ├── base.py · development.py · staging.py · production.py
    ├── simulate/               # App principal — motor de simulación
    │   ├── core/
    │   │   ├── discrete_engine.py
    │   │   ├── monte_carlo.py
    │   │   ├── decision_engine.py
    │   │   └── model_compiler.py
    │   ├── services/
    │   │   ├── simulation_service.py
    │   │   ├── sensitivity_service.py  # Análisis OAT + tornado chart
    │   │   └── financial_analysis.py
    │   ├── tasks.py            # Celery: run_sensitivity_async, check_var_alerts_async
    │   ├── canvas_models.py · canvas_serializers.py · canvas_dataclasses.py
    │   └── tests/              # 251 tests
    ├── business/ · product/ · variable/ · finance/
    ├── questionary/ · report/ · dashboards/ · pages/ · user/
    ├── static/js/model_canvas.js  # FindemproCanvas (Cytoscape.js)
    ├── templates/
    ├── requirements/
    │   ├── base.txt · development.txt · production.txt
    ├── nginx/
    ├── Dockerfile              # Multi-stage (builder + runtime)
    ├── docker-compose.prod.yml
    ├── docker-compose.dev.yml
    ├── gunicorn.conf.py
    ├── Makefile
    └── manage.py
```

---

## Variables de entorno

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `SECRET_KEY` | Django secret key | Sí |
| `DEBUG` | `False` en producción | Sí |
| `DJANGO_ENV` | `development` / `staging` / `production` | Sí |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos + `*` para K8s IPs | Sí |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | Credenciales PostgreSQL | Sí |
| `DB_HOST` / `DB_PORT` | Conexión PostgreSQL | Sí |
| `REDIS_URL` | URL Redis para cache | Sí |
| `CELERY_BROKER_URL` | URL broker Celery | Sí |
| `CELERY_RESULT_BACKEND` | Backend resultados Celery | Sí |
| `SOCIAL_AUTH_GOOGLE_OAUTH2_KEY` | Client ID Google OAuth2 | No |
| `SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET` | Client Secret Google OAuth2 | No |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP para alertas | No |
| `SENTRY_DSN` | DSN Sentry para errores | No |

---

## K8s / Despliegue

- **Namespace:** `public`
- **Worker:** `desktop-worker4`
- **Pods:** 4 — `findempro-app`, `findempro-celery-worker`, `findempro-celery-beat`, `findempro-nginx`
- **URL producción:** https://app.kapitalya.com.bo
- **Imagen:** `kapitalya/findemproai:vYYYYMMDD` (imagePullPolicy: IfNotPresent)
- **Health check:** `GET /health/` (django-health-check) para readiness probe

```powershell
# Build + import K8s
docker build -t kapitalya/findemproai:v$(Get-Date -Format "yyyyMMdd") .
docker save kapitalya/findemproai:vYYYYMMDD -o findemproai.tar
docker exec -i desktop-worker4 ctr images import - < findemproai.tar
Remove-Item findemproai.tar
```

**Nota K8s:** init container ejecuta `collectstatic` antes del pod principal. `ALLOWED_HOSTS` incluye `*` para que las probes K8s funcionen con IPs de pod.

---

## Desarrollo local

```bash
# Con Docker Compose
make deploy    # build + up + migrate + collectstatic + health check

# Comandos operacionales
make up        # Levantar servicios
make down      # Detener servicios
make logs      # Logs en tiempo real
make migrate   # Ejecutar migraciones
make test      # Ejecutar 251 tests
make health    # Verificar health check

# Sin Docker
cd findempro
python -m venv venv && venv\Scripts\activate
pip install -r requirements/development.txt
python manage.py migrate --settings=findempro.settings.development
python manage.py runserver --settings=findempro.settings.development

# Celery en terminal separada
celery -A findempro worker --loglevel=info
```

---

## Tests

**Suite completa en verde: 581 tests, 0 fallos, 2 skips justificados** (todas las apps).
Antes, `pytest` fallaba con 27 errores de colección (imports rotos); hoy corre limpio.

| Área | Suite |
|------|-------|
| Motor MC / eventos discretos / métricas | `simulate/tests/` (374) |
| Hub SSO — JWT + open redirect | `hub_auth/tests.py` (13) |
| Seguridad — validador anti-RCE de ecuaciones | `variable/tests/test_security.py` (18) |
| Negocio / producto / variable / finanzas | `business`, `product`, `variable`, `finance` |
| Usuarios / dashboards / cuestionarios / reportes | `user`, `dashboards`, `questionary`, `report` |
| Core (auth allauth, health) | `findempro/tests/` |

```bash
# Suite completa (rápida, aislada en SQLite)
python -m pytest

# Solo el motor + seguridad
python -m pytest simulate/tests/ hub_auth/ variable/tests/test_security.py -v

# Con cobertura
python -m pytest --cov=simulate --cov=hub_auth --cov-report=html

# CI con PostgreSQL (mayor fidelidad)
USE_POSTGRES_TESTS=1 DB_ENGINE=django.db.backends.postgresql python -m pytest
```

Los 2 `skip` están justificados en el propio test: `solve_equation` renderiza un template
de UI que nunca se creó, y la generación de PDF migró a tarea async de Celery (requiere broker).

---

## Conexiones con otros servicios

| Servicio | Uso |
|---------|-----|
| PostgreSQL namespace `databases` | Base de datos principal |
| Redis namespace `databases` | Cache + broker Celery |
| Celery workers (3 pods) | Simulaciones largas + análisis de sensibilidad |
| Nginx pod | Sirve archivos estáticos (WhiteNoise alternativo) |

---

## Seguridad

- `SECRET_KEY`: fail-fast — `RuntimeError` si no está definida en el entorno
- **CORS:** variable `CORS_ALLOWED_ORIGINS` (django-cors-headers)
- **Autenticación:** Django Allauth + Sanctum; OAuth2 Google disponible
- **Rate limiting:** DRF throttling en endpoints de simulación
- **Logs:** JSON estructurado con `python-json-logger` (sin datos sensibles)
- **Sentry:** captura de errores en producción con `SENTRY_DSN`
- **Dockerfile:** imagen final mínima, usuario no root, sin dev-dependencies

---

## Integración Hub SSO

Integrado con [Kapitalya Hub](https://kapitalya.com.bo) — un solo login para todo el ecosistema.

**Flujo:** Hub emite `project_token` (5 min) → redirect `?hub_token=XXX` → `HubAuthMiddleware` valida y crea sesión local sin segundo login.

| Variable | Descripción |
|----------|-------------|
| `HUB_JWT_SECRET` | Secret compartido — debe ser IDÉNTICO en todos los proyectos |
| `PROYECTO_SLUG` | `findemproai` — identificador del proyecto en el Hub |

**Archivos:** `findempro/hub_auth/tokens.py` · `findempro/hub_auth/middleware.py`
