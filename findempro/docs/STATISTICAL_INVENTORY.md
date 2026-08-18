# Inventario estadístico y de simulación

Este inventario distingue el runtime canónico de modelos nuevos de los
servicios históricos que todavía alimentan pantallas existentes. Ninguna
salida se interpreta como una garantía de realidad empresarial.

| Módulo | Modelo/distribución | Objetivo | Datos y N | Semilla | Validación | Estado |
|---|---|---|---|---|---|---|
| `modeling.engine.run_system_dynamics` | Stocks/flows deterministas; distribuciones declaradas | Evolución por período, ingresos, costos y utilidad | Especificación versionada; horizonte configurable | RNG inyectado | DSL, referencias, ciclos y unidades | Canónico |
| `modeling.engine.run_monte_carlo` | Empírica, normal, lognormal, Poisson, binomial negativa, gamma, uniforme, GBM | Distribución de utilidad bajo incertidumbre | Modelo versionado; `iterations` limitado a 100.000 | `numpy.Generator` derivado de semilla maestra | Validación DSL; percentiles P5/P50/P95; reproducibilidad | Canónico |
| `modeling.engine.DiscreteEventEngine` / DES legacy escalar-vectorizado | Llegadas, servicio, cola y capacidad en períodos discretos | Throughput, cola y utilización | Demanda y pasos/procesos configurados; dispersión histórica/configurada explícita | Contrato acepta semilla; el adaptador canónico no usa aleatoriedad actualmente | Referencias, tiempos, capacidad; DES legacy comparte `demand_std` y procedencia entre escenario, scalar, vector y guard de paridad | Revisado |
| `modeling.engine.run_sensitivity` | One-at-a-time, cambio aditivo explícito | Efecto sobre media de utilidad | Mismo modelo, N y semilla por baseline/factor | Reutilizada | Comparación pareada con semilla fija | Canónico |
| `simulate.services.simulation_engine.MonteCarloEngine` / `simulate.utils.simulation_core_utils.SimulationCore` | Distribución elegida por simulación histórica/legacy; incluye GBM | Demand, revenue, gross profit y riesgo | Configuración y observaciones históricas de demanda; N configurable | `numpy.Generator` por configuración | Historia positiva/finita obligatoria; predicción positiva/finita; fuente de dispersión persistida; distribución y percentiles | Legacy activo, fallbacks fabricados cerrados |
| `simulate.core.decision_engine` | Percentiles, momentos y cola inferior de utilidad monetaria | Riesgo condicional de resultados simulados | Muestras monetarias de escenarios; N del Monte Carlo | Hereda muestras del engine | Confianza explícita; VaR=`lower_profit_quantile`, CVaR=`lower_tail_mean_profit`; Sharpe/Sortino N/A sin retornos; forma N/A para muestras insuficientes/degeneradas | Revisado |
| `modeling.statistics` / consumidores legacy de ajuste | Normal, lognormal, exponencial, gamma, uniforme y Poisson | Ajustar candidatos sin fabricar evidencia inferencial | 5–10.000 observaciones finitas; semántica continua o de conteo explícita | No aplica; ajuste determinista | `distribution_fit_v2`: distancia KS continua o distancia máxima CDF discreta; p-value no disponible; ranking AIC/BIC solo dentro de familia likelihood comparable | Revisado |
| `simulate.services.demand_model.DemandModel` | Ajustes candidatos continuos; pronóstico lineal/media móvil/suavizamiento exponencial | Demanda histórica y forecast | Serie temporal proporcionada; N depende de datos | No aplica al ajuste; forecast determinista | AIC para selección comparable; KS solo como distancia descriptiva; holdout temporal para forecast | Revisado |
| `simulate.services.context_manager` / `validation_service` | Normal, lognormal, exponencial, gamma; Shapiro, t, F, KS-2, Pearson, Kendall | Comparar histórico, simulado y proyectado | Series históricas y simuladas; tamaño variable | Proyecciones estocásticas usan el RNG aislado de la simulación | GOF post-ajuste usa `distribution_fit_v2`; no convierte p-value ausente en aprobación, confianza o recomendación | Revisión parcial; otros diagnósticos legacy siguen pendientes |
| `report.tasks._extract_persisted_profit_summary` | Resumen descriptivo, sin reconstrucción de muestras | Reportar media/P5/P95 persistidos por período | Solo períodos con resumen finito y orden P5 ≤ media ≤ P95 | No aplica | `simulation_report_summary_v2`; VaR, CVaR y P(pérdida) quedan N/A sin muestras originales | Revisado |

## Contrato requerido por método

Cada nuevo engine debe documentar: semántica temporal, unidad de cada entrada y
salida, origen/proveniencia de datos, tamaño de muestra, semilla o razón de no
aplicar, método de ajuste, validación, límites y significado empresarial.

## Riesgos abiertos

- Las vistas activas de resultados ya no generan series aleatorias cuando
  faltan observaciones: muestran `NO DISPONIBLE`. Los assets históricos no
  enlazados se conservan solo como evidencia académica y no alimentan runtime.
- El reporte de simulación ya no reconstruye muestras normales desde
  media/P5/P95. Sin muestras Monte Carlo originales no publica VaR, CVaR ni
  probabilidad de pérdida; conserva un conteo descriptivo de períodos cuya
  utilidad media fue negativa.
- El forecast API selecciona el método con un holdout temporal entrenado solo
  con el prefijo disponible. La predicción final puede ajustar toda la historia
  suministrada porque su origen es el final de esa serie; el frontend grafica
  exactamente la historia enviada, no el ejemplo inicial.
- El ajuste de distribuciones históricas debe separar entrenamiento y
  evaluación temporal cuando exista una serie con fecha; no se debe usar el
  futuro para calibrar el pasado.
- La validación legacy de predicciones conserva el orden temporal y descarta
  el par completo si la predicción o la observación no es numérica o finita.
  MAPE queda no disponible si todas las observaciones válidas son cero; MAE y
  el recuento de descartes permanecen explícitos.
- El motor escalar legacy ya no inventa demanda `2500`, volatilidad de 10% ni
  ruido aleatorio cuando falta historia o falla el muestreo. La ejecución
  exige historia positiva/finita, rechaza predicciones no positivas y persiste
  si la dispersión procede de observaciones históricas o de una ventana
  simulada. Si todos los períodos fallan, la corrida falla explícitamente.
- DES escalar y vectorizado ya no definen `DSD` como 10% de la demanda. Usan
  dispersión histórica/configurada con procedencia, o una ventana simulada
  solo desde dos períodos previos. Sin fuente, `DSD/CVD` quedan ausentes; una
  dispersión negativa o no finita se rechaza.
- Asimetría y curtosis comparten un cálculo central normalizado entre riesgo,
  demanda y vistas legacy. Las series con menos de tres observaciones o sin
  variación numéricamente identificable devuelven `null` y un estado explícito,
  no `NaN`, cero fabricado ni una recomendación sobre colas inexistentes.
- Las pruebas estadísticas describen compatibilidad de muestras, no prueban que
  una distribución sea verdadera ni que el modelo prediga el negocio.
- `distribution_fit_v2` rechaza muestras insuficientes, constantes, no finitas
  o incompatibles con el soporte. Para familias continuas conserva la distancia
  KS real pero deja el p-value en `null`, porque los parámetros se estimaron con
  la misma muestra. Para Poisson usa una distancia entre CDF empírica y discreta,
  nunca el KS continuo. No se ejecuta bootstrap en el request path.
- AIC/BIC se calculan desde el likelihood ajustado y solo ordenan candidatos de
  una misma familia de likelihood. Una mezcla de candidatos continuos y de
  conteo devuelve ranking no comparable y no elige ganador.
- Sharpe/Sortino permanecen explícitamente N/A para utilidad monetaria cruda;
  solo podrían habilitarse con una serie de retornos periodizados y una tasa
  libre de riesgo dimensionalmente compatible.
- VaR/CVaR legacy conservan valores firmados de utilidad para compatibilidad:
  cuantil inferior y media de cola inferior. No son una magnitud positiva de
  pérdida y API, dashboard y reporte declaran esa semántica.
