# Changelog — FindemproAI

## [Unreleased] — 2026-07-07

### Seguridad
- **RCE eliminado** en `variable/views.py::solve_equation`: se reemplazó `eval()` sobre
  entrada del usuario por `sympy.parse_expr` con espacio de nombres restringido a `{x}`,
  y se añadió `@login_required`.
- **Open redirect corregido** en el SSO del Hub (`hub_auth/middleware.py`): el parámetro
  `next` ahora se valida con `url_has_allowed_host_and_scheme` (solo rutas internas).
- **XSS corregido** en el frontend: `static/js/model_canvas.js` (tooltip y equation-view
  ahora escapan todos los datos de nodo) y `templates/simulate/result/tabs/validation-tab.html`
  (se sustituyó `{{ var_data|safe }}` dentro de un `onclick` por `json_script` + `escapejs`).
- **Fuerza bruta**: se activó `django-axes` (5 intentos, bloqueo 1 h por IP+usuario;
  configurable por env, deshabilitado en tests).

### Tests e infraestructura
- Suite de `simulate` **374 tests en verde** (antes: 27 errores de colección + fallos).
- Aislamiento de DB en tests: `settings/testing.py` fuerza SQLite salvo `USE_POSTGRES_TESTS=1`.
- `pytest.ini`: `--import-mode=importlib` (resuelve colisiones de nombres entre apps) y
  `--strict-markers`.
- Corregidos imports rotos (`findempro.<app>` → `<app>`) en 9 archivos de test.
- Reescritos `simulate/tests/test_models.py`, `test_views.py`, `test_forms.py` al esquema vigente.
- **Nueva cobertura de `hub_auth`** (13 tests): validación JWT (exp, alg none, emisor, tipo)
  y protección de open redirect del middleware.
- `finance/forms.py` saneado (referenciaba modelos inexistentes que rompían la importación)
  y `FinanceRecommendationForm` implementado.

### Corrección de bug
- `DemandModelService.to_simulation_params()` ahora expone `distribution_type` (clave que
  consume `SimulationConfig`); se conserva `distribution` como alias.

### Suite completa en verde + bugs de producción descubiertos por los tests
Al alinear ~124 tests legacy de todas las apps al esquema vigente (antes fallaban en la
colección), la suite pasó de **27 errores de colección** a **581 tests, 0 fallos**. En el
proceso se corrigieron bugs reales de producción:

- **Seguridad — vistas sin autenticación:** `AppsView` (`/simulate/`) y todas las vistas de
  `variable` (`variable_list`, `variable_overview`, CRUD de variables/ecuaciones) usaban
  `request.user` sin `@login_required`/`LoginRequiredMixin` → exposición de datos y crash con
  usuario anónimo. Añadida la protección.
- **`variable/views.py`:** `create_or_update_equation_view` llamaba `request.is_ajax()`,
  eliminado en Django 3.1+ → `AttributeError` (500) en cada POST de ecuación.
- **`business/views.py`:** `get_business_details_view` devolvía 500 en vez de 404 (no capturaba `Http404`).
- **`product/models.py` / `product/forms.py`:** propiedades `variables_count`/`equations_count`
  inexistentes referenciadas por las vistas; `AreaForm.save()` sin `return` → 500 al crear áreas.
- **`user/views.py`:** `user_list_view` usaba accesores inversos incorrectos (`business` en vez
  de `businesses`, el `related_name` real).
- **`dashboards/urls.py`:** `dashboard_admin` montado en `admin/` quedaba eclipsado por el admin
  de Django (inalcanzable); reubicado a `dashboard-admin/`.
- **`report/views.py` + templates:** acceso a `report.created_by` inexistente; `report-list.html`
  con fragmento corrupto (`TemplateSyntaxError`); creados `report-detail.html`/`report-create.html`
  que las vistas referenciaban.
- **`templates/partials/sidebar.html`** y **`templates/business/business-overview.html`:**
  namespace de URL inexistente y `image_src.url` sin imagen → 500 al renderizar.

### Frontend — XSS restante, tooling y fuga de memoria
- **XSS (`|safe` → `json_script`):** `endogenous-tab.html` (datos de variables), `area-overview.html`
  (grafo que alimenta el canvas; la vista ahora pasa el dict nativo en vez de `json.dumps`) y
  `code-register-elements.html` (6 previews) ya no inyectan JSON crudo en `<script>`.
  `areas_section.html` dejó de renderizar la expresión de ecuación del usuario con `|safe`.
- **SPA:** añadido ESLint 9 (flat config) + scripts `lint`/`typecheck`; 0 errores. Code-splitting
  con `React.lazy` (bundle inicial 783 kB → 201 kB).
- **`model_canvas.js`:** el atajo de teclado global se registraba de nuevo en cada recarga del
  diagrama causal (fuga de listeners en `document`); ahora se enlaza una sola vez con referencia
  y hay un método `destroy()` para limpieza.

### App finance conectada
- `finance` cableada en `ROOT_URLCONF` (`path('finance/', include('finance.urls'))`); se
  corrigieron dos referencias a templates inexistentes (`financial-decision-list.html` y
  `finance/modals.html`) que hacían 500 la vista de listado. Tests de vista des-omitidos.

### Secretos
- `.env.production` saneado (Gmail app password y Google OAuth secret reales → placeholders;
  producción usa K8s Secrets). `.env.example` completado con las variables nuevas (AXES_*,
  HUB_JWT_SECRET, CORS…). Checklist de rotación en `docs/SECURITY_ROTATION.md`.
  (`.gitignore` y `.dockerignore` ya excluían todos los `.env*`.)

---

## [1.0.0] — 2026-06-13

### Primer lanzamiento productivo

**Motor de simulación financiera**
- Simulación de flujo de caja bajo distintas distribuciones de probabilidad (Normal, Poisson, Exponencial, Log-normal)
- Carga de historial de demanda para calibrar parámetros automáticamente
- Generación de proyecciones en múltiples horizontes temporales (días, semanas, meses)
- Visualizaciones: histograma con PDF superpuesta, scatter plot de demanda
- Exportación de resultados a PDF

**Cuestionario inteligente**
- Formulario guiado para capturar variables clave del negocio (precio, costo, demanda histórica)
- Validaciones en tiempo real con mensajes en español boliviano
- Resultados del cuestionario vinculados a la simulación

**Gestión de negocios y productos**
- Multi-negocio: cada usuario puede gestionar varios negocios con sus productos
- Variables financieras por producto (PVP, costo unitario, margen mínimo)

**Reportes y análisis**
- Reporte de rentabilidad proyectada con semáforos de riesgo
- Panel de control con KPIs: VAN, TIR, Payback, Margen de contribución
- Historial de simulaciones por negocio

**Infraestructura**
- Django 4.2 + PostgreSQL + Redis
- K8s namespace `kapitalya`, URL: `app.kapitalya.com.bo`
- Autenticación via Kapitalya Hub SSO (JWT 5min, tokens 24h)
- Health checks en `/health/live/` y `/health/ready/`
- Prometheus metrics en `/metrics`

---

## [0.8.0] — 2026-04-15

### Beta privada

- Simulación básica Normal y Poisson
- Registro de negocios y productos
- Cuestionario de 10 preguntas
- Exportación PDF básica

---

## [0.1.0] — 2025-06-01

### Prototipo académico

- Trabajo de grado de Ingeniería Financiera
- Simulación Monte Carlo básica con demanda histórica ingresada manualmente
