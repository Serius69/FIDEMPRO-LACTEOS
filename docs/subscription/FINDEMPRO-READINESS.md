# Findempro readiness DEV

## Matriz funcional

| Feature | Backend | Frontend | Connected | Tested | User accessible | Production safe | Plan sensitive |
|---|---|---|---|---|---|---|---|
| signup + Organization/Free | sí | Django auth + estado SPA | sí | sí | sí | sí | base |
| crear proyecto/empresa/modelo | sí | sí | sí | sí | sí | sí | quota |
| muestra/import CSV/XLSX/JSON | sí | sí | sí | sí | sí | sí, bounded | dataset quotas |
| configuración/model DSL/BOM/process | sí | sí | sí | sí | sí | sí | base |
| distribuciones | sí | sí | sí | sí | sí | sí | advanced_distributions |
| escenarios | sí | sí | sí | sí | sí | sí | base; compare GROWTH |
| Monte Carlo | sí | sí | sí | sí | sí | sí | monthly quota |
| DES/system dynamics/sensitivity | sí | sí | sí | sí | sí | bounded | advanced_simulation |
| lifecycle async/progress/cancel/retry | sí | sí | sí | sí | sí | existing Celery | advanced/batch |
| resultados/dashboard/comparación | sí | sí | sí | sí | sí | sí | comparison gated |
| report/export JSON/DSL/CSV | sí | sí | sí | sí | sí | formula-safe | entitlement/quota |
| persistencia/reejecución/errores | sí | sí | sí | sí | sí | safe envelopes | simulation quota |
| AI variables/questions | sí + fallback | legacy UI | sí | sí | sí | metered/bounded | ai_analysis |
| plan/trial/quota/upgrade CTA | sí | sidebar/errors | sí | sí | sí | provider-decoupled | n/a |

## Journey de valor

`signup -> Organization + FREE -> create project -> sample/import -> configure scenario -> run
simulation -> first result`. La muestra JSON genérica evita depender de Lácteos. El onboarding
anónimo conduce a signup para persistir el proyecto.

El tiempo a primer valor no se declara en minutos hasta medirlo con telemetría real; el journey
no requiere soporte técnico ni infraestructura externa para el camino Monte Carlo pequeño.

## Seguridad

- Auth + membership/RBAC; querysets org-scoped y negativas cross-tenant.
- Uploads: 2 MiB, 10.000 filas, XLSX archive/expanded-size bounds, lectura limitada.
- Fórmulas del motor por allowlist/AST; CSV neutraliza `= + - @ tab CR`.
- Anti-abuse separado para simulation/import/export/sensitivity/AI; cuotas de producto aparte.
- Cambios premium requieren operador interno hasta integrar proveedor; no self-upgrade.
- CORS/CSRF/security headers siguen el contrato existente por entorno.
- No se accedió a PROD, DB PROD o Redis PROD.

## Deuda de lanzamiento

| ID | Prioridad | Estado | Resolución |
|---|---|---|---|
| dual-identity | P1 launch | closed | decisión canónica en FINDEMPRO-IDENTITY |
| disabled-gates | P1 launch | closed | mode shadow/enforce + catálogo central |
| user/org ownership | P0 | closed | Organization FKs/chains + backfill/constraints |
| missing usage | P1 launch | closed | UsageEvent append-only/idempotente |
| missing cost | P1 launch | closed | ResourceUsage; coste unknown explícito |
| cross-tenant IDOR | P0 | closed | querysets + pruebas negativas |
| self-assigned premium/trial abuse | P0 | closed | operador interno + trial single-use |
| benchmark 25/100/500/1000 | ciclo posterior | open/non-launch | harness preparado; no benchmark aquí |

P0 abierto: 0. P1 launch-critical abierto: 0, condicionado a que todos los gates de validación
documentados abajo permanezcan PASS en el SHA final.

## Evidencia de validación

Evidencia DEV ejecutada el 2026-08-29:

| Gate | Resultado |
|---|---|
| Django system check | PASS, 0 issues |
| migration drift | PASS, no changes detected |
| migration compatibility | PASS: esquema legacy -> backfill -> latest -> restore latest |
| backend completo | PASS, 1.164 tests |
| contracts frontend | PASS, 11 tests |
| componentes frontend | PASS, 53 tests |
| journeys E2E Playwright | PASS, 18 tests desktop/tablet/mobile contra backend local |
| frontend lint | PASS con 0 errores y 1 warning preexistente de Fast Refresh |
| frontend typecheck | PASS |
| frontend build | PASS, Vite 6.4.3 |
| npm audit moderate+ | PASS, 0 vulnerabilidades |
| pip-audit producción | PASS, 0 vulnerabilidades conocidas |
| secreto high-confidence | PASS, sin coincidencias |
| Ruff archivos nuevos | PASS, ignorando solo RUF012 de Meta/migrations Django |
| harness prepare | PASS, 2 orgs/4 users/2 projects y cleanup |
| harness HTTP smoke | PASS, 2 requests, concurrency 2 y cleanup |
| benchmark 25/100/500/1000 | NOT_RUN por alcance |

Warnings no bloqueantes observados: deprecations de dependencias en tests, un warning ESLint
preexistente, Recharts 2 en rama de mantenimiento y Node 22.22.1 un patch por debajo del rango
preferido por jsdom 30 (los 53 tests jsdom pasan). Se registran como P2/P3, no deuda de
lanzamiento. Readiness de carga es `HARNESS_READY`, no `LOAD_READY`.
