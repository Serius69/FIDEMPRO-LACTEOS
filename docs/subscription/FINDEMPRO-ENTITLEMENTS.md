# Entitlements, quotas y gates

Las únicas autoridades son:

```python
has_entitlement(organization, capability)
get_quota(organization, capability)
```

`FINDEMPRO_COMMERCIAL_GATES_MODE=shadow|enforce` controla el despliegue gradual. Producción
falla a `enforce`; tests legacy usan shadow de forma explícita y las pruebas comerciales cubren
enforcement. `PLAN_GATES_ENABLED` es solo alias de compatibilidad para el flujo v1 y ya resuelve
la suscripción de Organization, no `hub_plan`.

## Capabilities reales

| Capability | Feature real | Primer plan |
|---|---|---|
| basic_results | resultados Monte Carlo básicos | FREE |
| basic_visualization | dashboards/resultados básicos | FREE |
| exports | JSON/DSL/CSV | FREE, con cuota |
| collaboration | Membership/RBAC multiusuario | STARTER |
| advanced_distributions | ajuste/laboratorio de distribuciones | GROWTH |
| large_datasets | importación sobre el flujo básico acotado | GROWTH |
| scenario_comparison | comparación de corridas | GROWTH |
| advanced_reports | reportes avanzados existentes | GROWTH |
| advanced_simulation | DES, system dynamics y sensibilidad | PRO |
| batch_runs | ejecución avanzada/encolada | PRO |
| api_access | APIs autenticadas para integración | PRO |
| ai_analysis | generación Claude existente de variables/preguntas | PRO |

No hay `if plan == "PRO"` en los flujos comerciales nuevos. BUSINESS hereda el conjunto de
capabilities. Los límites de seguridad y anti-abuso son independientes de entitlements/cuotas.

## Inventario de gates heredados

| Gate | Por qué estaba deshabilitado | Antes | Seguridad/comercial | Normalización |
|---|---|---|---|---|
| `PLAN_GATES_ENABLED` | evitar romper tests/flujo Hub | bypass global y plan por usuario | cuota evadible, doble autoridad | alias a mode; adaptador org-scoped y ledger |
| engines no-Monte-Carlo | no tenía catálogo común | disponible a cualquier login | alto CPU sin segmentación | `advanced_simulation` |
| sensitivity | sin enforcement | disponible a cualquier login | coste alto | `advanced_simulation` + anti-abuse |
| distribution fit | sin enforcement | disponible a cualquier login | feature premium sin control | `advanced_distributions` |
| compare | sin enforcement | disponible a cualquier login | feature premium sin control | `scenario_comparison` |
| exports/report | sin quota común | ilimitado | exfil/coste | entitlement + cuota + anti-abuse + metering |
| AI Claude | fallback opaco | llamada si había secret | coste sin plan/meter | `ai_analysis` + tokens + anti-abuse |

No se reactivaron fixtures sintéticos: esos gates permanecen deshabilitados por integridad de
resultados y no son features comerciales.
