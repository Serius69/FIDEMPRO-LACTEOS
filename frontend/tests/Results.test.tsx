import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import Results from '@/pages/Results'
import { getModelRuns } from '@/lib/api'
import type { ModelRunHistory } from '@/lib/api'

// Resultados y riesgo es donde se lee la salida estadística persistida
// (media, P5, P95, probabilidad de pérdida) de cada corrida de modelo. El
// helper local `number()` (Results.tsx:7) ya maneja bien los valores
// ausentes (retorna "—" en vez de "0.00"); estos tests fijan ese
// comportamiento correcto como regresión, y verifican los otros estados
// (carga / vacío / error) con comportamiento real, no implementación.

vi.mock('@/lib/api', () => ({
  getModelRuns: vi.fn(),
  compareModelRuns: vi.fn(),
  cancelModelRun: vi.fn(),
}))

const mockedGetModelRuns = vi.mocked(getModelRuns)

function buildRun(overrides: Partial<ModelRunHistory> = {}): ModelRunHistory {
  return {
    id: 'run-1',
    status: 'completed',
    engine: 'monte_carlo',
    seed: 42,
    scenario: 'base',
    model: 'Modelo Panadería',
    business: 'Panadería Doña Carmen',
    version: 3,
    content_hash: 'abcdef1234567890',
    created_at: '2026-08-01T10:00:00Z',
    summary: { mean: 8500, p5: 4000, p95: 22000 },
    ...overrides,
  }
}

beforeEach(() => {
  mockedGetModelRuns.mockReset()
})

describe('Results — estados de carga', () => {
  it('shows a loading indicator distinct from the "no results yet" empty state', async () => {
    let resolveFn: (v: { runs: ModelRunHistory[] }) => void = () => {}
    mockedGetModelRuns.mockReturnValue(new Promise((resolve) => { resolveFn = resolve }))

    render(<Results />)
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.queryByText('Aún no hay resultados persistidos.')).not.toBeInTheDocument()

    resolveFn({ runs: [] })
    await waitFor(() => expect(screen.queryByRole('status')).not.toBeInTheDocument())
    expect(screen.getByText('Aún no hay resultados persistidos.')).toBeInTheDocument()
  })

  it('shows the real error message on failure instead of a silent empty list', async () => {
    mockedGetModelRuns.mockRejectedValue(new Error('No se pudo autenticar con el backend.'))

    render(<Results />)

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('No se pudo autenticar con el backend.'))
    // El error se muestra explícitamente (no queda oculto detrás de un estado
    // "vacío" silencioso); no importa si el estado vacío también se muestra
    // debajo, porque efectivamente no hay corridas cargadas.
    expect(screen.queryByText('Modelo Panadería')).not.toBeInTheDocument()
  })
})

describe('Results — honestidad de valores faltantes (regresión)', () => {
  it('renders "—" (not "0.00") for a run whose statistical summary is genuinely empty', async () => {
    mockedGetModelRuns.mockResolvedValue({ runs: [buildRun({ id: 'run-empty', summary: {} })] })

    render(<Results />)

    await waitFor(() => expect(screen.getByText('Modelo Panadería')).toBeInTheDocument())
    const card = screen.getByText('Modelo Panadería').closest('[class*="rounded-xl"]') as HTMLElement
    // Media / P5 / P95 deben mostrarse como "—", nunca como "0.00" fabricado.
    expect(within(card).getAllByText('—').length).toBeGreaterThanOrEqual(3)
    expect(within(card).queryByText('0.00')).not.toBeInTheDocument()
  })

  it('renders the REAL statistical values (mean/p5/p95) when present, formatted to 2 decimals', async () => {
    mockedGetModelRuns.mockResolvedValue({ runs: [buildRun({ summary: { mean: 8500, p5: 4000.5, p95: 22000 } })] })

    render(<Results />)

    await waitFor(() => expect(screen.getByText('Modelo Panadería')).toBeInTheDocument())
    expect(screen.getByText('8500.00')).toBeInTheDocument()
    expect(screen.getByText('4000.50')).toBeInTheDocument()
    expect(screen.getByText('22000.00')).toBeInTheDocument()
  })

  it('shows a run error inline (message, where, how_to_fix) instead of hiding a failed run as if it succeeded', async () => {
    mockedGetModelRuns.mockResolvedValue({
      runs: [buildRun({
        id: 'run-failed',
        status: 'failed',
        summary: {},
        error: { code: 'E_SPEC', where: 'validation', message: 'La demanda no puede ser negativa.', how_to_fix: 'Corrige el rango de demanda en el modelo.' },
      })],
    })

    render(<Results />)

    await waitFor(() => expect(screen.getByText('La demanda no puede ser negativa.')).toBeInTheDocument())
    expect(screen.getByText(/Corrige el rango de demanda en el modelo\./)).toBeInTheDocument()
  })
})
