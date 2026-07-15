import type { DashboardData, DashboardSummary, SimulationRequest, SimulationResult, ForecastRequest, ForecastResult, Report } from '@/types'

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
    try { msg = JSON.parse(text).detail ?? JSON.parse(text).error ?? msg } catch { /* raw */ }
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

export async function runFullPipeline(businessId: number) {
  const res = await fetch(`/simulate/api/v1/full-pipeline/${businessId}/`, {
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
