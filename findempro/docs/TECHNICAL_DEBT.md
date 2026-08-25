# FindemproAI — registro técnico y gates

Este registro separa defectos observados de verificaciones que todavía no se
pueden afirmar. Un test local verde no convierte automáticamente un gate de
integración o producción en PASS.

## P0 — bloqueante inmediato

| Estado | Evidencia |
|---|---|
| 0 abiertos observados | Suite Django **1136/1136** sobre PostgreSQL 16 real; `check` limpio; `makemigrations --check --dry-run` sin cambios. Gates de producto verificados el 2026-08-25: frontend `vitest` 53/53, `tsc -b && vite build` OK, y navegador real (Chromium 151) 18/18 sobre tres viewports contra el Django real — Simulación y Pronóstico incluidas. El contexto macro sale de KDP observado, no del valor curado. |

**Cerrado durante el release del 2026-08-18:** el superusuario `sergio` seguía **vivo en
producción con la contraseña publicada en claro en `CHANGELOG.md`** de este repositorio en
GitHub. El arreglo anterior había quitado el literal de `ensure_superuser`, pero eso sólo
impedía que *futuros* despliegues la crearan: la cuenta existente nunca se rotó, así que
cualquiera que leyera el repo entraba al admin. Verificado con `check_password` contra una
copia del dump (nunca contra producción), **rotado en producción** y retirado del changelog.
> ⚠️ El changelog decía que esa contraseña era «idéntica a xgol». Si xgol o forex-erp
> comparten el literal, siguen expuestos — fuera del alcance de este repo.

## P1 — obligatorio antes de integrar o publicar

| Estado | Clase | Ítem | Evidencia / cierre requerido |
|---|---|---|---|
| CLOSED | RELEASE_GATE | Browser E2E | `libasound2t64` ya está instalado en el host, así que Chromium arranca y el arnés corre de verdad. `simulate/tests/e2e_browser_flow.js` → **23/23** sobre la pila actualizada (Django 5.2.17): login → negocio → plantilla → modelo → validar → datos → simular → progreso → resultados → escenarios → reporte, más los negativos (símbolo desconocido, no finito, iteraciones inválidas, JSON malformado), la autorización entre dueños y la consola sin errores. `simulate/tests/e2e_http_flow.py` → **18/18**. Actualizado 2026-08-25: el sembrado ya **es** reproducible — `frontend/playwright.config.ts` levanta Django y vite por su cuenta sobre un SQLite desechable y crea el usuario con `ensure_superuser`, así que el arnés corre con un solo comando: `FINDEMPRO_E2E_PYTHON=<venv>/bin/python npx playwright test` (**18/18** en tres viewports, ~45 s). Cubre Simulación y Pronóstico contra el Django real y falla ante cualquier `pageerror`. Sigue fuera del CI por decisión, no por impedimento: arrancar dos servidores en el runner alarga el gate y el contrato ya está cubierto por `test_api_v1_wire_contract.py`. |
| CLOSED | RELEASE_GATE | Integración y release | PR #27 mergeada (`dd9b4b2`) y **desplegada en producción el 2026-08-18**. Destino canónico verificado por labels de Compose, no por documentación: proyecto `findempro`, `findempro/docker-compose.prod.yml`, 7 servicios, expuesto como `app.kapitalya.com.bo` vía Cloudflare. Backup `pg_dump` **restaurado y validado** en un PostgreSQL desechable (66 tablas, 153 migraciones, 2 usuarios) y ensayo de migración sobre esa copia ANTES de tocar producción: 10 migraciones, cero filas perdidas, `DESTRUCTIVE_MIGRATIONS=0`. Post-deploy: Django **4.2.30 → 5.2.17**, `pip-audit` 0 contra el runtime real, 7/7 contenedores sanos con 0 reinicios, login del dueño y aceptación HTTPS 21/23 sobre producción (los 2 restantes no son regresiones: ver P2). Integridad: los únicos deltas son +6 ContentTypes y +24 Permissions — los 6 modelos `modeling` × 4 permisos. Rollback preparado (`findempro/rollback-*:pre-django52-20260818`) y no necesario. |
| CLOSED | RELEASE_GATE | Cobertura frontend de componentes | Runner de componentes instalado (vitest + @testing-library/react + jsdom, `npm run test:components`), fuera del grafo de `tsc -b`/`vite build`. **45 tests de comportamiento sobre 8 componentes críticos** (antes: 0 — el smoke previo sólo hacía contratos estáticos por regex, nunca renderizó un componente): ErrorBoundary, TooltipSimple, ResultadoSimulacion, OnboardingGuiado, Businesses, Dashboard, Simulate, Results, más OnboardingPage. No son snapshots ni relleno de cobertura: fijan que un valor ausente NO se pinte como `Bs. 0`, que un error se vea como error y no como éxito vacío, y que carga ≠ sin datos. Verdes junto a `npm test` (11), `npm run typecheck` y `npm run build`. |
| CLOSED | RELEASE_GATE | Soporte de dependencias y CVEs | Django **4.2.30 → 5.2.17 LTS** y 20 paquetes más. `pip-audit`: **63 vulnerabilidades en 17 paquetes → 0**, en `production.txt`, en `development.txt` y sobre el entorno instalado completo, sin ningún `--ignore-vuln`. Verificado también en el CI. Sin deriva de esquema. |
| CLOSED | PRODUCT_DEBT | Auditoría legacy estadística/financiera completa | Cerrados los tres pendientes que quedaban. **`simulation_financial_utils`**: estaba a medias — `gross_margin`/`net_margin`/`roi` ya devolvían `None`, pero ingresos, costos, utilidad, volumen y precio seguían leyéndose con `.get(clave, 0)`. Una corrida sin variables financieras se reportaba como un negocio que factura Bs 0,00 y pierde todos los días; y como esa serie de ceros inventados tiene volatilidad 0, **la ausencia de datos sumaba los 20 puntos de "estabilidad" del score de salud**. Además `None < 0.05` en `_assess_financial_risks` era un `TypeError` latente en producción. **Exports/API legacy**: el ranking puntuaba con 0 una corrida sin métricas y la mostraba como el peor negocio del conjunto (tras un `except:` desnudo); la comparación dejaba entrar una corrida vacía como un negocio que factura 0, nunca pierde (0 no es < 0) y competía por "ganador". **Dashboards**: el fallback ante excepción devolvía `financial_health: 0`, que se mapeaba a estado `poor` — un error interno se leía como "el negocio necesita mejoras significativas"; y una recomendación sin métrica tomaba `or 0.5` y se pintaba como "50%". Todo lo no observado vale `None` y se propaga hasta la vista; los agregados declaran `observed_days`/`total_days`. **44 tests nuevos** (25 + 10 backend, 9 dashboards) sobre 1002 previos: **1046/1046**. |

## P2 — no bloqueante para el slice actual, planificado

- **`/simulate/` responde 500** (`TemplateDoesNotExist: simulate/apps.html`). Ruta muerta
  (`simulate.index` → `AppsView`) que **nunca** tuvo plantilla en el historial de git y que
  también fallaba en la imagen anterior: no es una regresión del salto a Django 5.2. No está
  enlazada desde ninguna vista ni plantilla; los accesos reales son `/simulate/init/` y
  `/simulate/list/`, ambos 200. Debe devolver 404 o redirigir, no 500.
- **Cache-busting de los estáticos servidos por Django.** Producción usa
  `CompressedStaticFilesStorage` (sin manifiesto ni hash) y nginx los sirve con
  `Cache-Control: public, immutable, max-age=31536000`. Los assets de la SPA sí van
  hasheados por Vite (`index-<hash>.js`) y están bien, pero un cambio en el CSS del admin
  o de DRF puede no llegar a un navegador que ya lo tenga cacheado hasta por un año.
- **Password de Redis en los logs del contenedor.** `wait_for_redis` del entrypoint no
  quitaba las credenciales de `REDIS_URL` antes de parsear: imprimía el secreto en cada
  arranque y, de paso, el wait nunca funcionaba (caía siempre a "Redis no disponible").
  El parseo ya está corregido; **el secreto sigue en los logs de los contenedores actuales
  y en cualquier copia de ellos, así que conviene rotarlo**.
- Editor gráfico avanzado: agrupación y minimapa interactivo; el editor ya
  tiene zoom, undo/redo, arrastre/pan y conexiones causales estructuradas.
- Callbacks de progreso por iteración para ejecuciones largas; hoy se exponen
  fases bounded (10%, 20%, 100%).
- Validación real de GPU/CuPy en un host NVIDIA; el override compose es válido
  solo junto con el compose de producción.
- Optimización y capa agent-based, que deben añadirse solo con contratos y
  casos de negocio justificables.
- PDF/XLSX de reportes; CSV trazable está implementado.

## P3 — mantenimiento

- Advertencia `react-refresh/only-export-components` en `TooltipSimple.tsx`.
- Revisar warnings de dependencias antiguas de Django/requests sin alterar el
  contrato funcional.

## Invariantes

- P0/P1 no se declaran cerrados por ausencia de errores en una prueba estrecha.
- Las plantillas son sintéticas/editables y no son datos económicos reales.
- Las simulaciones son condicionales a datos, supuestos, distribuciones,
  parámetros, seed y versión del modelo; no representan predicción perfecta.
