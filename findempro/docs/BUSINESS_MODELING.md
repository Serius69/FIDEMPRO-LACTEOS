# Modelos de negocio dinámicos

FindemproAI usa `BusinessModelDefinition` como contenedor y
`BusinessModelVersion` como snapshot inmutable. La especificación JSON es la
fuente de verdad para la estructura del negocio; el canvas, BOM, procesos,
diagramas y resultados son vistas o artefactos derivados de esa versión.

## Contrato mínimo

```json
{
  "schema_version": "1.0",
  "metadata": {"name": "Tienda", "sector": "retail", "provenance": "USER_ENTERED"},
  "variables": [], "parameters": [], "entities": [], "resources": [],
  "employee_roles": [], "suppliers": [], "sales_channels": [], "inventory_nodes": [],
  "stocks": [], "flows": [], "products": [], "materials": [],
  "boms": [], "services": [], "processes": [], "demand": {},
  "costs": [], "revenues": [],
  "financial": {"units_sold": "period_demand", "unit_price": "unit_price"},
  "constraints": [], "equations": [],
  "distributions": [], "causal_links": [], "scenarios": [], "outputs": []
}
```

Cada elemento de una lista tiene un `id` estable. Las referencias se validan
antes de guardar una versión. Las ecuaciones y KPIs derivados pasan por un
intérprete allow-list sin `eval()` ni ejecución de código Python. Sus
dependencias se validan como un grafo acíclico y se ejecutan en orden
topológico, de modo que una fórmula puede referirse a otra declarada después
sin depender del orden del JSON. Los KPIs de `outputs` pueden usar
`revenue`, `cost`, `profit` y `unmet_demand`; las ecuaciones previas a la fase
financiera no pueden leer valores que todavía no existen.
Los errores de dominio numérico (división o módulo por cero, exponentes fuera
de rango, overflow y resultados no finitos) invalidan la ejecución con un
error controlado. Este contrato es común al evaluador escalar y vectorizado:
ninguno convierte una ecuación inválida en ingreso, costo o utilidad cero.

Variables, parámetros, stocks, flows, ecuaciones, procesos, servicios y
outputs comparten un único namespace ejecutable. Sus ids no pueden duplicarse
entre secciones, y `revenue`, `cost`, `profit` y `unmet_demand` están reservados
para agregados del motor. Los ids descriptivos de líneas de costo o ingreso no
son símbolos ejecutables y conservan libertad de nomenclatura.

La sección `demand` puede declarar `target` para conectar explícitamente la
demanda con una variable, parámetro, stock o distribución. Los targets no
declarados se rechazan antes de versionar el modelo.

## Límites de complejidad

La validación mide la complejidad antes de recorrer referencias, unidades o
ecuaciones. Los elementos de las listas del DSL y los componentes anidados de
BOM, procesos y servicios cuentan como nodos. Las relaciones causales, los
extremos de flows, componentes BOM, pasos/tareas, dependencias e `inputs`
declarados cuentan como aristas. La respuesta incluye `complexity.nodes`,
`complexity.edges` y los límites efectivos.

Los valores predeterminados son 1.000 nodos y 5.000 aristas, configurables con
`MODELING_MAX_MODEL_NODES` y `MODELING_MAX_MODEL_EDGES`. Un modelo que supera
alguno se rechaza antes de la validación profunda, versionado o compilación;
esto limita consumo accidental o abusivo sin cambiar el significado del DSL.

Cada expresión segura tiene además límites configurables de 500 caracteres,
200 nodos AST y 40 niveles de profundidad mediante
`MODELING_MAX_EXPRESSION_LENGTH`, `MODELING_MAX_EXPRESSION_NODES` y
`MODELING_MAX_EXPRESSION_DEPTH`. El parser aplica estos límites antes de
validar nombres o evaluar; `pow()` y el operador `**` comparten el mismo máximo
de exponente. Errores de dominio, overflow o recursión se convierten en errores
controlados y nunca habilitan ejecución Python arbitraria.

## Versiones y reproducibilidad

Una ejecución conserva `model_version`, `content_hash`, parámetros, engine y
seed. Cambiar una especificación crea otra versión y no altera el significado
de ejecuciones históricas. Los resultados son condicionales a datos,
supuestos, distribuciones, parámetros y escenario; el sistema mide
`MODEL_COMPLETENESS`, no exactitud de la realidad.

Los cambios de escenario son deltas aditivos en la unidad declarada. Para una
variable estocástica, el delta se aplica al valor muestreado usando la misma
secuencia aleatoria, lo que mantiene comparables el baseline y el escenario.
Para un stock, la distribución representa incertidumbre del estado inicial y
se muestrea una sola vez; el delta de escenario también se aplica una sola vez
al estado inicial y después los flujos transportan su evolución.

Los stocks son no negativos por defecto. Un modelo de deuda, sobregiro u otro
saldo firmado debe declarar `allow_negative: true`. Los outflows de un período
se limitan al stock de apertura y, si compiten varios, se reducen
proporcionalmente; los inflows forman parte del cierre y quedan disponibles en
el período siguiente. El resultado expone los flujos realizados, no solo los
solicitados, evitando inventario negativo y dependencia del orden del JSON.
Un flow con `role: "demand"` convierte cualquier recorte por inventario en
`flow_shortfalls`, `unmet_demand` y `stock_service_level`. Los ids de flows
realizados están disponibles para fórmulas seguras de ingresos y costos; así,
por ejemplo, `unit_price * sales` reconoce ventas efectivas y no factura
demanda que quedó sin atender.

Las plantillas de comercio separan `purchase_unit_cost` del costo total. El
COGS se calcula como costo unitario por ventas realizadas y el contrato
financiero reconcilia unidades, precio, ingreso y costo variable; un stockout
reduce tanto el ingreso como el costo de mercadería vendida.

Los ids de `processes` y `services` representan throughput realizado y están
disponibles como símbolos seguros después de calcular capacidad. Las
plantillas productivas conectan ese throughput con BOM, COGS e ingresos; las
plantillas de servicios conectan atenciones realizadas con ingresos. La
demanda que supera capacidad queda en `unmet_demand` y no genera producción,
consumo de materiales ni facturación ficticia.

## Unidades y procedencia

La primera tabla de unidades cubre `Bs`, `USD`, `kg`, `g`, `liter`, `ml`,
`minute`, `hour`, `day`, `unit`, `person`, `machine` y `%`. Solo se convierten
unidades de la misma dimensión. Los valores declaran procedencia, por ejemplo
`USER_ENTERED`, `IMPORTED`, `HISTORICAL_BUSINESS_DATA`, `PUBLIC_SOURCE`,
`ESTIMATED`, `SIMULATED` o `AI_SUGGESTED`.

Las expresiones declaradas también se validan dimensionalmente: los términos
sumados o restados deben ser compatibles, mientras que operaciones habituales
como `precio * cantidad` siguen siendo válidas. Costos e ingresos mantienen
una forma canónica de lista para que el editor y el runtime compartan el mismo
contrato.

`financial` es opcional y solo conecta entradas explícitas con el resumen
financiero: unidades/precio/costo unitario para break-even, inversión para ROI,
flujos de caja para cash flow y activos/pasivos corrientes para working capital.
Cada valor puede ser numérico o una expresión segura referida a símbolos del
modelo. Si falta una entrada o no coincide con ingresos/costos declarados, la
métrica no se presenta como válida.

## Paradigmas

La capa actual expone un runtime determinista de stocks/flows, Monte Carlo y
un adaptador DES acotado para colas/capacidad. El DES reconoce capacidad,
disponibilidad, downtime, fallo, retrabajo y scrap de los pasos, y reporta cada
resultado explícitamente. Cada engine conserva semántica temporal y resumen
propios; ABM sigue siendo una extensión opcional y no se presenta un modelo
causal como si fuera una ecuación numérica.

El puente DES heredado recibe la desviación de demanda desde el histórico o la
configuración Monte Carlo y conserva su procedencia en el escenario/resultado.
El motor escalar y la ruta vectorizada usan el mismo valor y el guard de
paridad los compara bajo ese contrato. Una ventana simulada reemplaza esa
dispersión únicamente cuando existen al menos dos períodos previos; sin fuente,
la incertidumbre queda no disponible y no se inventa como porcentaje.

Además del producto/BOM o servicio, el DSL puede representar proveedores,
canales de venta, roles de personal y nodos de inventario. Son estructuras
configurables y editables; no implican datos económicos por defecto.

Las relaciones de `causal_links` son explicativas: tienen origen, destino y
polaridad `positive`/`negative`. Los bucles se clasifican como `REINFORCING` o
`BALANCING`, pero no se ejecutan numéricamente sin una ecuación explícita.

## Puente con modelos heredados

El runtime heredado ya no carga valores económicos u operativos desde
`variable_test_data`: ese archivo es un fixture histórico, no una fuente de
verdad empresarial. Las respuestas del cuestionario tienen prioridad y los
valores ausentes permanecen ausentes. Los demos sembrados pueden completar
parámetros por producto únicamente dentro de un sobre
`SYNTHETIC_TEMPLATE` en `CompanyProfile.custom_kpis`; el sobre declara sus
valores y, cuando corresponde, ecuaciones seguras acotadas.

Las plantillas de servicio usan un contrato de demanda/capacidad, ingreso y
costos directos de servicio. No ejecutan ecuaciones de inventario físico,
mermas, cadena de frío o BOM manufacturero. Las ecuaciones del puente pasan por
los mismos evaluadores AST allow-list del motor escalar/vectorizado y no
habilitan Python arbitrario. Este puente conserva demos heredados mientras el
DSL versionado sigue siendo la fuente canónica para modelos nuevos.

## Finanzas

El contrato `modeling.financial` usa `Decimal` para dinero y exige separar
precio, COGS/costo de ventas, costo variable y costo fijo. Las líneas de costo
aceptan `COGS`, `VARIABLE` o `FIXED`; si se declara COGS, la utilidad bruta lo
resta y el margen de contribución resta COGS más los costos variables. Calcula
ingresos, costos, utilidad bruta, resultado operativo, márgenes, break-even y ROI únicamente cuando existen
los insumos correspondientes; un break-even imposible o un ROI sin inversión
se devuelve como `null`, no como un valor inventado.

También acepta entradas explícitas para flujo de caja y capital de trabajo:
`cash_inflows`, `cash_outflows`, `opening_cash`, `current_assets` y
`current_liabilities`. Si faltan entradas requeridas, `cash_flow`, `ending_cash`
o `working_capital` permanecen en `null`.

### Contrato del reporte financiero heredado

El creador de reportes conserva compatibilidad, pero ahora persiste las
suposiciones realmente enviadas por el propietario y su procedencia. Usa `Bs`,
períodos mensuales y horizonte de 1–120 meses. Sus métricas se definen así:

- `ROI`: retorno neto de caja de todo el horizonte dividido por inversión
  inicial; es N/A cuando la inversión es cero o falta.
- `VAN`: anualidad de flujos mensuales descontada con una tasa nominal anual
  explícita del formulario; no existe tasa oculta.
- `TIR`: raíz mensual que hace VAN cero, presentada como tasa anual efectiva;
  es N/A cuando no existe un contrato de inversión/flujo positivo aplicable.
- `payback_period`: inversión dividida por flujo mensual positivo, en meses;
  es N/A cuando el flujo no recupera capital.

El frontend de vista previa replica ROI/payback y no aplica inflación ni
impuestos hasta que esas relaciones tengan un contrato explícito. Los valores
de plantilla se etiquetan `TEMPLATE_DEFAULT`; los enviados por formulario,
`USER_ENTERED`.

## Referencias de diseño

La inspiración visual y conceptual es el modelado de stocks/flows,
retroalimentación y experimentos interactivos documentado públicamente por
isee systems para Stella/iThink. No se copia código, activos ni UI
propietaria. Prometheus se mantiene separado como observabilidad: sus series
etiquetadas sirven para telemetría de simulaciones, no como variables de
negocio ni como fuente contable.
