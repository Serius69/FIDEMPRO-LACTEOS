import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react'
import Simulate from '@/pages/Simulate'
import { runSimulation } from '@/lib/api'
import type { SimulationResult } from '@/types'

// Simulate.tsx corre y muestra el resultado del motor Monte Carlo: VaR,
// CVaR, beneficio esperado, escenarios. Es la salida financiera más sensible
// del producto. Verificamos: estado vacío inicial vs. cargando vs. resultado
// vs. error (cuatro estados distinguibles), y que los montos mostrados sean
// los reales que vinieron del backend (no ceros de relleno).

vi.mock('@/lib/api', () => ({
  runSimulation: vi.fn(),
}))

const mockedRunSimulation = vi.mocked(runSimulation)

function buildResult(overrides: Partial<SimulationResult> = {}): SimulationResult {
  return {
    demand: { mean: 1000, std: 150, var_95: -200, cvar_95: -260, distribution: [] },
    revenue: { mean: 25000, std: 3200, percentile_5: 19000, percentile_95: 31000 },
    profit: { mean: 13000, std: 2100, var_95: -1800, cvar_95: -2600, sharpe_ratio: 1.42, ratio_basis: 'periodized_returns' },
    risk: { var_level: 0.95, cvar_level: 0.95, probability_of_loss: 0.08, risk_category: 'bajo' },
    scenarios: {
      pessimist: { demand: 700, revenue: 17500, profit: 4000, probability: 0.05 },
      base: { demand: 1000, revenue: 25000, profit: 13000, probability: 0.9 },
      optimist: { demand: 1300, revenue: 32500, profit: 20000, probability: 0.05 },
    },
    time_series: { demand: [1000, 1010], revenue: [25000, 25200], profit: [13000, 13100], periods: ['1', '2'] },
    metadata: { n_iterations: 10000, confidence_level: 0.95, distribution_type: 'normal', execution_time: 1.234 },
    ...overrides,
  }
}

beforeEach(() => {
  mockedRunSimulation.mockReset()
})

describe('Simulate — estados', () => {
  it('shows the empty configure-and-run prompt before any simulation has been run', () => {
    render(<Simulate />)
    expect(screen.getByText('Configura y ejecuta una simulación')).toBeInTheDocument()
    expect(screen.queryByText('Demanda media')).not.toBeInTheDocument()
  })

  it('shows a distinct loading state (button text + spinner) while the simulation runs, separate from the empty and result states', async () => {
    let resolveFn: (v: SimulationResult) => void = () => {}
    mockedRunSimulation.mockReturnValue(new Promise((resolve) => { resolveFn = resolve }))

    render(<Simulate />)
    fireEvent.click(screen.getByRole('button', { name: /Ejecutar Simulación/ }))

    expect(await screen.findByRole('button', { name: /Simulando/ })).toBeInTheDocument()
    expect(screen.queryByText('Configura y ejecuta una simulación')).not.toBeInTheDocument()
    expect(screen.queryByText('Demanda media')).not.toBeInTheDocument()

    resolveFn(buildResult())
    await waitFor(() => expect(screen.getByText('Demanda media')).toBeInTheDocument())
  })

  it('shows the real error message on failure and does not render a stale/fake result panel', async () => {
    mockedRunSimulation.mockRejectedValue(new Error('El motor de simulación no respondió a tiempo.'))

    render(<Simulate />)
    fireEvent.click(screen.getByRole('button', { name: /Ejecutar Simulación/ }))

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('El motor de simulación no respondió a tiempo.'))
    expect(screen.queryByText('Demanda media')).not.toBeInTheDocument()
  })
})

describe('Simulate — resultado numérico real', () => {
  it('renders the actual VaR/CVaR/profit/demand figures returned by the backend, formatted in BOB, not placeholder zeros', async () => {
    mockedRunSimulation.mockResolvedValue(buildResult())

    render(<Simulate />)
    fireEvent.click(screen.getByRole('button', { name: /Ejecutar Simulación/ }))

    await waitFor(() => expect(screen.getByText('Demanda media')).toBeInTheDocument())

    const demandCard = screen.getByText('Demanda media').closest('div')?.parentElement as HTMLElement
    expect(within(demandCard).getByText('1.000')).toBeInTheDocument() // demand.mean, no cero de relleno

    expect(screen.getByText('Bs. 13.000')).toBeInTheDocument() // profit.mean
    expect(screen.getByText('Bs. 1.800')).toBeInTheDocument() // |profit.var_95|
    expect(screen.getByText('bajo')).toBeInTheDocument() // risk_category real (no "—", no invented category)
    expect(screen.getByText(/Prob\. pérdida: 8\.0%/)).toBeInTheDocument()
  })

  it('shows "—" for the risk category when the backend omits it — never a default/invented category like "bajo"', async () => {
    mockedRunSimulation.mockResolvedValue(buildResult({
      risk: { var_level: 0.95, cvar_level: 0.95, probability_of_loss: 0.08, risk_category: undefined as unknown as string },
    }))

    render(<Simulate />)
    fireEvent.click(screen.getByRole('button', { name: /Ejecutar Simulación/ }))

    await waitFor(() => expect(screen.getByText('Demanda media')).toBeInTheDocument())
    expect(screen.getByText('Categoría de riesgo').closest('div')?.parentElement).toHaveTextContent('—')
  })
})
