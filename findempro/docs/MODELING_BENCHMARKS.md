# Referencias de arquitectura de modelado

## Alcance

FindemproAI toma capacidades públicas como referencia de producto; no copia
código, assets, APIs privadas ni la interfaz de ningún proveedor. La semántica
del modelo canónico y sus resultados siguen siendo propios y están condicionados
por datos, supuestos, parámetros, distribuciones y escenarios.

## Referencia de modelado dinámico

La documentación oficial de isee describe Stella Architect/iThink como un
entorno que combina construcción de modelos e interfaces, con mapas stock/flow,
ecuaciones, unidades, sensibilidad, optimización, importación/exportación y
módulos. Esos conceptos justifican en FindemproAI:

- separar el DSL estructural de las vistas derivadas;
- tratar stock/flow y diagramas causales como representaciones explícitas;
- mantener unidades y ecuaciones en un panel de propiedades;
- ejecutar sensibilidad y escenarios sobre versiones inmutables;
- mantener importación/exportación trazable, sin ejecutar código del usuario.

La inspiración no implica que una relación causal sea automáticamente una
ecuación numérica: el compilador de FindemproAI exige referencias, unidades,
ciclos y distribuciones válidas antes de ejecutar.

Fuentes oficiales consultadas:

- https://ssl.iseesystems.com/resources/help/v3/Content/Welcome.htm
- https://www.iseesystems.com/resources/tutorials/legacy/
- https://www.iseesystems.com/resources/help/v2/Content/01-The_Stella_environment/Using_the_Properties_Panel.htm
- https://www.iseesystems.com/resources/help/v4/Content/07b-AdditionalSoftwareSolutions/StellaInExcel/StellaInExcelTaskPane.htm

## Clasificación de “Prometheus”

La evidencia local clasifica la referencia como `OBSERVABILITY_PROMETHEUS`:

- FindemproAI ya usa `django_prometheus`, middleware de métricas y una ruta
  de observabilidad en su stack operativo.
- El commit local preservado `379c38c43` añade el alias de red para que el
  scraper de Prometheus encuentre el backend.
- La documentación oficial de Prometheus lo define como sistema de
  monitorización y base de datos de series temporales, con métricas y PromQL;
  no es un motor de simulación empresarial.

Por tanto, las métricas de duración, fallos, cola, iteraciones y tamaño de
modelo pueden ir a observabilidad, pero nunca se mezclan con variables de
negocio, demanda, caja o resultados de simulación.

Fuente oficial:

- https://prometheus.io/

## Decisión

FindemproAI mantiene una arquitectura multiparadigma propia:

`DSL → validar → normalizar → compilar → engine seleccionado → resultado`

con Monte Carlo, System Dynamics y Discrete Event como contratos separados.
Un futuro Agent-Based engine solo se incorporará cuando exista un contrato de
tiempo, aleatoriedad, unidades, entradas, salidas y pruebas que lo justifique.
