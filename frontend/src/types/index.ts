export interface Business {
  id: number
  name: string
  type: number
  type_display?: string
  fk_user?: number
  is_active: boolean
  date_created: string
  last_updated: string
}

export interface DashboardData {
  businesses_count: number
  simulations_count: number
  products_count: number
  recent_simulations: SimulationSummary[]
  risk_alerts?: RiskAlert[]
}

export interface DashboardSummary {
  total_businesses: number
  active_simulations: number
  pending_alerts: number
  latest_simulation?: SimulationSummary
}

export interface SimulationSummary {
  id: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  date_created: string
  quantity_time: number
  unit_time: string
  confidence_level: number
}

export interface RiskAlert {
  id: number
  level: 'high' | 'medium' | 'low'
  message: string
  created_at: string
}

export interface SimulationRequest {
  business_id?: number
  demand_mean: number
  demand_std: number
  unit_price: number
  unit_cost: number
  fixed_costs: number
  distribution_type: 'normal' | 'lognormal' | 'gamma' | 'uniform' | 'exponential'
  n_iterations: number
  time_periods: number
  confidence_level: number
  random_seed?: number
  seasonality_factors?: number[]
}

/**
 * Contrato de `POST /simulate/api/v1/simulate/` y del `result` que devuelve
 * `.../simulate/status/<task_id>/`.
 *
 * Esta interfaz describía una forma que el servidor nunca emitió: `scenarios`
 * como objeto con claves fijas, `time_series` como columnas paralelas,
 * `revenue.percentile_5`, `metadata.distribution_type`, `risk.risk_category`.
 * `Simulate.tsx` leía esos caminos sin guardas y se caía en el render con cada
 * simulación que terminaba bien. Lo de aquí es ahora la forma real, fijada del
 * lado del servidor por `findempro/simulate/tests/test_api_v1_wire_contract.py`.
 */
export interface SimulationResult {
  demand: {
    mean: number; std: number; median: number
    p5: number; p25: number; p75: number; p95: number
    ci_lower: number; ci_upper: number
  }
  revenue: { mean: number; std: number; p5: number; p95: number }
  profit: {
    mean: number; std: number; median: number
    p5: number; p95: number
    var_95: number; cvar_95: number
    /** `null` para beneficio monetario: no es una serie de retornos periodizados. */
    sharpe_ratio: number | null
    ratio_basis: string
    var_semantics: string
    cvar_semantics: string
    ci_lower: number; ci_upper: number
  }
  risk: {
    probability_of_loss: number
    probability_breakeven: number
    confidence_level: number
    var_confidence_level: number
    cvar_confidence_level: number
    var_semantics: string
    cvar_semantics: string
    value_at_risk_95: number
    expected_shortfall: number
  }
  /** Cinco escenarios ordenados por demanda creciente. Es una lista, no un objeto. */
  scenarios: ScenarioData[]
  /** Un punto por período simulado. Es una lista, no columnas paralelas. */
  time_series: TimeSeriesPoint[]
  metadata: { n_iterations: number; distribution_used: string; confidence_level: number }
}

export interface ScenarioData {
  name: string
  demand_percentile: number
  demand_value: number
  revenue: number
  total_costs: number
  gross_profit: number
  profit_margin_pct: number
  roi: number | null
}

export interface TimeSeriesPoint {
  period: number
  seasonality_factor: number
  demand_mean: number
  demand_p5: number
  demand_p95: number
  revenue_mean: number
  profit_mean: number
  profit_p5: number
  profit_p95: number
}

export interface ForecastRequest {
  historical_data: number[]
  periods: number
  method: 'auto' | 'linear' | 'moving_average' | 'exponential_smoothing'
  confidence_level: number
  include_analysis: boolean
}

/**
 * Contrato de `POST /simulate/api/v1/forecast/`.
 *
 * `forecast` es un OBJETO con series paralelas, no un array de valores:
 * `Forecast.tsx` hacía `result.forecast.map(...)` y se caía con
 * «forecast.map is not a function» en cada pronóstico.
 *
 * `mape` es `null` cuando el holdout tiene observaciones en cero (el error
 * relativo no está definido contra cero y el servidor no lo inventa); `rmse`
 * queda definido siempre y va en unidades de la demanda.
 */
export interface ForecastResult {
  forecast: {
    periods: number
    values: number[]
    ci_lower: number[]
    ci_upper: number[]
    method_used: string
    confidence_level: number
    mape: number | null
    rmse: number | null
  }
  simulation_params: {
    distribution_type: SimulationRequest['distribution_type']
    demand_mean: number
    demand_std: number
    demand_min?: number
    demand_max?: number
    trend_slope?: number
    trend_r2?: number
  }
}

export interface Report {
  id: number
  title: string
  status: string
  date_created: string
  last_updated: string
  is_active: boolean
}

export interface ModelVersion {
  id: string
  definition_id: string
  version: number
  schema_version: string
  status: string
  content_hash: string
  spec: Record<string, unknown>
  validation?: { readiness?: ModelReadiness }
  created_at: string
}

export interface ModelReadiness {
  score: number
  missing: string[]
  dimensions?: Record<string, boolean>
  actions?: Record<string, string>
}

export interface BusinessModel {
  id: string
  name: string
  business_id: number
  business_name: string
  description?: string
  sector: string
  status: string
  current_version?: number | ModelVersion
  readiness?: ModelReadiness
}

export interface ModelTemplate {
  slug: string
  name: string
  sector: string
  description: string
  spec: Record<string, unknown>
  provenance: Record<string, unknown>
}
