import type { DashboardData, DashboardSummary, SimulationRequest, SimulationResult, ForecastRequest, ForecastResult, Report, BusinessModel, ModelTemplate, ModelVersion, ModelReadiness } from '@/types'

const DJANGO_LOGIN = '/account/login/'

function getCsrf(): string {
  return document.cookie.split('; ').find((r) => r.startsWith('csrftoken='))?.split('=')[1] ?? ''
}

function headers(extra: Record<string, string> = {}): HeadersInit {
  return {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCsrf(),
    'Accept': 'application/json',
    ...extra,
  }
}

async function handle<T>(res: Response): Promise<T> {
  if (res.status === 401 || res.status === 403) {
    window.location.href = `${DJANGO_LOGIN}?next=${encodeURIComponent(window.location.pathname)}`
    throw new Error('Not authenticated')
  }
  if (!res.ok) {
    const text = await res.text().catch(() => `HTTP ${res.status}`)
    let msg = text
    try {
      const payload = JSON.parse(text) as { detail?: string; message?: string; error?: string; how_to_fix?: string }
      msg = payload.message ?? payload.detail ?? payload.error ?? msg
      if (payload.how_to_fix) msg += ` Cómo corregirlo: ${payload.how_to_fix}`
    } catch { /* raw */ }
    throw new Error(msg)
  }
  const ct = res.headers.get('content-type') ?? ''
  if (ct.includes('application/json')) return res.json() as Promise<T>
  return res.text() as unknown as T
}

export async function checkAuth(): Promise<boolean> {
  const res = await fetch('/health/', { credentials: 'include' })
  return res.ok
}

export async function getDashboardData(): Promise<DashboardData> {
  const res = await fetch('/api/dashboard-data/', { credentials: 'include', headers: headers() })
  return handle<DashboardData>(res)
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const res = await fetch('/api/summary/', { credentials: 'include', headers: headers() })
  return handle<DashboardSummary>(res)
}

/** Espera `ms` milisegundos. */
function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

interface TaskStatus {
  state: 'pending' | 'SUCCESS' | 'FAILURE'
  progress?: number
  result?: SimulationResult
  error?: string
}

/**
 * Ejecuta la simulación Monte Carlo SIN bloquear el worker gunicorn:
 * encola la tarea en Celery (202 → task_id) y hace polling del estado hasta
 * que termina. Mantiene la firma `Promise<SimulationResult>` para que los
 * consumidores (p.ej. Simulate.tsx) no cambien.
 *
 * @param payload  parámetros de la simulación
 * @param onProgress  callback opcional de progreso (0-100)
 */
export async function runSimulation(
  payload: SimulationRequest,
  onProgress?: (progress: number) => void,
): Promise<SimulationResult> {
  const enqueueRes = await fetch('/simulate/api/v1/simulate/async/', {
    method: 'POST',
    credentials: 'include',
    headers: headers(),
    body: JSON.stringify(payload),
  })
  const { task_id: taskId, status_url: statusUrl } = await handle<{
    task_id: string
    status: string
    status_url: string
  }>(enqueueRes)

  const pollUrl = statusUrl ?? `/simulate/api/v1/simulate/status/${taskId}/`
  const POLL_INTERVAL_MS = 1000
  const MAX_ATTEMPTS = 300 // ~5 min

  for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
    await delay(POLL_INTERVAL_MS)
    const statusRes = await fetch(pollUrl, { credentials: 'include', headers: headers() })
    const status = await handle<TaskStatus>(statusRes)

    if (typeof status.progress === 'number') onProgress?.(status.progress)

    if (status.state === 'SUCCESS') {
      if (!status.result) throw new Error('La simulación terminó sin resultado.')
      return status.result
    }
    if (status.state === 'FAILURE') {
      throw new Error(status.error ?? 'La simulación falló.')
    }
  }

  throw new Error('La simulación excedió el tiempo máximo de espera (5 min).')
}

export async function runForecast(payload: ForecastRequest): Promise<ForecastResult> {
  const res = await fetch('/simulate/api/v1/forecast/', {
    method: 'POST',
    credentials: 'include',
    headers: headers(),
    body: JSON.stringify(payload),
  })
  return handle<ForecastResult>(res)
}

export async function getSimulationProgress(id: number): Promise<{ status: string; progress: number; message: string }> {
  const res = await fetch(`/simulate/api/progress/${id}/`, { credentials: 'include' })
  return handle(res)
}

export async function getReports(): Promise<Report[]> {
  const res = await fetch('/report/api/list/', { credentials: 'include', headers: headers() })
  return handle<Report[]>(res)
}

export async function getBusinessDetails(id: number) {
  const res = await fetch(`/business/api/details/${id}/`, { credentials: 'include' })
  return handle(res)
}

/**
 * Pipeline completo (Monte Carlo → Eventos Discretos → Motor de Decisión) sobre
 * una **Simulation** ya guardada.
 *
 * Recibía un `businessId` y lo mandaba a una ruta que resuelve por
 * `simulation_id`: el backend busca la Simulation del usuario con ese pk y, al
 * no coincidir los espacios de identificadores, sólo podía devolver 404
 * «Simulación no encontrada». Nunca ejecutó nada.
 */
export async function runFullPipeline(simulationId: number) {
  const res = await fetch(`/simulate/api/v1/full-pipeline/${simulationId}/`, {
    method: 'POST',
    credentials: 'include',
    headers: headers(),
    body: JSON.stringify({}),
  })
  return handle(res)
}

export async function runRiskAnalysis(payload: { business_id?: number; profit_data: number[]; historical_periods?: number; var_percentile?: number; confidence_level?: number }) {
  const res = await fetch('/simulate/api/v1/risk-analysis/', {
    method: 'POST',
    credentials: 'include',
    headers: headers(),
    body: JSON.stringify(payload),
  })
  return handle(res)
}

export async function runScenarios(payload: { business_id?: number; base_demand: number; base_price: number; base_cost: number; fixed_costs: number }) {
  const res = await fetch('/simulate/api/v1/scenarios/', {
    method: 'POST',
    credentials: 'include',
    headers: headers(),
    body: JSON.stringify(payload),
  })
  return handle(res)
}

export async function getBusinessModels(): Promise<{ models: BusinessModel[] }> {
  const res = await fetch('/modeling/models/', { credentials: 'include', headers: headers() })
  return handle(res)
}

export async function getOwnedBusinesses(): Promise<{ businesses: { id: number; name: string; sector: string }[] }> {
  const res = await fetch('/modeling/businesses/', { credentials: 'include', headers: headers() })
  return handle(res)
}

export async function createBusiness(payload: { name: string; location: string; sector: string; description?: string }) {
  const res = await fetch('/modeling/businesses/', { method: 'POST', credentials: 'include', headers: headers(), body: JSON.stringify(payload) })
  return handle<{ business: { id: number; name: string; sector: string; type: number } }>(res)
}

export async function createModelTemplate(payload: { name: string; slug?: string; sector: string; description?: string; spec: Record<string, unknown> }) {
  const res = await fetch('/modeling/templates/', { method: 'POST', credentials: 'include', headers: headers(), body: JSON.stringify(payload) })
  return handle<{ template: ModelTemplate }>(res)
}

export async function createBusinessModel(payload: { business_id: number; name: string; sector: string; spec: Record<string, unknown> }) {
  const res = await fetch('/modeling/models/', { method: 'POST', credentials: 'include', headers: headers(), body: JSON.stringify(payload) })
  return handle<{ model: BusinessModel & { version: ModelVersion } }>(res)
}

export async function getBusinessModel(id: string): Promise<BusinessModel & { current_version?: ModelVersion; versions: ModelVersion[] }> {
  const res = await fetch(`/modeling/models/${id}/`, { credentials: 'include', headers: headers() })
  return handle(res)
}

export async function getModelTemplates(): Promise<{ templates: ModelTemplate[] }> {
  const res = await fetch('/modeling/templates/', { credentials: 'include', headers: headers() })
  return handle(res)
}

export async function validateBusinessModel(id: string, spec: Record<string, unknown>) {
  const res = await fetch(`/modeling/models/${id}/validate/`, {
    method: 'POST', credentials: 'include', headers: headers(), body: JSON.stringify({ spec }),
  })
  return handle<{ valid: boolean; errors: { path: string; code: string; message: string }[]; warnings: { path: string; code: string; message: string }[]; readiness: ModelReadiness }>(res)
}

export async function createModelVersion(id: string, spec: Record<string, unknown>) {
  const res = await fetch(`/modeling/models/${id}/versions/`, { method: 'POST', credentials: 'include', headers: headers(), body: JSON.stringify({ spec, status: 'validated' }) })
  return handle<{ version: ModelVersion }>(res)
}

export interface ModelDiagram {
  title: string
  nodes: { id: string; label: string; kind: string; [key: string]: unknown }[]
  edges: { source: string; target: string; relation: string; [key: string]: unknown }[]
}

export async function getModelDiagrams(id: string): Promise<{ model_id: string; version: number | null; diagrams: Record<string, ModelDiagram> }> {
  const res = await fetch(`/modeling/models/${id}/diagrams/`, { credentials: 'include', headers: headers() })
  return handle(res)
}

export interface ModelScenario { id: string; name: string; label: string; changes: Record<string, number> }

export async function getModelScenarios(id: string): Promise<{ scenarios: ModelScenario[] }> {
  const res = await fetch(`/modeling/models/${id}/scenarios/`, { credentials: 'include', headers: headers() })
  return handle(res)
}

export async function createModelScenario(id: string, payload: { name: string; label: string; changes: Record<string, number> }) {
  const res = await fetch(`/modeling/models/${id}/scenarios/`, { method: 'POST', credentials: 'include', headers: headers(), body: JSON.stringify(payload) })
  return handle<{ scenario: ModelScenario }>(res)
}

export interface ModelSensitivityResult {
  engine: 'one_at_a_time_sensitivity'
  simulation_engine?: 'monte_carlo' | 'system_dynamics' | 'discrete_event'
  metric?: 'profit' | 'completed' | 'queue_end' | 'utilization'
  seed: number | null
  iterations: number
  baseline: Record<string, number>
  factors: { variable: string; change: number; baseline_mean: number; perturbed_mean: number; effect: number }[]
}

export async function runModelSensitivity(id: string, payload: { changes: Record<string, number>; iterations: number; seed: number; engine?: 'monte_carlo' | 'system_dynamics' | 'discrete_event'; metric?: 'profit' | 'completed' | 'queue_end' | 'utilization' }): Promise<{ model_version: number; content_hash: string; result: ModelSensitivityResult }> {
  const res = await fetch(`/modeling/models/${id}/sensitivity/`, { method: 'POST', credentials: 'include', headers: headers(), body: JSON.stringify(payload) })
  return handle(res)
}

export interface DistributionFitCandidate {
  distribution: string
  family: 'continuous' | 'discrete'
  parameters: Record<string, number>
  fit_method: string
  method_version: string
  log_likelihood: number
  aic: number
  bic: number
  statistic: number
  ks_statistic: number | null
  p_value: number | null
  test_name: string
  p_value_unavailable_reason: string | null
  valid: boolean
  assumptions: string[]
  warnings: string[]
  sample_size: number
}

export interface DistributionFitResult {
  method: string
  quantiles: Record<string, number>
  candidates: DistributionFitCandidate[]
  rejected: { distribution: string; reason: string }[]
  ranking: { criterion: string; comparable: boolean; selected_distribution: string | null; unavailable_reason: string | null }
  provenance: string
  requires_review: boolean
}

export async function fitModelDistributions(id: string, observations: number[], candidates?: string[], dataSemantics: 'continuous' | 'count' = 'continuous'): Promise<DistributionFitResult> {
  const res = await fetch(`/modeling/models/${id}/distribution-fit/`, {
    method: 'POST', credentials: 'include', headers: headers(),
    body: JSON.stringify({ observations, candidates, data_semantics: dataSemantics }),
  })
  return handle(res)
}

export async function runBusinessModel(id: string, payload: { iterations: number; seed: number; engine?: 'monte_carlo' | 'system_dynamics' | 'discrete_event'; scenario_id?: string }) {
  const res = await fetch(`/modeling/models/${id}/simulate/`, { method: 'POST', credentials: 'include', headers: headers(), body: JSON.stringify(payload) })
  const queued = await handle<{ run_id: string; status_url: string }>(res)
  for (let attempt = 0; attempt < 60; attempt += 1) {
    const statusRes = await fetch(queued.status_url, { credentials: 'include', headers: headers() })
    const status = await handle<{ status: string; progress: number; result?: { summary: Record<string, number> }; error?: ModelRunHistory['error'] }>(statusRes)
    if (status.status === 'completed') return status.result
    if (status.status === 'failed') throw new Error(status.error?.message ?? 'La simulación falló.')
    await new Promise((resolve) => setTimeout(resolve, 250))
  }
  throw new Error('La simulación excedió el tiempo de espera.')
}

export interface ImportReceipt {
  id: string
  status: 'validated' | 'rejected'
  rows_imported: number
  error_rows: { row: number; error: string }[]
  provenance: { kind: string; source_name: string; format: string }
}

export async function importModelFile(
  modelId: string,
  file: File,
  format: 'json' | 'csv' | 'xlsx',
  mapping: Record<string, string> = {},
): Promise<{ import: ImportReceipt }> {
  const form = new FormData()
  form.append('file', file)
  form.append('format', format)
  form.append('mapping', JSON.stringify(mapping))
  const res = await fetch('/modeling/models/' + modelId + '/imports/', {
    method: 'POST',
    credentials: 'include',
    headers: { 'X-CSRFToken': getCsrf(), Accept: 'application/json' },
    body: form,
  })
  return handle(res)
}

export interface ImportPreview {
  preview: Record<string, unknown>[]
  rows_total: number
  error_rows: { row: number; error: string }[]
  mapping: Record<string, string>
  provenance: { kind: string; source_name: string; format: string }
}

export async function previewModelFile(
  modelId: string,
  file: File,
  format: 'json' | 'csv' | 'xlsx',
  mapping: Record<string, string> = {},
): Promise<ImportPreview> {
  const form = new FormData()
  form.append('file', file)
  form.append('format', format)
  form.append('mapping', JSON.stringify(mapping))
  form.append('preview', 'true')
  const res = await fetch('/modeling/models/' + modelId + '/imports/', {
    method: 'POST',
    credentials: 'include',
    headers: { 'X-CSRFToken': getCsrf(), Accept: 'application/json' },
    body: form,
  })
  return handle(res)
}

export interface ModelRunHistory {
  id: string
  status: string
  engine: string
  seed: number | null
  scenario: string
  model: string
  business: string
  version: number
  content_hash: string
  created_at: string
  traceability?: { model_version_id?: string; model_version?: number; schema_version?: string; content_hash?: string; engine?: string; seed?: number | null; iterations?: number; scenario_id?: string | null; scenario?: string }
  summary: { mean?: number; median?: number; std?: number; p5?: number; p95?: number; probability_loss?: number; mean_unmet_demand?: number; p95_unmet_demand?: number; mean_stock_service_level?: number; financial?: { status: string; revenue?: string; total_cost?: string; variable_cost?: string; cogs?: string; fixed_cost?: string; gross_profit?: string; contribution_margin?: string; operating_result?: string; cash_flow?: string; ending_cash?: string; working_capital?: string; break_even_units?: string; break_even_revenue?: string; roi?: string; mean_revenue?: string; mean_total_cost?: string; mean_cogs?: string; mean_contribution_margin?: string; mean_operating_result?: string; mean_roi?: string; mean_cash_flow?: string; mean_ending_cash?: string; mean_working_capital?: string } }
  error?: { code: string; where: string; message: string; how_to_fix: string; details?: { errors?: { path: string; code: string; message: string }[] } } | null
}

export async function getModelRuns(): Promise<{ runs: ModelRunHistory[] }> {
  const res = await fetch('/modeling/runs/', { credentials: 'include', headers: headers() })
  return handle(res)
}

export async function cancelModelRun(id: string): Promise<{ run_id: string; status: 'cancelled' }> {
  const res = await fetch(`/modeling/runs/${id}/cancel/`, { method: 'POST', credentials: 'include', headers: headers() })
  return handle(res)
}

export interface ModelRunComparison {
  run_id: string
  scenario: string
  seed: number | null
  summary: ModelRunHistory['summary']
  delta: Record<string, number>
}

export async function compareModelRuns(ids: string[]): Promise<{ model_version: number; content_hash: string; baseline_run_id: string; comparisons: ModelRunComparison[] }> {
  const res = await fetch(`/modeling/runs/compare/?ids=${encodeURIComponent(ids.join(','))}`, { credentials: 'include', headers: headers() })
  return handle(res)
}
