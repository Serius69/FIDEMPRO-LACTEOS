import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react'
import Simulate from '@/pages/Simulate'
import { runSimulation } from '@/lib/api'
import type { SimulationResult } from '@/types'
import respuestaReal from './fixtures/api-v1-simulate.json'

// Simulate.tsx corre y muestra el resultado del motor Monte Carlo: VaR,
// CVaR, beneficio, escenarios. Es la salida financiera más sensible del
// producto. Verificamos: estado vacío inicial vs. cargando vs. resultado vs.
// error (cuatro estados distinguibles), y que los montos mostrados sean los
// reales que vinieron del backend (no ceros de relleno).
//
// ── Sobre el fixture ────────────────────────────────────────────────────────
// `tests/fixtures/api-v1-simulate.json` es una respuesta CAPTURADA de
// `POST /simulate/api/v1/simulate/`, no un objeto escrito a mano. El fixture
// anterior sí lo era, y describía una forma que el servidor nunca emitió
// (`scenarios` como objeto con claves `pessimist`/`base`/`optimist`,
// `time_series` como columnas paralelas, `revenue.percentile_5`,
// `metadata.execution_time`, `risk.risk_category`). Con él este archivo pasaba
// en verde mientras la página se caía en producción con `undefined.map` en
// cuanto una simulación terminaba bien.
//
// El lado servidor del mismo contrato está fijado en
// `findempro/simulate/tests/test_api_v1_wire_contract.py`.

vi.mock('@/lib/api', () => ({
  runSimulation: vi.fn(),
}))

const mockedRunSimulation = vi.mocked(runSimulation)

function buildResult(overrides: Partial<SimulationResult> = {}): SimulationResult {
  return { ...(respuestaReal as SimulationResult), ...overrides }
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
  async function renderConResultado(overrides: Partial<SimulationResult> = {}) {
    mockedRunSimulation.mockResolvedValue(buildResult(overrides))
    render(<Simulate />)
    fireEvent.click(screen.getByRole('button', { name: /Ejecutar Simulación/ }))
    await waitFor(() => expect(screen.getByText('Demanda media')).toBeInTheDocument())
  }

  it('renders the payload the server actually sends without crashing the result panel', async () => {
    // La regresión concreta: `time_series.periods.map(...)` y
    // `scenarios.pessimist.demand` sobre la respuesta real lanzaban TypeError
    // durante el render, y la página entera desaparecía.
    await renderConResultado()

    expect(screen.getByText('Series de tiempo — Demanda, Ingresos y Beneficio')).toBeInTheDocument()
    expect(screen.getByText('Análisis de escenarios (por percentil de demanda)')).toBeInTheDocument()
  })

  it('renders the actual demand/profit/VaR figures returned by the backend, formatted in BOB, not placeholder zeros', async () => {
    await renderConResultado()

    const demandCard = screen.getByText('Demanda media').closest('div')?.parentElement as HTMLElement
    expect(within(demandCard).getByText('996')).toBeInTheDocument() // demand.mean real

    // Mediana de utilidad — el escenario típico, que la API no exponía.
    expect(screen.getByText('Bs. 8.012')).toBeInTheDocument()
    // VaR: cuantil inferior del beneficio, tal cual (no un valor absoluto
    // repintado como «pérdida máxima», que es lo que se mostraba antes).
    expect(screen.getByText('Bs. 4.713')).toBeInTheDocument()
    expect(screen.getByText(/Probabilidad de pérdida/)).toBeInTheDocument()
  })

  it('lists the five named scenarios the engine returns, by demand percentile', async () => {
    await renderConResultado()

    // Los cinco percentiles del motor, cada uno una vez. Antes la página sólo
    // podía pintar tres claves fijas (pessimist/base/optimist) que además no
    // existían en la respuesta.
    for (const percentil of [5, 25, 50, 75, 95]) {
      expect(screen.getByText(new RegExp(`percentil ${percentil} de demanda`))).toBeInTheDocument()
    }
    expect(screen.getAllByText(/Muy Optimista/).length).toBeGreaterThan(0)
  })

  it('reports the Sharpe ratio as unavailable with the server-stated reason, never as a number', async () => {
    // El servidor manda `sharpe_ratio: null` y explica por qué en
    // `ratio_basis`; presentar un número aquí sería fabricarlo.
    await renderConResultado()

    const sharpeCard = screen.getByText('Sharpe Ratio').closest('div') as HTMLElement
    expect(within(sharpeCard).getByText('—')).toBeInTheDocument()
    expect(screen.getByText(/no es una serie de retornos periodizados/)).toBeInTheDocument()
  })

  it('labels VaR/CVaR with the confidence level the server actually used, not a hardcoded 95%', async () => {
    await renderConResultado({
      risk: { ...(respuestaReal as SimulationResult).risk,
              confidence_level: 0.9, var_confidence_level: 0.9, cvar_confidence_level: 0.9 },
    })

    expect(screen.getByText('VaR 90.0%')).toBeInTheDocument()
    expect(screen.getByText('CVaR 90.0%')).toBeInTheDocument()
  })
})
