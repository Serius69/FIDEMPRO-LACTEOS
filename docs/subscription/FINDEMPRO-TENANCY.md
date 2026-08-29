# Tenancy, ownership y RBAC

## Modelo canónico

`Organization` posee `Subscription`, ledgers y recursos comerciales. Un usuario accede por
`OrganizationMembership`; roles: `OWNER`, `ADMIN`, `MEMBER`, `READ_ONLY`.

- OWNER/ADMIN/MEMBER: lectura y mutación dentro del tenant.
- READ_ONLY: lectura dentro del tenant, sin mutación.
- Cambio/cancelación de suscripción: OWNER/ADMIN; cambio o inicio de trial además requiere
  operador interno mientras no exista proveedor de pago.

`OrganizationMiddleware` selecciona una Organization activa de la membresía autenticada. La
cabecera `X-Organization-ID` solo selecciona entre Organizations a las que el usuario pertenece;
un ID ajeno produce 403.

## Grafo de propiedad

| Recurso | Propiedad autoritativa |
|---|---|
| project/empresa legacy | `Business.organization` |
| proyecto canvas | `SimulationProject.organization` |
| dataset/import | `BusinessDataImport -> ModelVersion -> Definition -> Business.organization` |
| scenario | `BusinessScenario -> ModelVersion -> Definition -> Business.organization` |
| simulation/result/job modeling | `BusinessSimulationRun -> ModelVersion -> Definition -> Business.organization` |
| canvas result/job/export | `CanvasSimulationRun -> SimulationProject.organization` |
| risk alert | `RiskAlert.organization` |
| usage/cost | FK directa a `Organization` |
| report/export | recurso fuente org-scoped + evento de ledger org-scoped |

Las FK de Organization tienen `PROTECT` en recursos/ledgers relevantes. Constraints impiden
Business, SimulationProject y RiskAlert sin Organization después del backfill. `fk_user` se
conserva como creador legacy y no autoriza acceso.

## Aislamiento probado

Los querysets API parten de Organization. Las pruebas negativas cubren que ORG_A no puede leer
o mutar proyecto de ORG_B, importar o ejecutar con su dataset/modelo, leer resultado, reportar o
exportar, consultar/cancelar jobs ni consumir cuota ajena, tanto en Modeling como Canvas.

Los caches anti-abuso incluyen Organization y actor. Los callbacks async vuelven a resolver la
Organization desde el run persistido; no aceptan tenant desde el payload del cliente.
