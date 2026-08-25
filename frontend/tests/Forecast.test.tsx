import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import ForecastPage from '@/pages/Forecast'
import { runForecast } from '@/lib/api'
import type { ForecastResult } from '@/types'
import respuestaReal from './fixtures/api-v1-forecast.json'

// La página de pronóstico no tenía ningún test, y estaba rota en producción:
// leía `result.forecast.map(...)` sobre un `forecast` que el servidor manda
// como OBJETO con series paralelas, así que reventaba con
// «forecast.map is not a function» en cuanto llegaba una respuesta 200.
//
// El fixture es una respuesta CAPTURADA de `POST /simulate/api/v1/forecast/`.
// El lado servidor del contrato está fijado en
// `findempro/simulate/tests/test_api_v1_wire_contract.py`.

vi.mock('@/lib/api', () => ({
  runForecast: vi.fn(),
}))

const mockedRunForecast = vi.mocked(runForecast)
const RESPUESTA = respuestaReal as ForecastResult

function conForecast(overrides: Partial<ForecastResult['forecast']> = {}): ForecastResult {
  return { ...RESPUESTA, forecast: { ...RESPUESTA.forecast, ...overrides } }
}

beforeEach(() => {
  mockedRunForecast.mockReset()
})

async function generar() {
  render(<ForecastPage />)
  fireEvent.click(screen.getByRole('button', { name: /Generar Pronóstico/ }))
  await waitFor(() => expect(screen.getByText('Valores pronosticados')).toBeInTheDocument())
}

describe('Forecast', () => {
  it('shows the empty prompt before any forecast has been requested', () => {
    render(<ForecastPage />)
    expect(screen.getByText('Pronóstico de series de tiempo')).toBeInTheDocument()
    expect(screen.queryByText('Valores pronosticados')).not.toBeInTheDocument()
  })

  it('renders the payload the server actually sends without crashing the result panel', async () => {
    mockedRunForecast.mockResolvedValue(RESPUESTA)
    await generar()

    // Un renglón por período proyectado, con su intervalo.
    expect(screen.getByText('1.299')).toBeInTheDocument()   // values[0]
    expect(screen.getByText('1.166')).toBeInTheDocument()   // ci_lower[0]
    expect(screen.getByText('1.432')).toBeInTheDocument()   // ci_upper[0]
    expect(screen.getByText('linear')).toBeInTheDocument()  // method_used
  })

  it('shows both error metrics the server computes, MAPE and RMSE', async () => {
    mockedRunForecast.mockResolvedValue(RESPUESTA)
    await generar()

    expect(screen.getByText('6,61%')).toBeInTheDocument()   // mape
    expect(screen.getByText('95,38')).toBeInTheDocument()   // rmse
  })

  it('shows "—" for MAPE when the server reports it as undefined, and still shows RMSE', async () => {
    // MAPE es un error relativo: contra observaciones en cero no está definido
    // y el servidor manda `null` antes que inventarlo. RMSE sigue siendo el
    // indicador de error disponible, y por eso la API ahora lo expone.
    mockedRunForecast.mockResolvedValue(conForecast({ mape: null }))
    await generar()

    const mapeCard = screen.getByText('MAPE').closest('div') as HTMLElement
    expect(mapeCard).toHaveTextContent('—')
    expect(screen.getByText('95,38')).toBeInTheDocument()
  })

  it('shows the real error message on failure and no result panel', async () => {
    mockedRunForecast.mockRejectedValue(new Error('El servicio de pronóstico no respondió.'))

    render(<ForecastPage />)
    fireEvent.click(screen.getByRole('button', { name: /Generar Pronóstico/ }))

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('El servicio de pronóstico no respondió.'))
    expect(screen.queryByText('Valores pronosticados')).not.toBeInTheDocument()
  })
})
