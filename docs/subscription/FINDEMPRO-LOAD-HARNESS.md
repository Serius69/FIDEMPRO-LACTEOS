# Harness de capacidad DEV de Findempro

El harness canónico es `scripts/load/findempro_load_harness.py`. Está limitado por código al
host `tromay-dev`, crea una base SQLite y un broker de filesystem en `/tmp`, usa únicamente
loopback y elimina el estado al terminar salvo `--keep-state`. No conoce credenciales de PROD,
no usa Docker, Redis ni proveedores de IA.

`--organizations` significa **Organizations de pago**. `--free-ratio 3` añade tres
Organizations Free activas por cada una de pago. Los datos, usuarios, proyectos, datasets y
sesiones son sintéticos y aislados por Organization.

## Ejecución reproducible

Ejemplo S1:

```bash
./scripts/load/findempro_load_harness.py \
  --python /home/sergui/dev/venvs/findempro-py312/bin/python \
  --benchmark --label S1-25 \
  --organizations 25 --free-ratio 3 \
  --users-per-org 3 --active-users-per-org 1 \
  --projects-per-org 2 --datasets-per-project 1 \
  --dataset-size SMALL_DATASET --simulation-profile mixed \
  --simulations-per-session 4 --concurrency 12 \
  --duration 60 --warmup 5 --ramp-up 10 --think-time-ms 250 \
  --worker-concurrency 2
```

El resultado queda en `artifacts/load/<label>.json`. Los tamaños aceptados son
`SMALL_DATASET=100`, `MEDIUM_DATASET=1000` y `LARGE_ALLOWED_DATASET=10000`; también se acepta
un entero entre 1 y 10000. Los escenarios no están hardcodeados.

## Workload real ponderado

Cada usuario virtual cerrado selecciona operaciones con estos pesos base:

| Operación | Peso | Clase |
|---|---:|---|
| auth/session | 3 | INTERACTIVE_HTTP |
| Organization context, RBAC, entitlements | 8 | INTERACTIVE_HTTP |
| project list / detail / validate-write | 9 / 8 / 3 | INTERACTIVE_HTTP |
| dataset preview | 5 | DATASET_IMPORT |
| scenario configuration | 4 | INTERACTIVE_HTTP |
| simulation submit / status | 16 / 14 | SIMULATION_SUBMIT / SIMULATION_STATUS |
| result/dashboard views | 10 | INTERACTIVE_HTTP |
| usage/metering read | 5 | INTERACTIVE_HTTP |
| cross-tenant read/write/job probes | 2 | SECURITY |
| AI determinista local | 1 | AI |

Dataset import (+1), export (+2), scenario comparison (+3) y carga adicional de simulación
Heavy Paid (+8) se habilitan según perfil y límites por sesión. El mix de simulaciones es 60%
small (25 iteraciones), 30% medium (250) y 10% heavy (2000). Free siempre usa small.

Perfiles:

- `FREE_PROFILE`: plan FREE, 1 usuario/proyecto/dataset y límites comerciales reales.
- `PAID_PROFILE`: plan GROWTH; 90% de las Organizations de pago del mix.
- `HEAVY_PAID_PROFILE`: plan PRO; `--heavy-paid-ratio`, 10% por defecto.

Cuotas reales usadas por el harness: FREE 1 proyecto activo, 1 dataset, 10000 filas/import,
10 simulaciones/mes, 1 export y 1 miembro; GROWTH 20/25/10000/500/150/10; PRO
100/100/10000/2000/500/25 respectivamente.

## Métricas y límites

El middleware `tenancy.load_metrics.LoadMetricsMiddleware` solo se activa mediante
`FINDEMPRO_LOAD_METRICS=1` en settings E2E. Devuelve conteo y latencia DB por request. El
harness captura requests, RPS, percentiles, errores, CPU/RAM de server+workers, queries,
slow queries, locks detectables, cola, lifecycle de simulación, ingest/export, metering,
seguridad, almacenamiento, timeouts y reinicios.

Limitaciones deliberadas:

- PostgreSQL, Redis, conexiones DB y WSGI de producción: `NOT_MEASURABLE` en esta corrida.
- El broker filesystem valida el lifecycle Celery, no representa capacidad Redis externa.
- IA externa: `REAL_AI_CAPACITY=NOT_MEASURABLE`; el stub no hace red.
- Cliente y servidor comparten host; CPU/RAM reportados son de server+workers.
- Los tests cerrados ejercitan tantas Organizations simultáneas como `--concurrency`; el resto
  queda aprovisionado. La distribución real de usuarios activos sigue siendo `ASSUMPTION`.

## Safety guards

El preflight rechaza host distinto de `tromay-dev`, RAM disponible menor al guard, más de 2500
Organizations totales por defecto y tiers exploratorios con menos de 512 MB de swap libre.
Un fallo de aislamiento tenant, corrupción, crash o cola sin drenar hace fallar la corrida.
