# FindemproAI — Sistema de Apoyo a Decisiones Financieras para PYMES

> **Sistema web de simulación probabilística y análisis financiero** para pequeñas y medianas empresas del sector productivo. Apoya la toma de decisiones basándose en el comportamiento histórico de la demanda usando funciones de densidad de probabilidad y simulación Monte Carlo.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2.11-green)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.15-orange)](https://www.django-rest-framework.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Version](https://img.shields.io/badge/Version-3.0.0-purple)](package.json)

---

## Índice

- [Descripción del Sistema](#descripción-del-sistema)
- [Problema que Resuelve](#problema-que-resuelve)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Tecnologías Utilizadas](#tecnologías-utilizadas)
- [Instalación Local](#instalación-local)
- [Variables de Entorno](#variables-de-entorno)
- [Flujo de Trabajo de Desarrollo](#flujo-de-trabajo-de-desarrollo)
- [Uso del Sistema](#uso-del-sistema)
- [Modelos Matemáticos](#modelos-matemáticos)
- [Simulación Monte Carlo](#simulación-monte-carlo)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [API REST](#api-rest)
- [Roadmap](#roadmap)
- [Autor](#autor)

---

## Descripción del Sistema

**FindemproAI** es una plataforma web que permite a las PYMES:

1. **Registrar su negocio** y productos con variables de demanda históricas.
2. **Ajustar distribuciones de probabilidad** a su comportamiento de demanda (Normal, Log-Normal, Gamma, Exponencial, Uniforme).
3. **Ejecutar simulaciones Monte Carlo** para proyectar demanda futura bajo múltiples escenarios (pesimista / base / optimista).
4. **Obtener análisis financieros automáticos**: márgenes, punto de equilibrio, VaR, CVaR, ROI.
5. **Recibir recomendaciones priorizadas** basadas en umbrales y métricas financieras.
6. **Visualizar resultados** mediante dashboards interactivos con gráficos estadísticos.

### Nivel técnico

- Backend en **Django 4.2** con REST API (DRF + Swagger).
- Motor de simulación en **NumPy / SciPy / Statsmodels**.
- Tareas asíncronas con **Celery + Redis**.
- Autenticación con **Django-AllAuth + Google OAuth2**.
- Despliegue en **Docker + Gunicorn + Nginx + PostgreSQL**.

---

## Problema que Resuelve

Las PYMES del sector productivo (lácteo, agroindustrial, manufacturero) toman decisiones financieras basadas en intuición o datos históricos simples, sin considerar:

- La **incertidumbre inherente** de la demanda.
- El **riesgo financiero** bajo distintos escenarios.
- El **comportamiento estadístico** de sus variables clave.

FindemproAI transforma datos históricos de demanda en **proyecciones cuantificadas con intervalos de confianza**, permitiendo que los gerentes evalúen el riesgo antes de invertir, comprar inventario o cambiar precios.

---

## Arquitectura del Sistema

```
┌────────────────────────────────────────────────────────────────┐
│                        CLIENTE (Browser)                       │
│              Bootstrap 5 + ApexCharts + Chart.js               │
└─────────────────────────────┬──────────────────────────────────┘
                              │ HTTP/HTTPS
┌─────────────────────────────▼──────────────────────────────────┐
│                    NGINX (Reverse Proxy)                        │
│              Static files + SSL termination                     │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│               GUNICORN (WSGI Application Server)               │
│                    findempro Django App                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ business │  │ product  │  │ simulate │  │   finance    │  │
│  │   app    │  │   app    │  │   app    │  │     app      │  │
│  └──────────┘  └──────────┘  └─────┬────┘  └──────────────┘  │
│                                     │                          │
│  ┌─────────────────────────────────▼─────────────────────────┐│
│  │              SIMULATION SERVICES LAYER                     ││
│  │  MonteCarloEngine │ DemandModelService │ FinancialAnalysis ││
│  └────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────┘
         │                        │                    │
┌────────▼──────┐      ┌──────────▼──────┐   ┌────────▼────────┐
│  PostgreSQL   │      │  Redis Cache    │   │  Celery Worker  │
│  (Datos)      │      │  + Sessions     │   │  (Async Tasks)  │
└───────────────┘      └─────────────────┘   └─────────────────┘
```

### Flujo de datos principal

```
Datos históricos de demanda
        │
        ▼
Ajuste de distribución de probabilidad (SciPy - KS test)
        │
        ▼
Motor Monte Carlo (10,000+ iteraciones)
        │
        ▼
Métricas financieras + Análisis de riesgo (VaR, CVaR)
        │
        ▼
Recomendaciones automáticas por severidad
        │
        ▼
Dashboard interactivo + Reportes exportables
```

---

## Tecnologías Utilizadas

### Backend
| Tecnología | Versión | Uso |
|---|---|---|
| Python | 3.10+ | Lenguaje principal |
| Django | 4.2.11 | Framework web |
| Django REST Framework | 3.15.1 | API REST |
| Celery | 5.3.6 | Tareas asíncronas |
| NumPy | 1.26.4 | Operaciones numéricas |
| SciPy | 1.13.0 | Distribuciones estadísticas |
| Pandas | 2.2.2 | Manipulación de datos |
| Statsmodels | 0.14.1 | Análisis estadístico |
| Scikit-learn | 1.5.0 | ML auxiliar |
| SymPy | 1.12.1 | Álgebra simbólica (ecuaciones) |
| SimPy | 4.1.1 | Simulación de eventos discretos |
| Matplotlib / Seaborn | 3.8.4 / 0.13.2 | Generación de gráficos |

### Base de datos y caché
| Tecnología | Uso |
|---|---|
| PostgreSQL | Base de datos principal |
| Redis | Caché + Sessions + Broker Celery |
| psycopg2 | Driver PostgreSQL |
| hiredis | Parser Redis de alta velocidad |

### Autenticación y Seguridad
| Tecnología | Uso |
|---|---|
| Django-AllAuth | Auth completa + Social |
| Google OAuth2 | Login social |
| Django-Axes | Protección contra fuerza bruta |
| Sentry | Monitoreo de errores en producción |
| Prometheus | Métricas de rendimiento |

### Frontend
| Tecnología | Versión |
|---|---|
| Bootstrap | 5.3.0 |
| ApexCharts | 3.41.0 |
| Chart.js | 4.3.0 |
| ECharts | latest |
| SweetAlert2 | latest |
| Dropzone | latest |

---

## Instalación Local

### Prerrequisitos

- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- Node.js 16+ (para assets frontend)
- Git

### 1. Clonar el repositorio

```bash
git clone https://github.com/Serius69/FindemproAI.git
cd FindemproAI
```

### 2. Crear y activar entorno virtual

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instalar dependencias Python

```bash
pip install -r findempro/requirements/base.txt
```

### 4. Configurar variables de entorno

```bash
cp findempro/.env.example findempro/.env.development
# Editar findempro/.env.development con tus valores
```

### 5. Configurar base de datos

```bash
# Crear base de datos PostgreSQL
psql -U postgres -c "CREATE DATABASE findempro_dev;"
psql -U postgres -c "CREATE USER findempro_user WITH PASSWORD 'tu_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE findempro_dev TO findempro_user;"
```

### 6. Aplicar migraciones

```bash
cd findempro
python manage.py migrate --settings=findempro.settings.development
```

### 7. Cargar datos iniciales (opcional)

```bash
python manage.py loaddata initial_data --settings=findempro.settings.development
```

### 8. Crear superusuario

```bash
python manage.py createsuperuser --settings=findempro.settings.development
```

### 9. Recolectar archivos estáticos

```bash
python manage.py collectstatic --noinput --settings=findempro.settings.development
```

### 10. Ejecutar servidor de desarrollo

```bash
python manage.py runserver --settings=findempro.settings.development
```

Accede a: http://localhost:8000

### Usando Docker (recomendado)

```bash
# Desarrollo
docker-compose -f findempro/docker-compose.dev.yml up --build

# Producción
docker-compose -f findempro/docker-compose.prod.yml up --build -d
```

### Usando los scripts .bat (Windows)

```bat
# Configuración inicial
setup.bat

# Servidor de desarrollo
dev_start.bat

# Producción
prod_start.bat
```

---

## Variables de Entorno

Copia `.env.example` y configura las siguientes variables:

### Variables requeridas

```env
# Django
SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria
DJANGO_ENV=development

# Base de datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/findempro_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu@email.com
EMAIL_HOST_PASSWORD=tu-password-app
```

### Variables opcionales (producción)

```env
# Seguridad
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
CSRF_TRUSTED_ORIGINS=https://tudominio.com
HTTPS_ENABLED=True

# Sentry (monitoreo de errores)
SENTRY_DSN=https://tu-dsn@sentry.io/proyecto

# Google OAuth2
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=tu-client-id
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=tu-client-secret

# AWS S3 (almacenamiento de archivos en producción)
AWS_ACCESS_KEY_ID=tu-key-id
AWS_SECRET_ACCESS_KEY=tu-secret-key
AWS_STORAGE_BUCKET_NAME=tu-bucket
```

---

## Uso del Sistema

### Flujo típico de trabajo

#### 1. Registro y configuración del negocio
- Crear cuenta o iniciar sesión con Google.
- Registrar empresa: nombre, tipo de industria, descripción.
- El sistema crea automáticamente 5 distribuciones de probabilidad por defecto.

#### 2. Configurar productos y variables
- Agregar productos del negocio.
- Definir áreas de producción por producto.
- Crear variables (exógenas, de estado, endógenas) con sus unidades.
- Definir ecuaciones que relacionan variables.

#### 3. Completar cuestionario
- Responder el cuestionario sobre historial de demanda.
- Ingresar datos históricos de ventas/producción.

#### 4. Ejecutar simulación
- Seleccionar distribución de probabilidad apropiada.
- Configurar parámetros de simulación:
  - Número de iteraciones (1,000 - 100,000)
  - Nivel de confianza (80% - 99%)
  - Horizonte temporal
- Ejecutar simulación Monte Carlo.

#### 5. Analizar resultados
- Ver estadísticas descriptivas de la demanda simulada.
- Revisar análisis financiero automático.
- Evaluar escenarios: pesimista, base, optimista.
- Revisar recomendaciones priorizadas por severidad.
- Exportar reportes.

### Ejemplo de entrada/salida

**Entrada:**
```json
{
  "distribution_type": "normal",
  "demand_mean": 5000,
  "demand_std": 800,
  "unit_price": 2.50,
  "unit_cost": 1.20,
  "fixed_costs": 3000,
  "n_iterations": 10000,
  "time_periods": 12,
  "confidence_level": 0.95
}
```

**Salida (SimulationResult):**
```json
{
  "demand": {
    "mean": 5012.3,
    "std": 798.6,
    "p5": 3695.4,
    "p25": 4469.1,
    "p75": 5545.2,
    "p95": 6337.8
  },
  "revenue": {
    "mean": 12530.75,
    "p5": 9238.5,
    "p95": 15844.5
  },
  "profit": {
    "mean": 3280.45,
    "p5": -186.3,
    "p95": 6591.2
  },
  "risk": {
    "probability_of_loss": 0.034,
    "var_95": -186.3,
    "expected_shortfall": -420.7
  },
  "scenarios": {
    "pessimistic": {"demand": 3695, "profit": -186, "margin": -1.5},
    "base": {"demand": 5012, "profit": 3280, "margin": 26.2},
    "optimistic": {"demand": 6338, "profit": 6591, "margin": 41.6}
  }
}
```

---

## Modelos Matemáticos

### Distribuciones de Probabilidad Implementadas

El sistema ajusta distribuciones estadísticas a los datos históricos de demanda usando el **test de Kolmogorov-Smirnov** para seleccionar el mejor ajuste.

#### 1. Distribución Normal
Apropiada cuando la demanda fluctúa simétricamente alrededor de un promedio estable.

```
f(x | μ, σ) = (1 / (σ√(2π))) · exp(-(x-μ)² / (2σ²))
```
- **μ (mu):** demanda promedio
- **σ (sigma):** desviación estándar

#### 2. Distribución Log-Normal
Cuando la demanda es siempre positiva y tiene sesgo positivo (típico en productos estacionales).

```
f(x | μ, σ) = (1 / (xσ√(2π))) · exp(-(ln(x)-μ)² / (2σ²))
```

#### 3. Distribución Gamma
Modela tiempos de espera o acumulación de demanda con variabilidad positiva.

```
f(x | k, θ) = x^(k-1) · exp(-x/θ) / (θ^k · Γ(k))
```
- **k:** parámetro de forma
- **θ:** parámetro de escala

#### 4. Distribución Exponencial
Demanda con patrón de llegadas aleatorias (ej: pedidos esporádicos).

```
f(x | λ) = λ · exp(-λx)
```
- **λ (lambda):** tasa de ocurrencia

#### 5. Distribución Uniforme
Cuando no hay información suficiente o la demanda varía aleatoriamente en un rango definido.

```
f(x | a, b) = 1 / (b - a), para a ≤ x ≤ b
```

### Métricas de Evaluación del Ajuste

| Métrica | Descripción |
|---|---|
| KS statistic | Distancia máxima entre distribución empírica y teórica |
| p-value | Probabilidad de aceptar H₀ (buen ajuste) |
| AIC / BIC | Criterios de información para selección de modelo |

---

## Simulación Monte Carlo

### Algoritmo

```python
for i in range(n_iterations):
    # 1. Muestrear demanda aleatoria de la distribución ajustada
    demand = distribution.rvs(size=time_periods)
    
    # 2. Aplicar factores de estacionalidad
    demand *= seasonality_factors
    
    # 3. Calcular ingresos y costos
    revenue = demand * unit_price
    variable_costs = demand * unit_cost
    total_costs = variable_costs + fixed_costs
    
    # 4. Calcular utilidad
    profit = revenue - total_costs
    
    # 5. Almacenar resultados
    results[i] = (demand.sum(), revenue.sum(), profit.sum())

# Calcular estadísticas sobre las 10,000 simulaciones
```

### Métricas de Riesgo Calculadas

| Métrica | Fórmula | Interpretación |
|---|---|---|
| **VaR 95%** | Percentil 5 de utilidades | Pérdida máxima esperada el 95% del tiempo |
| **CVaR (Expected Shortfall)** | Media de pérdidas > VaR | Pérdida esperada en el peor 5% de escenarios |
| **Prob. Pérdida** | P(utilidad < 0) | Probabilidad de no ser rentable |
| **Prob. Punto de Equilibrio** | P(utilidad ≥ 0) | Probabilidad de cubrir costos |
| **Coef. Variación** | σ/μ | Variabilidad relativa de la demanda |

### Análisis de Escenarios

| Escenario | Percentil de Demanda | Descripción |
|---|---|---|
| Pesimista | P5 | El 5% de los peores casos |
| Conservador | P25 | Cuartil inferior |
| Base | P50 (mediana) | Caso más probable |
| Optimista | P75 | Cuartil superior |
| Muy optimista | P95 | El 5% de los mejores casos |

---

## Estructura del Proyecto

```
FindemproAI/
├── findempro/                      # Raíz del proyecto Django
│   ├── findempro/                  # Configuración principal
│   │   ├── settings/
│   │   │   ├── base.py             # Configuración compartida
│   │   │   ├── development.py      # Entorno local
│   │   │   ├── production.py       # Entorno producción
│   │   │   └── staging.py          # Entorno staging
│   │   ├── celery.py               # Configuración Celery
│   │   ├── urls.py                 # URLs raíz
│   │   ├── health.py               # Health checks
│   │   └── wsgi.py                 # Punto de entrada WSGI
│   │
│   ├── business/                   # App: Gestión de empresas
│   │   ├── models.py               # Business, CompanyProfile
│   │   ├── views.py                # CRUD empresas
│   │   └── migrations/
│   │
│   ├── product/                    # App: Productos y áreas
│   │   ├── models.py               # Product, Area
│   │   └── ...
│   │
│   ├── variable/                   # App: Variables y ecuaciones
│   │   ├── models.py               # Variable, Equation, EquationResult
│   │   └── ...
│   │
│   ├── simulate/                   # App: Motor de simulación (CORE)
│   │   ├── models.py               # PDF, Simulation, Result, Demand
│   │   ├── services/               # Capa de servicios (lógica de negocio)
│   │   │   ├── simulation_engine.py    # Motor Monte Carlo
│   │   │   ├── demand_model.py         # Análisis y pronóstico de demanda
│   │   │   ├── financial_analysis.py   # Análisis financiero y riesgo
│   │   │   ├── statistical_service.py  # Estadísticas auxiliares
│   │   │   ├── chart_service.py        # Generación de gráficos
│   │   │   └── validation_service.py   # Validaciones de entrada
│   │   ├── views/
│   │   │   ├── api_v1_views.py     # REST API v1
│   │   │   ├── simulate_init_view.py   # Inicialización simulación
│   │   │   ├── simulate_list_view.py   # Listado simulaciones
│   │   │   └── simulate_result_view.py # Resultados y análisis
│   │   └── tests/
│   │       └── test_math_engine.py  # Tests matemáticos
│   │
│   ├── finance/                    # App: Decisiones financieras
│   │   ├── models.py               # FinancialDecision, Recommendations
│   │   └── ...
│   │
│   ├── dashboards/                 # App: Visualizaciones
│   │   ├── models.py               # Chart, ChartTemplate
│   │   ├── services/
│   │   │   └── dashboard_service.py
│   │   └── ...
│   │
│   ├── questionary/                # App: Cuestionarios de diagnóstico
│   ├── report/                     # App: Generación de reportes
│   ├── user/                       # App: Gestión de usuarios
│   ├── pages/                      # App: Páginas estáticas/landing
│   │
│   ├── templates/                  # Plantillas HTML (Django templates)
│   ├── static/                     # Archivos estáticos compilados
│   ├── src/                        # Fuentes frontend (SCSS, JS)
│   ├── media/                      # Archivos subidos por usuarios
│   ├── logs/                       # Logs de aplicación
│   ├── nginx/                      # Configuración Nginx
│   ├── scripts/                    # Scripts de utilidad
│   │
│   ├── requirements/
│   │   └── base.txt                # Dependencias Python
│   ├── manage.py
│   ├── Dockerfile
│   ├── docker-compose.dev.yml
│   ├── docker-compose.prod.yml
│   ├── gunicorn.conf.py
│   └── .env.example
│
├── README.md                       # Este archivo
├── dev_start.bat                   # Script inicio desarrollo (Windows)
├── prod_start.bat                  # Script inicio producción (Windows)
└── setup.bat                       # Script configuración inicial (Windows)
```

---

## API REST

La API REST está disponible en `/api/v1/` con documentación automática.

### Documentación interactiva

- **Swagger UI:** `http://localhost:8000/swagger/`
- **ReDoc:** `http://localhost:8000/redoc/`

### Endpoints principales

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/health/` | Health check general |
| `GET` | `/health/ready/` | Readiness check |
| `GET` | `/health/live/` | Liveness check |
| `GET/POST` | `/business/` | Listar / crear empresas |
| `GET/PUT/DELETE` | `/business/<id>/` | Detalle empresa |
| `GET/POST` | `/product/` | Listar / crear productos |
| `GET/POST` | `/simulate/` | Listar / iniciar simulaciones |
| `GET` | `/simulate/<id>/results/` | Resultados de simulación |
| `GET` | `/simulate/api/v1/results/` | API v1 resultados |

### Autenticación de API

```bash
# Obtener token
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "usuario", "password": "contraseña"}'

# Usar token
curl http://localhost:8000/simulate/ \
  -H "Authorization: Bearer <token>"
```

### Límites de tasa (Rate limiting)

| Tipo de usuario | Límite |
|---|---|
| Anónimo | 100 requests/hora |
| Autenticado | 1,000 requests/hora |

---

## Roadmap

### v3.1 (Próxima versión)
- [ ] Exportación de reportes en PDF y Excel
- [ ] Notificaciones en tiempo real (WebSockets / Django Channels)
- [ ] Dashboard de comparación entre múltiples simulaciones
- [ ] API pública documentada con versioning

### v3.2
- [ ] Integración con fuentes de datos externas (INEI, bancos de datos sectoriales)
- [ ] Modelos de pronóstico ARIMA / SARIMA para series temporales
- [ ] Análisis de correlación entre variables de diferentes productos
- [ ] Módulo de planificación de inventario (EOQ, Safety Stock)

### v4.0 (Largo plazo)
- [ ] Motor de IA para selección automática de distribución óptima
- [ ] Integración con ERP (SAP, Odoo)
- [ ] App móvil (React Native)
- [ ] Multi-tenancy para grupos empresariales
- [ ] Benchmarking sectorial anonimizado

---

## Contribuir

```bash
# Fork + Clone
git clone https://github.com/Serius69/FindemproAI.git

# Crear rama feature
git checkout -b feature/nombre-feature

# Ejecutar tests
cd findempro
python manage.py test --settings=findempro.settings.development

# Pull Request con descripción clara
```

### Tests

```bash
# Todos los tests
python manage.py test --settings=findempro.settings.development

# Solo tests del motor matemático
python manage.py test simulate.tests.test_math_engine --settings=findempro.settings.development

# Con cobertura
coverage run manage.py test
coverage report
coverage html
```

---

---

## Flujo de Trabajo de Desarrollo

### 1. Clonar el proyecto

```bash
git clone https://github.com/Serius69/FindemproAI.git
cd FindemproAI
```

### 2. Configurar el entorno (primera vez)

```bat
setup.bat
```

Este script realiza automáticamente:
- Crea el entorno virtual `venv/`
- Instala dependencias desde `requirements/base.txt`
- Crea `findempro/.env.development` desde `.env.example`
- Aplica migraciones de la base de datos
- Verifica la configuración Django

> **Importante:** Edita `findempro/.env.development` con tus credenciales reales antes de continuar.

### 3. Iniciar el servidor de desarrollo

```bat
dev_start.bat
```

Disponible en:
- App: `http://127.0.0.1:8000`
- Admin: `http://127.0.0.1:8000/admin/`
- Swagger: `http://127.0.0.1:8000/swagger/`

### 4. Trabajar con Git — Convención de Commits

Este proyecto usa **Conventional Commits**. El hook `commit-msg` valida el formato automáticamente.

**Formato:**
```
<tipo>(<scope>): <descripción corta en imperativo>
```

**Tipos válidos:**

| Tipo | Cuándo usarlo |
|------|--------------|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Cambios en documentación |
| `style` | Formato, espacios (sin cambio de lógica) |
| `refactor` | Refactorización sin nuevo comportamiento |
| `test` | Agregar o corregir tests |
| `chore` | Mantenimiento, dependencias, configuración |
| `perf` | Mejora de rendimiento |
| `ci` | Cambios en CI/CD |

**Ejemplos correctos:**
```bash
feat(simulate): agregar simulación Monte Carlo para empresas PYME
fix(business): corregir validación de NIT duplicado en formulario
refactor(finance): extraer cálculo de VAN a función separada
docs: actualizar README con flujo de trabajo Git
chore: actualizar dependencias de seguridad
test(product): agregar tests unitarios para modelo de demanda
```

**Ejemplos incorrectos:**
```bash
cambios varios          # sin tipo
FIX bug                 # tipo en mayúsculas
feat: x                 # descripción muy corta
```

### 5. Flujo diario de trabajo

```bash
# 1. Actualizar rama local
git pull origin main

# 2. Crear rama para tu feature/fix
git checkout -b feat/nombre-descriptivo
# o para bugs:
git checkout -b fix/descripcion-del-bug

# 3. Hacer cambios y limpiar antes de commitear
clean.bat

# 4. Stagear solo lo relevante (NUNCA git add .)
git add findempro/modulo/archivo.py
git add findempro/modulo/tests.py

# 5. Commit con formato correcto
git commit -m "feat(modulo): descripción clara del cambio"

# 6. Push y Pull Request
git push origin feat/nombre-descriptivo
```

### 6. Comandos de mantenimiento

```bat
clean.bat      # Elimina __pycache__, .pyc, logs, staticfiles generados
setup.bat      # Configura el entorno desde cero
dev_start.bat  # Inicia servidor de desarrollo
prod_start.bat # Inicia servidor de producción con Gunicorn
```

### 7. Buenas prácticas del equipo

| Regla | Detalle |
|-------|---------|
| **Nunca** `git add .` | Usar `git add <archivo>` para control exacto |
| **Nunca** commitear `.env` real | Solo `.env.example` va al repo |
| **Nunca** commitear `venv/` o `node_modules/` | Están en `.gitignore` |
| **Siempre** branch por feature | `feat/`, `fix/`, `refactor/`, `docs/` |
| **Siempre** PR hacia `main` | No pushear directo a `main` |
| **Siempre** ejecutar `clean.bat` antes de commit | Evita subir basura |

### 8. Variables de entorno por ambiente

| Archivo | Propósito | En repo |
|---------|-----------|---------|
| `.env.example` | Plantilla sin credenciales | ✅ Sí |
| `.env.development` | Config local de desarrollo | ❌ No |
| `.env.production` | Config de producción | ❌ No |
| `.env.staging` | Config de staging | ❌ No |

Siempre copia desde `.env.example`:
```bash
cp findempro/.env.example findempro/.env.development
# Luego edita con tus valores reales
```

### 9. Verificar estado del repositorio

```bash
git status          # ver cambios pendientes
git diff            # ver diferencias en detalle
git log --oneline   # historial de commits
git stash           # guardar cambios temporalmente
```

---

## Autor

**Sergio Denis Troche Mayta**

- GitHub: [@Serius69](https://github.com/Serius69)
- Email: sergio.denis.troche.mayta@gmail.com

Sistema desarrollado como proyecto de titulación universitaria, enfocado en la aplicación práctica de modelos probabilísticos y simulación computacional para el apoyo a decisiones financieras en PYMES del sector productivo boliviano.

---

## Licencia

MIT License — ver [LICENSE](LICENSE) para más detalles.

---

*FindemproAI v3.0.0 — Sistema de Apoyo a Decisiones Financieras para PYMES*
