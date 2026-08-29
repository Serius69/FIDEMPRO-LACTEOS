# Usage y resource metering

## Ledgers

`UsageEvent` y `ResourceUsage` son organization-scoped y append-only a nivel de modelo/manager.
No permiten update/delete; las FK usan PROTECT. La unicidad por Organization, métrica/recurso,
source y `correlation_id` hace idempotentes los productores que pueden reintentarse.

Cada evento registra Organization, métrica/recurso, quantity, timestamp, source,
correlation_id y metadata. No se inventan dólares: `cost_amount` queda NULL y metadata declara
`COST_UNKNOWN` hasta disponer de pricing verificable.

## Instrumentación

| Flujo | UsageEvent | ResourceUsage |
|---|---|---|
| crear/importar proyecto | PROJECT_CREATED | — |
| importar dataset | DATASET_INGESTED, DATASET_ROWS, STORAGE | STORAGE bytes |
| simulación | SIMULATION_RUN, SIMULATION_RUNTIME | CPU_SIMULATION seconds, STORAGE result bytes |
| escenario | SCENARIO_RUN | incluido en runtime/result |
| export/reporte | EXPORT | — |
| Claude | AI_CALL | AI_INPUT_TOKENS, AI_OUTPUT_TOKENS |
| gate shadow | API_REQUEST con decisión `would_deny` | — |

El runtime modeling y Canvas mide tiempo real observado. CPU_SIMULATION es por ahora un proxy de
wall seconds del job, no CPU-seconds del host; está etiquetado para no confundirlo con coste.
Storage cubre imports y resultados generados en los caminos comerciales instrumentados.

Con estos ledgers se puede agregar posteriormente por Organization/proyecto/simulación para
estimar coste por simulación, proyecto y Organization. La conversión a moneda queda bloqueada
hasta contar con tarifas reales de CPU, storage, AI y proveedor.
