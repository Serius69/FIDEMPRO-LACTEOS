# Planes y unidades comerciales de Findempro

## Sujeto y unidades

- **Sujeto de suscripción:** `Organization`.
- **METERABLE_UNIT:** eventos reales de proyecto, dataset, filas, simulación, runtime,
  escenario, export, reporte, AI, API y storage; recursos CPU/tokens/storage cuando existen.
- **BILLABLE_UNIT:** plan de la Organization. No hay precio por uso ni proveedor de pago en
  este ciclo.
- **QUOTA_UNIT:** proyectos activos, datasets, filas por import, simulaciones por mes,
  exports por mes y miembros.

Los límites son defaults configurables de lanzamiento, no afirmaciones de capacidad. Derivan
de límites de seguridad ya presentes (10/100 ejecuciones históricas, 10.000 filas y 2 MiB por
import) y se validarán comercialmente tras el benchmark independiente 25/100/500/1000.

| Plan | Proyectos | Datasets | Filas/import | Sim/mes | Exports/mes | Miembros |
|---|---:|---:|---:|---:|---:|---:|
| FREE | 1 | 1 | 10.000 | 10 | 1 | 1 |
| STARTER | 5 | 5 | 10.000 | 100 | 30 | 3 |
| GROWTH | 20 | 25 | 10.000 | 500 | 150 | 10 |
| PRO | 100 | 100 | 10.000 | 2.000 | 500 | 25 |
| BUSINESS | sin cuota comercial | sin cuota comercial | 10.000 hard safety | sin cuota comercial | sin cuota comercial | sin cuota comercial |

El hard limit por import y los límites anti-abuso siguen aplicando a BUSINESS.

## Free y trial

FREE resuelve un problema pequeño completo: una Organization crea un proyecto, usa la muestra
genérica o importa un dataset acotado, ejecuta Monte Carlo, ve resultados básicos y realiza una
exportación. No depende del dataset lácteo.

El trial configura `trial_started_at`, `trial_ends_at`, `trial_plan` y
`trial_consumed_at`. Es de un solo uso por Organization. Al expirar vuelve a FREE; no elimina
datos. Si el estado existente excede FREE, se conserva y las nuevas creaciones quedan bloqueadas
hasta reducir uso aplicable o hacer upgrade.

## Cambios de plan

`change_plan(organization, plan)` es el servicio interno canónico y no conoce Stripe ni otro
procesador. Su endpoint administrativo exige operador interno; un OWNER no puede autoasignarse
un plan premium. Upgrade habilita capabilities inmediatamente. Downgrade y cancellation
preservan Organization, proyectos, datasets y resultados; cancellation lleva el plan efectivo
a FREE. El CTA de UI dirige al Hub configurado.
