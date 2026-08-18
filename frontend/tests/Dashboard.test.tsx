import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import Dashboard from '@/pages/Dashboard'
import { getDashboardData, getDashboardSummary } from '@/lib/api'

// El Dashboard es la primera pantalla que ve el usuario. Los KPIs mezclan dos
// fuentes (data + summary) con Promise.allSettled — el comportamiento
// correcto es: valores reales cuando existen, "—" cuando no (nunca 0 u otro
// valor inventado), y un error explícito solo cuando AMBAS fuentes fallan
// (no cuando hay degradación parcial con datos reales disponibles).

vi.mock('@/lib/api', () => ({
  getDashboardData: vi.fn(),
  getDashboardSummary: vi.fn(),
}))

const mockedData = vi.mocked(getDashboardData)
const mockedSummary = vi.mocked(getDashboardSummary)

beforeEach(() => {
  mockedData.mockReset()
  mockedSummary.mockReset()
})

describe('Dashboard — carga exitosa', () => {
  it('shows a loading spinner before data arrives, then the real KPI numbers from the API', async () => {
    let resolveData: (v: unknown) => void = () => {}
    mockedData.mockReturnValue(new Promise((resolve) => { resolveData = resolve }))
    mockedSummary.mockResolvedValue({ total_businesses: 3, active_simulations: 1, pending_alerts: 0 })

    render(<Dashboard />)
    expect(screen.getByLabelText('Cargando datos...')).toBeInTheDocument()

    resolveData({
      businesses_count: 5,
      simulations_count: 12,
      products_count: 4,
      recent_simulations: [],
      risk_alerts: [],
    })

    await waitFor(() => expect(screen.queryByLabelText('Cargando datos...')).not.toBeInTheDocument())
    expect(screen.getByText('5')).toBeInTheDocument() // businesses_count real, no fabricado
    expect(screen.getByText('12')).toBeInTheDocument() // simulations_count real
  })
})

describe('Dashboard — falla total de backend', () => {
  it('shows an explicit "backend not reachable" error (with a login link) when BOTH endpoints fail, and does not show fabricated KPI numbers', async () => {
    mockedData.mockRejectedValue(new Error('network error'))
    mockedSummary.mockRejectedValue(new Error('network error'))

    render(<Dashboard />)

    await waitFor(() => expect(screen.getByText(/Backend Django no alcanzable/)).toBeInTheDocument())
    expect(screen.getByRole('link', { name: /Iniciar sesión/ })).toBeInTheDocument()

    // Ningún KPI debe mostrar un número inventado (0, etc.) — deben quedar
    // en el placeholder honesto "—" porque no hay dato real disponible.
    const kpiValues = screen.getAllByText('—')
    expect(kpiValues.length).toBe(4)
  })
})

describe('Dashboard — degradación parcial (una fuente falla, la otra no)', () => {
  it('falls back to the summary endpoint numbers (real data) without showing the "backend unreachable" error banner', async () => {
    mockedData.mockRejectedValue(new Error('dashboard-data down'))
    mockedSummary.mockResolvedValue({ total_businesses: 7, active_simulations: 2, pending_alerts: 4 })

    render(<Dashboard />)

    await waitFor(() => expect(screen.queryByLabelText('Cargando datos...')).not.toBeInTheDocument())
    expect(screen.queryByText(/Backend Django no alcanzable/)).not.toBeInTheDocument()

    // KPIs derivados de `summary` (que sí respondió) muestran su número real.
    expect(screen.getByText('7')).toBeInTheDocument()  // Negocios (total_businesses)
    expect(screen.getByText('2')).toBeInTheDocument()  // Simulaciones (active_simulations)

    // El KPI que depende exclusivamente de `data` (que falló) debe quedar
    // como "—", nunca como 0 disfrazado de "sin análisis recientes".
    const ultimoAnalisisCard = screen.getByText('Último análisis').closest('div')?.parentElement
    expect(ultimoAnalisisCard).toBeTruthy()
    expect(within(ultimoAnalisisCard as HTMLElement).getByText('—')).toBeInTheDocument()
  })
})
