# Modelo de capacidad inicial de Findempro

Fecha: 2026-08-29. Entorno: DEV, host `tromay-dev`. Base Git:
`b6d6add8e1629ddc2231bc16ffd248f610c38f19`.

## Unidad de capacidad

`CUSTOMER=Organization`. Organization no equivale a User, active user, concurrent user,
Project, Dataset, Simulation, Scenario, Job, AI call ni Export. Cada tier declara por separado
Organizations aprovisionadas y concurrencia realmente ejercitada.

## Modelo inicial

Perfil comercial seleccionado para S1/S2: 1 paid : 3 Free activas. También se midieron 1:1 y
1:10 a igual concurrencia. El workload usa:

| Variable | Valor de S1/S2 | Estado |
|---|---:|---|
| users_per_paid_org | 3 | ASSUMPTION |
| active_users_per_paid_org | 1 | ASSUMPTION |
| projects_per_paid_org | 2 | ASSUMPTION |
| datasets_per_project | 1 | ASSUMPTION |
| dataset_rows principal | 100 | Medido; sensibilidad 1000/10000 |
| simulations_per_session | 4 | ASSUMPTION |
| scenarios_per_session | 2 | ASSUMPTION |
| exports_per_session | 1 | ASSUMPTION |
| AI_calls_per_session | 1 stub | ASSUMPTION; proveedor real no llamado |
| storage_growth | Medido por corrida | No es forecast mensual |

No existe telemetría de comportamiento real que valide aún estas distribuciones. Por eso los
valores anteriores son hipótesis reproducibles, no una predicción de demanda comercial.

## SLO definidos antes de medir

| Clase | Error | p95 | p99 |
|---|---:|---:|---:|
| INTERACTIVE_HTTP | <1% | <500 ms | <1000 ms |
| SIMULATION_SUBMIT | <1% | <500 ms | <1000 ms |
| SIMULATION_STATUS | <1% | <500 ms | <1000 ms |
| DATASET_IMPORT | <1% | <3000 ms | Informativo |
| EXPORT | <1% | <2000 ms | Informativo |

El runtime completo de simulación tiene SLO descriptivo por tamaño y se reporta separado del
submit/status. Background: la cola debe drenar y no crecer sin límite. Invariantes universales:
cross-tenant access=0, data corruption=0 y process crash=0.

## Interpretación válida

La verificación S2 prueba 100 Organizations de pago + 300 Free aprovisionadas, con 15 sesiones
concurrentes, durante 90 segundos sostenidos después de 8 segundos de warmup y 12 de ramp-up.
No prueba 400 usuarios concurrentes. La prueba de sensibilidad a concurrencia 25 falló y define
el límite observado del runtime SQLite/broker DEV.

No se extrapola a PostgreSQL, Redis, WSGI ni proveedores externos. Antes de usar estos números
para un despliegue distinto se debe repetir exactamente el workload contra ese runtime.
