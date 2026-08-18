import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ResultadoSimulacion } from '@/components/ResultadoSimulacion'

// Esta es la pantalla de resultado financiero que ve el dueño de una PYME al
// final del onboarding: decide si "su negocio es viable" en base a estos
// números. Los tests verifican comportamiento real, no snapshots: los montos
// mostrados, la clasificación viable/no-viable, y que compartir por
// WhatsApp/copiar produzca el texto real (no una plantilla vacía).

const escenariosSanos = { p5: 4000, p50: 8500, p95: 22000 }

describe('ResultadoSimulacion — negocio viable', () => {
  it('shows the three real percentile amounts and marks the business as viable when p50 > 0', () => {
    render(<ResultadoSimulacion escenarios={escenariosSanos} tipoNegocio="comercio" horizonte={12} nombreNegocio="Panadería Doña Carmen" />)

    expect(screen.getByText('Proyección para Panadería Doña Carmen')).toBeInTheDocument()
    expect(screen.getByText('Bs. 22.000')).toBeInTheDocument() // p95
    expect(screen.getByText('Bs. 8.500')).toBeInTheDocument()  // p50
    expect(screen.getByText('Bs. 4.000')).toBeInTheDocument()  // p5

    expect(screen.getByText('Tu negocio ES VIABLE según estos datos.')).toBeInTheDocument()
    expect(screen.queryByText('El negocio necesita ajustes antes de ser viable.')).not.toBeInTheDocument()
  })

  it('recommends a reserve based on the worst case (p5), not on the optimistic or probable scenario', () => {
    render(<ResultadoSimulacion escenarios={escenariosSanos} tipoNegocio="comercio" horizonte={12} />)
    // reservaRecomendada = round(p5 * 0.15 / 1000) * 1000 = round(4000*0.15/1000)*1000 = 1000
    expect(screen.getByText(/al menos Bs\. 1\.000 de reserva/i)).toBeInTheDocument()
  })
})

describe('ResultadoSimulacion — negocio no viable', () => {
  it('marks the business as needing adjustments when the probable scenario (p50) is not positive, and does not show a fake reserve recommendation', () => {
    render(<ResultadoSimulacion escenarios={{ p5: -3000, p50: 0, p95: 5000 }} tipoNegocio="servicios" horizonte={6} />)

    expect(screen.getByText('El negocio necesita ajustes antes de ser viable.')).toBeInTheDocument()
    expect(screen.queryByText('Tu negocio ES VIABLE según estos datos.')).not.toBeInTheDocument()
    expect(screen.getByText('Revisa tus gastos fijos y el precio de venta antes de continuar.')).toBeInTheDocument()
    // No debe sugerir una reserva "recomendada" para un negocio que ya se marcó como no viable.
    expect(screen.queryByText(/reserva mínima recomendada/i)).not.toBeInTheDocument()
  })
})

describe('ResultadoSimulacion — compartir resultados', () => {
  const originalClipboard = navigator.clipboard
  const originalShare = (navigator as unknown as { share?: unknown }).share

  afterEach(() => {
    Object.defineProperty(navigator, 'clipboard', { value: originalClipboard, configurable: true })
    Object.defineProperty(navigator, 'share', { value: originalShare, configurable: true })
    vi.restoreAllMocks()
  })

  it('copies the REAL scenario amounts to the clipboard, not placeholder text', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true })

    render(<ResultadoSimulacion escenarios={escenariosSanos} tipoNegocio="comercio" horizonte={12} nombreNegocio="Tienda Central" />)
    fireEvent.click(screen.getByRole('button', { name: 'Copiar resultados al portapapeles' }))

    await waitFor(() => expect(writeText).toHaveBeenCalledTimes(1))
    const copiedText = writeText.mock.calls[0][0] as string
    expect(copiedText).toContain('Tienda Central')
    expect(copiedText).toContain('Bs. 22.000') // optimista real
    expect(copiedText).toContain('Bs. 8.500')  // probable real
    expect(copiedText).toContain('Bs. 4.000')  // difícil real

    await waitFor(() => expect(screen.getByRole('button', { name: 'Resultados copiados' })).toBeInTheDocument())
  })

  it('uses window.open with a wa.me link (not navigator.share) when the Web Share API is unavailable', async () => {
    Object.defineProperty(navigator, 'share', { value: undefined, configurable: true })
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null)

    render(<ResultadoSimulacion escenarios={escenariosSanos} tipoNegocio="comercio" horizonte={12} nombreNegocio="Tienda Central" />)
    fireEvent.click(screen.getByRole('button', { name: 'Compartir resultados por WhatsApp' }))

    await waitFor(() => expect(openSpy).toHaveBeenCalledTimes(1))
    const [url] = openSpy.mock.calls[0]
    expect(String(url)).toMatch(/^https:\/\/wa\.me\/\?text=/)
    const decoded = decodeURIComponent(String(url).replace('https://wa.me/?text=', ''))
    expect(decoded).toContain('Tienda Central')
    expect(decoded).toContain('Bs. 8.500')
  })
})

describe('ResultadoSimulacion — un percentil ausente se muestra, no se inventa ni revienta', () => {
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  // `formatBOB` llamaba `n.toLocaleString(...)` sin guarda: un percentil
  // ausente (payload parcial o legacy) reventaba el render entero con
  // TypeError. Ahora se muestra "No disponible".
  it('muestra "No disponible" en vez de reventar cuando falta p95', () => {
    const escenariosIncompletos = { p5: 100, p50: 200, p95: undefined } as unknown as {
      p5: number | null; p50: number | null; p95: number | null
    }

    expect(() =>
      render(<ResultadoSimulacion escenarios={escenariosIncompletos} tipoNegocio="comercio" horizonte={12} />),
    ).not.toThrow()

    expect(screen.getAllByText(/No disponible/i).length).toBeGreaterThan(0)
  })

  it('no muestra "Bs. 0" por un percentil ausente', () => {
    const escenariosIncompletos = { p5: null, p50: 200, p95: null }

    render(<ResultadoSimulacion escenarios={escenariosIncompletos} tipoNegocio="comercio" horizonte={12} />)

    expect(screen.queryByText(/Bs\. 0\b/)).toBeNull()
  })

  it('sin escenario probable no afirma ni niega la viabilidad', () => {
    const sinProbable = { p5: -100, p50: null, p95: 500 }

    render(<ResultadoSimulacion escenarios={sinProbable} tipoNegocio="comercio" horizonte={12} />)

    expect(screen.getByText(/No se puede determinar la viabilidad/i)).toBeInTheDocument()
    expect(screen.queryByText(/ES VIABLE/i)).toBeNull()
    expect(screen.queryByText(/necesita ajustes antes de ser viable/i)).toBeNull()
  })
})
