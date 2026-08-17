# FindemproAI — registro técnico y gates

Este registro separa defectos observados de verificaciones que todavía no se
pueden afirmar. Un test local verde no convierte automáticamente un gate de
integración o producción en PASS.

## P0 — bloqueante inmediato

| Estado | Evidencia |
|---|---|
| 0 abiertos observados en el entorno local | Suite Django: 975/975; `check`; `makemigrations --check --dry-run`; `git diff --check` pasan. |

## P1 — obligatorio antes de integrar o publicar

| Estado | Clase | Ítem | Evidencia / cierre requerido |
|---|---|---|---|
| OPEN | RELEASE_GATE | Browser E2E | **Arnés escrito y listo; falta un paquete del sistema.** `simulate/tests/e2e_browser_flow.js` cubre el flujo crítico contra una instancia desechable (`findempro.settings.e2e`, SQLite en archivo temporal, Celery síncrono). Chromium sigue sin arrancar: `ldd` sobre `chromium-1234/chrome-linux64/chrome` reporta **una sola** dependencia ausente, `libasound.so.2`, y `ldconfig -p` no la encuentra en el sistema. Acción exacta en Ubuntu 26.04: `sudo apt-get install -y libasound2t64` (candidato 1.2.15.3-1ubuntu1.1, no instalado). Mientras tanto, el mismo flujo se verificó a nivel HTTP contra la app corriendo: `simulate/tests/e2e_http_flow.py` → **18/18** (login, negocio, plantilla, modelo, validación, simulación, iteraciones inválidas → 400, JSON malformado → 400, valor no finito rechazado, dueño ajeno 403/404, anónimo redirigido). Eso cubre servidor y autorización, **no** el render ni el JavaScript. |
| OPEN | RELEASE_GATE | Integración y release | La rama no está committeada/mergeada/desplegada por las restricciones del worktree. Requiere revisión de diff, PR, backup, migraciones en staging, owner login y post-deploy. |
| OPEN | RELEASE_GATE | Cobertura frontend de componentes | Existe smoke de contratos de rutas/UI; no se afirma cobertura de componentes ni E2E hasta disponer del runner aprobado. |
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
