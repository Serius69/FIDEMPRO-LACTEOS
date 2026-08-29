# Resultados de capacidad de Findempro

## Dictamen

`FINDEMPRO_LOAD_READY_FOR_INITIAL_MARKET=PASS` dentro del runtime DEV declarado y hasta el punto
verificado: 100 paid + 300 Free aprovisionadas, 15 sesiones concurrentes. S1 y S2 pasan los SLO,
el aislamiento tenant y la atribución de uso. Este PASS no valida la topología de producción.

| Tier | Mezcla | Concurrencia | Resultado | RPS | p95 global | Error | CPU pico host | RAM pico procesos |
|---|---|---:|---|---:|---:|---:|---:|---:|
| S0 | 1 paid + 1 Free | 2 | VERIFIED_PASS | 8.250 | 18.620 ms | 0% | 7.237% | 493.418 MB |
| S1 | 25 paid + 75 Free | 12 | VERIFIED_PASS | 47.267 | 45.212 ms | 0% | 14.438% | 508.074 MB |
| S2 | 100 paid + 300 Free | 15 | VERIFIED_PASS | 57.678 | 51.730 ms | 0.0193% | 14.966% | 513.027 MB |
| S3 | 500 paid + 1500 Free | — | NOT_RUN_CAPACITY_GUARD | — | — | — | — | — |
| S4 | 1000 paid + 3000 Free | — | NOT_RUN_CAPACITY_GUARD | — | — | — | — | — |

El único error inesperado de S2 fue un 429 en dataset preview; 1/5191 requests y 0.2762% en
la clase DATASET_IMPORT, por debajo del SLO. Hubo 714 rechazos 403/404 esperados por cuota o
probes de seguridad y no se contabilizaron como errores.

## Saturación observada

Con el mismo inventario S2, concurrencia 25 no cumplió el SLO de submit:

| Worker concurrency | RPS | p95 global | p95 submit | Queue peak | DB latency acumulada | Locks | Resultado |
|---:|---:|---:|---:|---:|---:|---:|---|
| 4 | 69.544 | 403.577 ms | 5401.954 ms | 50 | 178835 ms | 7 | FAIL |
| 2 | 86.700 | 152.432 ms | 1311.722 ms | 75 | 89706 ms | 0 | FAIL |
| 1 | 91.656 | 97.736 ms | 869.165 ms | 88 | 75373 ms | 0 | FAIL |
| 2, concurrencia 15 | 57.678 | 51.730 ms | 333.321 ms | 42 | 16478 ms | 0 | PASS |

`SATURATION_POINT=BETWEEN_CONCURRENCY_15_AND_25_AT_S2_MIX`.
`PRIMARY_BOTTLENECK=SQLITE_WRITE_CONTENTION_ON_SIMULATION_SUBMIT_AND_METERING`.
`SECONDARY_BOTTLENECK=SIMULATION_QUEUE_WAIT_DEPTH`.

No se cambió código de producto ni se desactivaron controles. El ajuste demostrado fue del
scheduling del stub DEV (workers 4→2) y la rampa; aun así, concurrencia 25 siguió fallando. La
capacidad publicada se redujo al último punto que sí pasó, concurrencia 15.

## Simulaciones y async

El profiler puro ejecutó diez repeticiones por tamaño:

| Perfil | Iteraciones | CPU mean | Runtime p95 | Python allocation peak mean | Process max RSS | Sim/min, 1 proceso |
|---|---:|---:|---:|---:|---:|---:|
| small | 25 | 299.591 ms | 319.996 ms | 0.168 MB | 145.699 MB | 200.129 |
| medium | 250 | 2914.109 ms | 3008.302 ms | 0.185 MB | 145.699 MB | 20.577 |
| heavy | 2000 | 23589.142 ms | 23869.658 ms | 0.322 MB | 146.074 MB | 2.542 |

El engine puro hizo 0 queries; persistencia y metering ocurren en el lifecycle HTTP/worker. En
S2 se enviaron/completaron 60/60, failed=0, cancelled=0, p95 end-to-end=21482.838 ms, p95 de
espera/job=21315.809 ms y 39.998 simulaciones/min durante la ventana, con concurrencia worker=2.
La cola llegó a 42 y drenó. Las simulaciones sí compiten con tráfico interactivo a través de
escrituras SQLite de lifecycle y metering.

Lifecycle `queued/running/completed/failed/cancelled` y errores controlados se validaron mediante
tests y carga. Retry rate y duplicate execution bajo broker externo son `NOT_MEASURABLE`.

## DB, suscripción, datasets e IA

En S2: 23712 queries, 16478 ms DB acumulados, 4 requests con DB >100 ms, 0 locks y conexiones
`NOT_MEASURABLE_SQLITE`. El microbenchmark aislado midió entitlement en 0.3535 ms/check y 1
query/check; metering en 0.7805 ms/event y 4 queries/event. No se eliminó RBAC, cuota,
entitlement ni metering.

Import sintético: 100 filas p95=205.370 ms en S2 (5 muestras), 1000 filas=15.455 ms y 10000
filas=29.182 ms (una muestra cada una). Los dos últimos datos tienen baja confianza y no deben
usarse como percentil poblacional.

IA fue un stub local determinista: 57 calls, p95=0.011 ms, failures=0 en S2. No hubo llamadas de
carga a proveedores; `REAL_AI_CAPACITY=NOT_MEASURABLE`.

## Seguridad, fallos y atribución

S2 hizo 158 intentos de cada probe cross-org read/write/job; todos devolvieron ocultación 404:
cross_org_reads=0, cross_org_writes=0 y cross_org_jobs=0. Los 150 eventos esperados quedaron
atribuidos a la Organization correcta, con 0 errores. Quota leakage=0 en probes/tests.

Tests controlados cubren timeout de simulación, failed job/export coherente, AI timeout con
fallback determinista y metering, aislamiento tenant, lifecycle, suscripción y API de modelos.
Parsing failure, quota exhaustion e idempotencia/duplicate submission también se mantienen en
la suite existente; la duplicidad bajo un broker externo real sigue `NOT_MEASURABLE`.

## Sensibilidad Free y datos por customer activo

Con S1 a concurrencia fija 12, las mezclas 1:1, 1:3 y 1:10 dieron respectivamente p95 39.823,
45.212 y 35.047 ms, todas PASS. Esto demuestra que el aprovisionamiento sintético no degradó
la carga cerrada a concurrencia fija; no prueba que Free no aumente la concurrencia real.

En S2, por cada una de las 15 Organizations activamente ejercitadas durante la sesión:
6.088 CPU-s, 1.3414 MB de delta RAM pico, 79189 bytes de storage, 346.067 requests y 3.8 llamadas
AI stub. Son cocientes observados, no lineales ni forecasts. CPU de simulación por Organization
no puede aislarse del proceso compartido: `NOT_MEASURABLE`; se reporta arriba por simulación.

## Evidencia

Los JSON bajo `artifacts/load/` son la fuente machine-readable. `S2-100-before-*` y
`S2-100-concurrency25-worker1.json` preservan los FAIL; `S0.json`, `S1-25.json` y `S2-100.json`
son los resultados finales. S3/S4 contienen únicamente el capacity guard, sin métricas
inventadas.
