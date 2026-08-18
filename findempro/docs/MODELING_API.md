# API de modelado

Todas las rutas requieren sesión autenticada y filtran por
`Business.fk_user`.

| Ruta | Uso |
|---|---|
| `GET, POST /modeling/businesses/` | Listar o crear empresas del usuario; `sector` solo clasifica y sugiere plantillas |
| `GET, POST /modeling/templates/` | Listar plantillas built-in y propias, o publicar una plantilla propia tras validación DSL |
| `GET, POST /modeling/models/` | Listar o crear definición y versión |
| `GET /modeling/models/{id}/` | Ver definición, versión actual e historial |
| `GET /modeling/models/{id}/export/` | Descargar el envoltorio JSON de la versión inmutable, incluyendo hash, validación y DSL |
| `POST /modeling/models/{id}/validate/` | Validar una especificación sin persistirla |
| `GET /modeling/models/{id}/diagrams/` | Proyecciones derivadas de BOM, procesos, causalidad, stock/flow, recursos y finanzas |
| `POST /modeling/models/{id}/versions/` | Crear una versión inmutable |
| `GET, POST /modeling/models/{id}/scenarios/` | Listar o crear cambios explícitos |
| `POST /modeling/models/{id}/simulate/` | Encolar una ejecución con `engine=monte_carlo|system_dynamics|discrete_event`; aplica el límite configurable de ejecuciones activas por propietario |
| `POST /modeling/models/{id}/sensitivity/` | Sensibilidad one-at-a-time con cambios aditivos explícitos; acepta `engine` y `metric` (`profit` por defecto, o `completed`, `queue_end`, `utilization` para modelos de eventos) |
| `POST /modeling/models/{id}/distribution-fit/` | Proponer ajustes acotados para observaciones; no publica ni muta la versión |
| `GET /modeling/runs/{id}/` | Consultar progreso y resultado |
| `GET /modeling/runs/compare/?ids={id1},{id2}` | Comparar 2–10 ejecuciones completadas de la misma versión con deltas financieros, incertidumbre, demanda no atendida y nivel de servicio |
| `POST /modeling/runs/{id}/cancel/` | Cancelar cooperativamente una ejecución queued/running del propietario |

La ejecución asíncrona sigue `queued → running → completed|failed` y expone
progreso de fase (10% al iniciar, 20% al preparar el engine, 80% al terminar el
cálculo, 100% al persistir el resultado).
El límite `MODELING_MAX_ACTIVE_RUNS` tiene valor predeterminado 4 por propietario;
cuando se alcanza, la API responde `429 simulation_capacity_reached` con una
acción correctiva explícita. La base
de datos es la verdad del resultado; Celery/Redis solo coordinan el trabajo y
el estado transitorio.

La validación devuelve `complexity` con nodos, aristas y máximos efectivos.
`MODELING_MAX_MODEL_NODES` (1.000 por defecto) y
`MODELING_MAX_MODEL_EDGES` (5.000 por defecto) se aplican antes de la
validación profunda y compilación. El exceso produce los códigos accionables
`model_node_limit` o `model_edge_limit`; no se persiste una versión inválida.
Las expresiones también se acotan por longitud, número de nodos AST y
profundidad con `MODELING_MAX_EXPRESSION_LENGTH` (500),
`MODELING_MAX_EXPRESSION_NODES` (200) y `MODELING_MAX_EXPRESSION_DEPTH` (40).
Una fórmula que supera esos límites se devuelve como `unsafe_expression` con
una explicación accionable y no alcanza el compilador.

Los imports están limitados a 10.000 filas y 2 MB por archivo. El mapping es
`columna_origen → id_de_variable` y sus destinos deben existir en la versión
inmutable; los destinos desconocidos se rechazan. Se puede enviar
`preview=true` para recibir hasta 25 filas y errores sin crear un recibo. Cada recibo
queda ligado a una versión inmutable y marca la procedencia como `IMPORTED`.
Las filas inválidas se conservan en `error_rows`; nunca se mezclan
silenciosamente con las filas válidas. La ruta es:
`POST /modeling/models/{id}/imports/`.

La sensibilidad usa la misma versión, semilla y número de iteraciones para la
línea base y cada perturbación. La respuesta identifica el hash de la versión
y ordena los factores por efecto absoluto sobre la media simulada.

El laboratorio de distribuciones acepta entre 5 y 10.000 observaciones finitas
y candidatos compatibles con su soporte (`normal`, `lognormal`, `gamma`,
`exponential`, `uniform`, `poisson`). Devuelve parámetros, log-likelihood, AIC,
BIC, un diagnóstico de distancia, cuantiles, candidatos rechazados y
`requires_review=true`. El método `distribution_fit_v2` publica `p_value=null`
para ajustes continuos hechos sobre la misma muestra y para el diagnóstico
discreto Poisson no calibrado; nunca rellena ese campo con una aproximación.
El ranking AIC/BIC solo elige candidato cuando las familias likelihood son
comparables; una mezcla continua/discreta devuelve ganador `null`.
El resultado es una propuesta con procedencia `USER_ENTERED_OBSERVATIONS`; no
se copia automáticamente al DSL ni altera datos históricos.

Las plantillas creadas por usuarios quedan ligadas a `created_by` y solo son
visibles para su propietario; las plantillas built-in son sintéticas y
compartidas. Crear una plantilla no la convierte en una verdad de negocio:
sus parámetros siguen requiriendo confirmación y procedencia explícita.

Los cambios de escenario solo pueden referirse a variables, parámetros, stocks
o destinos de distribución declarados en la versión. Se rechazan referencias
desconocidas y valores no finitos antes de guardar o ejecutar.

El DSL también admite estructuras configurables de `suppliers`,
`sales_channels`, `employee_roles` e `inventory_nodes`; los componentes de BOM
pueden referir un `supplier_id`, y una referencia no declarada se rechaza antes
de persistir la versión.
