# Findempro: decisión de identidad canónica

Fecha de decisión: 2026-08-29. Alcance: DEV. No se borra ni fusiona ningún repositorio.

## Decisión

| Rol | Identidad canónica |
|---|---|
| Producto comercial | **Findempro** |
| Runtime canónico | linaje desplegable `FindemproAI` (Django + React/Vite) |
| Core engine | `findempro/modeling`, `findempro/simulate/core` y motores existentes |
| Web app | SPA React/Vite y vistas Django legacy del mismo runtime |
| API | Django/DRF: Modeling API y Canvas API v2 |
| Reescritura standalone | candidato de sustitución futura; no runtime canónico de este ciclo |
| FindemproLácteos | producto/vertical sectorial separado existente; no es el core comercial canónico |

La marca de cara al mercado es Findempro. `FindemproAI` queda como nombre técnico del
repositorio/runtime hasta que exista un rename coordinado. El nombre no define una segunda
cuenta, tenant, plan ni proveedor de identidad.

## Evidencia

- `FindemproAI` contiene el conjunto funcional más amplio: modeling DSL, canvas, Monte Carlo,
  eventos discretos, dinámica de sistemas, escenarios, sensibilidad, importación, reportes,
  dashboards, frontend y contratos de release backend/frontend. Su `origin/main` era
  `7e6af7d93edc493dfd5ba827e7237d5d077e8cac` al abrir este ciclo.
- El standalone (`/home/sergui/dev/products/findempro`) es una extracción/productización
  FastAPI + React + NumPy con tenant JWT y gates propios. Su documentación declara que no
  tiene billing y que su despliegue no fue ejecutado. Su remote no pudo refrescarse durante
  esta auditoría; por tanto no desplaza al linaje con contratos de release verificables.
- FindemproLácteos se autodefine como fork sectorial con URL, base de datos e infraestructura
  separadas. Se preserva como vertical/producto separado. La plantilla dairy del core y el
  dataset de ejemplo genérico permiten que Findempro no dependa de ese fork.

## Límites de la decisión

- No hay dependencia de código entre los repositorios.
- No se copia ciegamente el standalone ni XGOL.
- Una convergencia futura requiere ADR/migración propia, compatibilidad de datos, comparación
  de motores y evidencia de deployment; queda fuera de este ciclo.
- `fk_user` en tablas legacy identifica al creador por compatibilidad. La propiedad comercial
  autoritativa es `Organization` y se deriva de una FK/chain obligatoria documentada.
