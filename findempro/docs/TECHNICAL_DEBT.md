# FindemproAI — registro técnico y gates

Este registro separa defectos observados de verificaciones que todavía no se
pueden afirmar. Un test local verde no convierte automáticamente un gate de
integración o producción en PASS.

## P0 — bloqueante inmediato

| Estado | Evidencia |
|---|---|
| 0 abiertos observados | Suite Django **1002/1002** en SQLite y en **PostgreSQL 16**; `check` limpio; `makemigrations --check --dry-run` sin cambios. Confirmado además en GitHub Actions (run 32139967469): 1002 passed contra PostgreSQL. |

## P1 — obligatorio antes de integrar o publicar

| Estado | Clase | Ítem | Evidencia / cierre requerido |
|---|---|---|---|
| CLOSED | RELEASE_GATE | Browser E2E | `libasound2t64` ya está instalado en el host, así que Chromium arranca y el arnés corre de verdad. `simulate/tests/e2e_browser_flow.js` → **23/23** sobre la pila actualizada (Django 5.2.17): login → negocio → plantilla → modelo → validar → datos → simular → progreso → resultados → escenarios → reporte, más los negativos (símbolo desconocido, no finito, iteraciones inválidas, JSON malformado), la autorización entre dueños y la consola sin errores. `simulate/tests/e2e_http_flow.py` → **18/18**. Ambos siguen fuera del CI: exigen sembrar usuarios y un negocio contra una instancia desechable, y ese sembrado todavía no es un comando reproducible. |
| OPEN | RELEASE_GATE | Integración y release | Avanzado: la rama está committeada y publicada en la PR #27, y el CI de GitHub Actions pasa **entero** (static, checks+migraciones, tests, auditoría de dependencias, frontend, y la compuerta de release). Queda el merge y, después, backup, migraciones en staging, login del dueño y verificación post-deploy. No hay destino de producción canónico verificado para FindemproAI. |
| OPEN | RELEASE_GATE | Cobertura frontend de componentes | Existe smoke de contratos de rutas/UI; no se afirma cobertura de componentes ni E2E hasta disponer del runner aprobado. |
| CLOSED | RELEASE_GATE | Soporte de dependencias y CVEs | Django **4.2.30 → 5.2.17 LTS** y 20 paquetes más. `pip-audit`: **63 vulnerabilidades en 17 paquetes → 0**, en `production.txt`, en `development.txt` y sobre el entorno instalado completo, sin ningún `--ignore-vuln`. Verificado también en el CI. Sin deriva de esquema. |
| OPEN | PRODUCT_DEBT | Auditoría legacy estadística/financiera completa | Cerrados en esta ola: fallbacks aleatorios de charts; mutación de proyecciones en charts; reconstrucción PDF de muestras/VaR/CVaR; riesgo sin muestras ahora N/A; onboarding no persiste fixtures como verdad; forecast React usa la serie enviada. Sigue pendiente normalizar `simulation_financial_utils`, exports/API legacy y dashboards que aún convierten campos monetarios ausentes a cero. |

## P2 — no bloqueante para el slice actual, planificado

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
