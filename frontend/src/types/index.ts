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

export interface SimulationResult {
  demand: { mean: number; std: number; var_95: number; cvar_95: number; distribution: number[] }
  revenue: { mean: number; std: number; percentile_5: number; percentile_95: number }
  profit: { mean: number; std: number; var_95: number; cvar_95: number; sharpe_ratio: number | null; ratio_basis?: string }
  risk: { var_level: number; cvar_level: number; probability_of_loss: number; risk_category: string; confidence_level?: number; var_confidence_level?: number; cvar_confidence_level?: number }
  scenarios: { pessimist: ScenarioData; base: ScenarioData; optimist: ScenarioData }
  time_series: { demand: number[]; revenue: number[]; profit: number[]; periods: string[] }
  metadata: { n_iterations: number; confidence_level: number; distribution_type: string; execution_time: number }
}

export interface ScenarioData {
  demand: number
  revenue: number
  profit: number
  probability: number
}

export interface ForecastRequest {
  historical_data: number[]
  periods: number
  method: 'auto' | 'linear' | 'moving_average' | 'exponential_smoothing'
  confidence_level: number
  include_analysis: boolean
}

export interface ForecastResult {
  forecast: number[]
  confidence_intervals: { lower: number[]; upper: number[] }
  trend: string
  method_used: string
  metrics: { mae: number; rmse: number; mape: number }
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
