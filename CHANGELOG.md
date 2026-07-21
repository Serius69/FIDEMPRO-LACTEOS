# Changelog — FindemproAI

## [Unreleased] — 2026-07-21

### Fix crítico de login en prod — Redis con auth + email verificado
- **`docker-compose.prod.yml`**: las URLs `REDIS_URL`/`CELERY_BROKER_URL`/
  `CELERY_RESULT_BACKEND` (backend + celery + beat, 9 en total) apuntaban a
  `redis://findempro_redis:6379/N` **sin la contraseña**, mientras Redis arranca
  con `--requirepass ${REDIS_PASSWORD}`. Resultado: todo write de caché fallaba
  (fail-open silencioso) → como `SESSION_ENGINE=cache`, **no se podían crear
  sesiones** → el login reventaba con 500 (`RuntimeError: Unable to create a new
  session key`). Corregido a `redis://:${REDIS_PASSWORD}@findempro_redis:6379/N`.
- **allauth email verificado**: con `ACCOUNT_EMAIL_VERIFICATION` obligatorio, el
  login dispara el envío del correo de confirmación; con el SMTP de Gmail fallando
  (`535 BadCredentials`) eso también tiraba 500. `ensure_superuser` ahora deja el
  `EmailAddress` del superuser **primary + verified** para que el login no intente
  enviar correo.
- Verificado **end-to-end** en `https://app.kapitalya.com.bo/account/login/`:
  POST → 302, `sessionid` emitido, home autenticado 200.

### Superusuario `sergio` idempotente
- **`manage.py ensure_superuser`** (NUEVO, `business/management/commands/`): asegura
  el superuser `sergio` sin efectos colaterales — lo crea si falta (super/staff/
  activo, email allauth verificado) y, si ya existe, corrige flags **sin pisar la
  contraseña** (regla del ecosistema Kapitalya, igual que xgol/forex-erp). Defaults:
  usuario `sergio`, email `kapitalyabolivia@gmail.com`, password `Kapitalya2026!`
  (idénticos a xgol); configurables por flag o env (`FINDEMPRO_SUPERUSER*` /
  `DJANGO_SUPERUSER_PASSWORD`). Pensado para correr tras cada `migrate` en dev/
  test/prod — **siempre también en prod**.
- **Tests**: `business/tests/test_ensure_superuser.py` (5: crea, idempotente sin
  reset de password, repara flags sin tocar password, usuario/clave custom, email
  allauth verificado).
- Ejecutado en dev y en **prod** (contenedor `findempro_backend`): superuser
  `sergio` (kapitalyabolivia@gmail.com) creado, email verificado y login OK.

## [Unreleased] — 2026-07-15

### Simulación — Modo GBM elegible desde la UI
- **`Simulation.demand_distribution`** (NUEVO campo opcional, migración `simulate/
  0021`): override del proceso de demanda. Cuando el usuario elige **GBM** en el
  formulario de lanzamiento, gana sobre la FDP y sobre el modo `'auto'` del
  `CompanyProfile`; vacío (`''`) = comportamiento i.i.d. previo por FDP →
  **retrocompatibilidad total**. El branch GBM del motor (escalar + vectorizado)
  ya existía (sesión 2026-07-12); solo hubo que alimentarlo desde
  `MonteCarloConfig.from_simulation()`. Cierra el pendiente "exponer GBM en la UI".
- **Selector "Proceso de demanda"** (Automático / GBM) en el form real de
  lanzamiento (`templates/simulate/init/partials/model_summary.html`), cableado
  por `simulate_add_view` → validador (lista blanca) → `create_simulation` →
  persistencia → `from_simulation`.
- **Tests**: `simulate/tests/test_gbm_ui.py` (9: GBM activa el branch calibrado y
  gana sobre FDP/`auto`; vacío conserva i.i.d. parametrizado normal/lognormal/
  gamma/poisson; e2e por la cadena real); `simulate/` completo **422 passed**.

### Datos — Mezcla estacional (perfil sector × picos del producto) + variantes regionales
- **(b) Realce estacional mixto** en `seed_service._blended_seasonal_profile()`:
  el perfil del TIPO (`bolivia_sector_series`, media 1.0) se realza un **+10%**
  (`_PEAK_BOOST`) en los `peak_months` propios del producto y se **renormaliza a
  media 1.0**. Corrige el caso Tour Turístico (tipo 16 hotelería): jun/jul/ago
  suben de `[0.95, 0.99, 1.05]` a `[1.02, 1.06, 1.12]` — su temporada alta de
  invierno ahora es visible sobre 1.0, sin destruir la forma del sector. Sin
  `peak_months` (o sin `business_type`) → comportamiento previo intacto.
- **(c) Variantes regionales por ciudad**: `bolivia_regions.py` (NUEVO) mapea
  ciudad→región del IPC y expone `city_price_factor()` (fallback 1.0 seguro).
  `seed_bolivia --regions "El Alto,Cochabamba,Oruro,…"` (rama separada, vía
  `IndustrySeeder.seed_regional()`) siembra un negocio por (tipo × ciudad) con
  nombre sufijado — "Panadería San Jorge (El Alto)" — evitando el UNIQUE(name,
  fk_user), y escala `price`/`unit_cost` por el factor de presión de precios de
  la ciudad (de `regional_price_pressure()`, señal IPC en vivo). Mapeo: La Paz y
  El Alto → "Conurbación La Paz"; **Cochabamba → "Región Metropolitana Kanata"**
  (su conurbación real, factor 1.0128 jun-2026); Santa Cruz sin dato → 1.0.
  Degrada a 1.0 si no hay señal IPC.
- **Tests**: `test_sector_series.py` (+2 mezcla estacional) y
  `test_regional_variants.py` (NUEVO, 12: mapeo/fallback incl. Cochabamba→Kanata,
  escalado, no-colisión unique, idempotencia, e2e por el motor, comando);
  `business/` completo **90 passed**.
- **Verificación conjunta**: `business/` + `simulate/` = **512 passed**, `check`
  limpio, cero contaminación cruzada entre apps.
- **Sin commitear/desplegar todavía.**

### Validación — Smoke de simulación del catálogo COMPLETO (49/49 ✓)
- **`manage.py validate_catalog`** (NUEVO): corre el pipeline Monte Carlo real
  (`SimulationService.run_full_pipeline`) sobre **cada producto activo** del
  usuario y reporta ✓/✗ por producto con ingreso/utilidad por día. Cierra el
  hueco de `seed_bolivia --run-sim`, que solo simula 1 producto por negocio y
  únicamente los recién sembrados — nunca se había validado el catálogo entero.
  Flags `--types`, `--mc-scenarios`, `--periods`, `--keep` (por defecto las
  simulaciones de humo se eliminan). Sale con error si algo falla → usable como
  gate en CI.
- **Resultado**: los **49 productos simulan ✓** (n=100, 30 períodos), incluidos
  los 10 arquetipos micro nuevos y la serie REAL del forex (365 pts, ingreso
  Bs 778/día, utilidad Bs 73/día).
- **Bug de calibración detectado y corregido por el smoke**: "Venta de
  Medicamentos" operaba a pérdida (utilidad media Bs −15/día: margen Bs 9/ticket
  × 60/día no cubría fijos+sueldos). Recalibrado a ~95 tickets/día (escala real
  de farmacia de barrio) → utilidad Bs +249/día, re-validado.
- **Tests**: `business/tests/test_validate_catalog.py` (4: valida todos los
  productos + limpieza, `--keep`, usuario sin productos, usuario inexistente);
  `business` completo **76 passed**, `check` limpio.
- **Sin commitear/desplegar todavía.**

### Datos — Catálogo expandido con los arquetipos MICRO emblemáticos (+9)
- **9 rubros micro/PYME que faltaban** añadidos a `bolivia_industries.py`, cada
  uno en su `BusinessType` y a escala micro real (1–4 empleados, sueldos ≥
  salario mínimo Bs 2.750): **Prenda de Confección** (taller textil El Alto,
  tipo 9) · **Corte de Cabello** (belleza, 12) · **Reparación Mecánica**
  (talleres, 12) · **Lavado de Ropa** (lavandería, 12) · **Venta de
  Medicamentos** (farmacia de barrio, 13) · **Artículos de Ferretería** (10) ·
  **Venta de Puesto de Mercado** (comercio informal gremial, 10) · **Tour
  Turístico** (agencia, 16) · **Internet y Fotocopias** (punto de barrio, 7).
  Con "Cambio de Divisas" (19), el catálogo pasa de ~39 a **49 productos**.
- **Verificado end-to-end** en DB dev: 19 negocios activos (los 19 tipos) y 49
  productos con cadena completa (variables/ecuaciones/cuestionario + DH de 360
  pts vía el reader real del motor, con la estacionalidad del sector: puesto de
  mercado pico dic 110 vs media 79 — aguinaldo). La serie REAL del forex quedó
  intacta (365 pts, media 12,4).
- **Nota de diseño**: la forma de la demanda histórica sigue el perfil
  estacional del *tipo* de negocio (`bolivia_sector_series`), no los
  `peak_months` por producto — p.ej. Tour Turístico hereda el perfil hotelería.
- **Tests**: `test_catalog_includes_micro_archetypes` (existencia, tipo
  correcto y escala micro de los 10 arquetipos) + fix de
  `test_seed_single_type_builds_full_chain` (asumía el orden de productos);
  `business` completo **72 passed**, `check` limpio.
- **Sin commitear/desplegar todavía.**

### Datos — Casa de Cambio con demanda REAL (dataset forex-erp cableado)
- **Arquetipo "Cambio de Divisas"** añadido al tipo 19 (Servicios Financieros)
  en `bolivia_industries.py`, con baseline anclado al dataset real de forex-erp
  (jul-2025→jun-2026: 12,5 ops/día · ~Bs 4.325/op → comisión ~1,5% ≈ Bs 65/op ·
  CV mensual 0,21).
- **`manage.py import_forex_demand`** (NUEVO): adapta el export anonimizado de
  operaciones (`operaciones_forex_anonimizado.csv`, 4.570 ops) a la serie diaria
  de demanda del producto y la persiste donde el motor la lee (answers `DH`,
  vía `demand_import.write_series`). Flags `--metric ops|bs`, `--include-partial`,
  `--append`, `--dry-run`, `--user/--business`.
- **Desagregación honesta mes→día** (`business/services/forex_adapter.py`): el
  CSV anonimizado no trae fecha exacta (solo `mes` + `dia_semana`), así que la
  serie diaria se reconstruye preservando **exactos** los totales mensuales
  reales y repartiendo dentro del mes con la distribución REAL por día de semana
  (domingo ≈ 6% del lunes). No inventa nivel ni tendencia. Meses de borde
  parciales (<50% de las ops del mes mediano) se excluyen por defecto.
- **Verificado en vivo end-to-end**: 12 meses completos → 365 puntos diarios
  (media 12,4 ops/día), leídos por el reader real del motor
  (`_extract_demand_data`: domingos 0,97 vs 14,2 el resto — la forma semanal
  real llega a la simulación) y calibración GBM corriendo sobre la serie.
  Primera serie de demanda 100% real por-negocio en el catálogo.
- **Tests**: `business/tests/test_forex_adapter.py` (8: totales mensuales
  preservados, métrica bs, forma semanal, meses parciales, validación de CSV
  ajeno, spec 19, comando e2e vía reader del motor, hint de seed) en verde;
  `business` completo (71) sin regresión.
- **Sin commitear/desplegar todavía.**

### Datos — Estacionalidad REAL por sector (INE/BCB → calibración de demanda)
- **`business/data/bolivia_sector_series.py`** (NUEVO): perfiles estacionales
  mensuales (12 factores, media 1.0) para los 19 `BusinessType`, anclados a la
  estacionalidad económica boliviana documentada — **aguinaldo** (dic, pico de
  retail/consumo), **Todos Santos** (nov, panadería), **año escolar** (feb,
  educación), **cosecha** altiplano/valle (abr-jul, agro), **Día de la Madre**
  (may), **estación seca** (ago-oct, construcción). Helpers `seasonal_factors()`,
  `monthly_factor()`, `peak_months()`.
- **`manage.py ingest_ine_series`** (NUEVO): consolida los perfiles en
  `business/data/bolivia_sector_series.json` con **refresco en vivo best-effort**
  de INE/BCB y **fallback curado** — mismo patrón robusto que `scrape_bolivia_data`.
  Flags `--offline`, `--dry-run`, `--timeout`.
- **IPC en vivo vía WP REST API** (el INE corre WordPress): en vez del regex frágil
  sobre la home JS (que devolvía `None`), consulta
  `wp-json/wp/v2/posts?search=índice de precios al consumidor`, elige la última nota
  mensual del IPC (excluye IPM/IPP) y parsea niveles reales: **variación mensual,
  interanual (12 meses), acumulada** y **variación por ciudad** (8 regiones). Verificado
  en vivo: junio 2026 → mensual 2,15% · interanual 9,23% · acumulada 4,82% · Oruro
  3,86%, Conurbación La Paz 3,40%, etc. El % por *división* no es parseable de forma
  fiable (vive en gráficos amCharts/Excel tras JS) y queda como dato curado. El parseo
  se aisló en `_parse_ipc_note()` (puro, testeado con fixture del artículo real).
- **Calibración cableada**: `seed_service.generate_answers()` acepta
  `business_type` y `_seasonality_multiplier()` usa el perfil real del sector; el
  sembrado genera ahora un **año completo** de histórico diario (360 pts) para que
  la estacionalidad boliviana sea observable. Sustituye la onda `sin` genérica.
  Verificado: la demanda seedeada correlaciona **+0.99** con el perfil del sector
  (retail pico dic, agro cosecha, educación feb, construcción seca), confirmado
  vía el reader real del motor (`_extract_demand_data` → 360 pts, pico dic).
- **Datos vs realidad**: cierra el gap de "todos los rubros con forma real" para
  los rubros sin serie propia (la única serie real por-negocio disponible es
  forex/casa de cambio); los demás usan estacionalidad real + nivel calibrado.
- **Inflación interanual REAL en el contexto macro**: `scrape_bolivia_data` ahora
  obtiene la inflación por la misma vía WP REST (reutiliza `_fetch_ipc_wp` de
  `ingest_ine_series`) con fallback al regex legacy y al curado. Corrido en vivo:
  `bolivia_market_data.json` pasó de `inflation_annual_pct: 10.0 [fallback-curado]`
  a **`9.23 [ine-wp-rest]`** (+ detalle de la nota en `meta.ipc`), y el overlay de
  `bolivia_industries.MARKET_CONTEXT` lo propaga al sembrado automáticamente.
- **Señal regional consumible**: `bolivia_sector_series.live_ipc()` (última señal
  IPC persistida) y `regional_price_pressure()` — factor relativo de presión de
  precios por ciudad (media ≈ 1.0) derivado de la variación mensual por ciudad
  (jun-2026: Oruro 1.015 … Tarija 0.980). Es señal de un mes para sesgar
  costos/precios al expandir el catálogo por región, no un nivel calibrado.
- **Tests**: `business/tests/test_sector_series.py` (18: normalización, picos
  bolivianos, correlación serie↔perfil ×5, comando offline/dry-run, parser IPC con
  fixture real ×3, presión regional ×2, scraper WP-REST/fallback ×2) en verde;
  `business` completo (63) + `simulate/tests/test_gbm.py` (18) sin regresión.
- **Sin commitear/desplegar todavía.**

### Datos — Importador de series de demanda REALES (CSV/Excel → simulación)
- **`manage.py import_demand_series`** (NUEVO): carga series históricas de demanda
  reales desde CSV/Excel y las persiste **donde el motor las lee** — la respuesta del
  cuestionario `DH` (`'Ingrese los datos históricos de la demanda… (mínimo 30 datos).'`)
  de cada `QuestionaryResult` activo del producto. Reemplaza la demanda **sintética**
  que generaba `seed_bolivia` (ruido gaussiano), cerrando el gap "simular datos reales".
- **Formato tidy/largo** (`product,date,demand`, con `business` opcional para desambiguar)
  o **serie única** (`--product "Leche"` sin columna de producto). Soporta Excel
  (`--sheet`) y formato boliviano (`--sep ';' --decimal ','`). Ordena por fecha si existe.
- **Reemplazo correcto**: el reader (`_extract_demand_data`) recorre las answers **sin
  filtrar `is_active`** y toma la primera parseable → desactivar no basta; el modo
  `replace` (default) **elimina** las answers `DH` previas antes de insertar la real.
  Modo `--append` antepone la serie previa.
- **Validación alineada al motor**: descarta NaN/inf/negativos (igual que
  `_validate_and_clean_demand_data`) y advierte por debajo de los umbrales de calibración
  (2 duro / 10 ajuste de distribución / 30 recomendado). Flags `--dry-run`, `--strict`,
  `--user`, `--business`.
- **Lógica testeable** en `business/services/demand_import.py` (carga, agrupación,
  resolución de producto, escritura transaccional). **Tests**:
  `business/tests/test_import_demand_series.py` (12 casos: limpieza, agrupación,
  reemplazo de la sintética verificado vía el reader real del motor, append, dry-run,
  comando end-to-end) en verde; `test_seed_bolivia.py` (8) sin regresión.
- **Alcance**: importa a productos que ya existen (onboarding o `seed_bolivia`); no crea
  productos/cuestionarios. Sin commitear/desplegar todavía.

## [Unreleased] — 2026-07-10

### Datos — Sembrado multi-industria boliviano (los 19 tipos de empresa, listos para simular)
- **Cobertura de los 19 `BusinessType`** (antes sólo lácteos, `type=1`, hardcodeado).
  Catálogo `business/data/bolivia_industries.py`: 19 industrias × 39 productos con
  precio, costo, demanda, empleados, costos fijos y estacionalidad **anclados en datos
  reales del mercado boliviano 2024-2025** (salario mín. Bs 2.750, inflación ~10 %,
  FX Bs 6,96 oficial; leche 7,5/L, queso 42/kg, pan 0,6/u, carne 60/kg, cemento 60/bolsa,
  colegio privado 900/mes, hora dev 120…). Fuentes: INE, BCB, SEPREC, prensa.
- **Reutiliza el motor validado**: el sembrado no reinventa el modelo — usa la misma
  estructura de 181 variables / 91 ecuaciones / 14 áreas por producto (helpers del
  onboarding) y sólo **parametriza los valores económicos** por industria. El motor ya
  era genérico (ingresos/costos/inventario/márgenes); sólo era "lácteo" en sus ejemplos.
- **`generate_answers()`**: genera las respuestas del cuestionario (42 preguntas) desde
  el baseline de cada producto, incluido un **histórico de demanda ≥ 30 puntos** con
  estacionalidad y ruido → simulaciones que corren para cualquier industria.
- **`manage.py seed_bolivia`**: siembra idempotente (usuario demo `demo_bolivia`), con
  flags `--types`, `--user`, `--run-sim`, `--force`. Generaliza el onboarding lácteo.
- **Onboarding web con selector de rubro**: la pantalla `register-elements/` ahora ofrece
  un `<select>` con los 19 tipos; el POST (`register_elements_create`) rutea al
  `IndustrySeeder` del tipo elegido (mismo camino que el comando) y cae al flujo lácteo
  legacy si no se elige tipo. Un usuario puede crear un negocio por rubro.
- **`manage.py scrape_bolivia_data`**: scraper best-effort de BCB (tipo de cambio) e INE
  (inflación anual) → `bolivia_market_data.json`, que se superpone sobre `MARKET_CONTEXT`.
  Con **fallback curado** si una fuente cae (el pipeline nunca se rompe).
- **Calibración de rentabilidad por línea**: la simulación corre un producto a la vez,
  pero cada producto cargaba el overhead de **todo** el negocio (salarios de 15-25
  empleados) → 10 de 19 tipos simulaban en pérdida. Se recalibró el overhead de cada
  `ProductBaseline` (`employees`/`monthly_salaries`/`daily_fixed_cost`/`marketing_monthly`)
  a la carga de **esa línea** (costo fijo ≈ 66 % del margen bruto, tope 18 empleados).
  Ahora los **19 tipos simulan utilidad positiva** con márgenes netos realistas por sector
  (commodity ~4-6 %, retail/comida 10-16 %, servicios/software/educación 17-22 %).
  **Precios, costos y demandas no se tocaron.**
- **Fix `--force`**: recrear un tipo ya sembrado (o tras una corrida parcial) lanzaba
  `IntegrityError UNIQUE(name, fk_user)` — `seed_business(force=True)` creaba un duplicado
  sin liberar el nombre (el índice es NOCASE y el modelo title-casea al guardar). Ahora
  renombra+desactiva el previo (match `name__iexact`) antes de recrear.
- **Tests**: `business/tests/test_seed_bolivia.py` (catálogo 19 tipos, forma de
  respuestas, cadena completa, idempotencia, `--force` sin choque UNIQUE, y pipeline
  Monte Carlo end-to-end `slow` con **ingreso y utilidad positivos**).
- **Verificado** (Monte Carlo sobre los 19 tipos sembrados): 19 ingresos distintos y
  utilidad diaria positiva en todos (lácteos +Bs 5.566, colegio +6.711, fideos +753,
  cemento +712, restaurante +640…). Doc: `findempro/docs/SEED_BOLIVIA.md`.

## [Unreleased] — 2026-07-08

### Rendimiento — Motor Monte Carlo vectorizado con GPU (CuPy) y fallback CPU
- **Vectorización del motor Monte Carlo**: el pipeline reemplaza el bucle Python
  `for período: for escenario: engine.run_period(...)` (hasta millones de iteraciones
  objeto-por-objeto) por operaciones de array sobre toda la grilla T×N. Válido porque
  cada escenario corre *stateless* (`reset_state()`). **~1.000–2.000× más rápido** que
  el bucle anterior; **equivalencia numérica exacta** validada por celda.
- **Backend GPU/CPU seleccionable** (`simulate/core/gpu_backend.py`): usa **CuPy (GPU)**
  cuando hay una GPU compatible y **cae automáticamente a NumPy (CPU)** si no. Detección
  segura (probe de kernel), memoizada. Flags `FINDEMPRO_GPU` (auto|on|off) y
  `FINDEMPRO_MC_ENGINE` (vectorized|scalar).
- **Motor vectorizado** (`simulate/core/vectorized_engine.py`): evalúa las MISMAS
  ecuaciones de negocio con variables array-valuadas; `can_vectorize()` valida contra el
  motor escalar antes de usarlo y cae al escalar ante cualquier divergencia.
- **GPU adicional**: ~3× end-to-end (hasta ~70× en cómputo puro) en una RTX 5070 Ti
  (Blackwell). Requiere NVRTC ≥ 12.8 (fijado en `requirements/gpu.txt`).
- **Deploy**: imagen CPU K8s reconstruida a `v20260708` (drift `:latest` del worker
  corregido); `Dockerfile.gpu` + `docker-compose.gpu.yml` + `docs/GPU_DEPLOY.md` para un
  worker GPU opcional en host Linux (el cluster Docker Desktop/Windows no expone GPU).
- **Tests**: `simulate/tests/test_vectorized_engine.py` (equivalencia, backend, 6 distribuciones).
- **Higiene**: corregidos comentarios engañosos que mencionaban "TensorFlow inference"
  (el motor real es Monte Carlo numpy/CuPy) en `throttles.py`, `settings/base.py`,
  `api_v1_views.py`.

## [Unreleased] — 2026-07-07

### Rendimiento, higiene y supply-chain (última tanda)
- **Índices DB compuestos** en los patrones calientes: `Variable(fk_product, is_active)`,
  `Equation(fk_area, is_active)`, y en `questionary` (`Questionary`, `QuestionaryResult`,
  `Question`, `Answer`). Migraciones `variable/0006` y `questionary/0005`.
- **SRI (Subresource Integrity)** añadido a los 12 recursos CDN pinneados (jQuery, Bootstrap,
  Chart.js 3.9.1, DataTables, Prism, jsPDF, html2canvas, Dropzone) con `crossorigin="anonymous"`;
  hashes `sha384` verificados contra los bytes reales del CDN. *(Pendiente: pinnear + SRI los
  no versionados —chart.js/apexcharts/sweetalert2@11/d3 v7— requiere cambio de versión y prueba
  en navegador.)*
- **`print()` → `logging`** en `variable/views.py` (14 ocurrencias en bloques except).
- **Limpieza:** eliminados `__pycache__`, `.coverage`, `db_test.sqlite3`, `data.json` (dump
  2023 sin referencias) y `findempro_dev` (artefacto de 0 bytes); `.gitignore` ampliado.
- **Tests reproducibles:** `pytest-mock`, `parameterized`, `beautifulsoup4` añadidos a
  `requirements/development.txt` (los usaban los tests pero no estaban declarados).

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
