import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

/**
 * El fallo de la API NO puede terminar en la vista de resultado.
 *
 * El `catch` inventaba una proyección de ejemplo (p5 -2500 / p50 8500 /
 * p95 22000) y la pintaba en la MISMA pantalla de resultado que los datos
 * reales, con un banner amarillo pequeño. El usuario leía "Bs. 8.500" como la
 * proyección de SU negocio cuando nadie la calculó.
 *
 *   SINTÉTICO != OBSERVADO · AUSENTE != 0
 *
 * El wizard se sustituye por un doble: acá se prueba la página (parseo de la
 * respuesta y manejo del fallo), no la UI del formulario, que tiene sus
 * propios tests en OnboardingGuiado.test.tsx.
 */
vi.mock('@/components/OnboardingGuiado', () => ({
  OnboardingGuiado: ({ onCompletado }: { onCompletado: (r: Record<string, string | number>) => void }) => (
    <button
      type="button"
      onClick={() => onCompletado({
        ventas_mes: 10000, gastos_fijos: 5000, tiempo_operando: 12,
        tipo_negocio: 'comercio', horizonte: 12, nombre_negocio: 'Panadería',
      })}
    >
      enviar-formulario
    </button>
  ),
}))

const { default: OnboardingPage } = await import('@/pages/OnboardingPage')

async function enviar() {
  const user = userEvent.setup()
  render(<OnboardingPage />)
  await user.click(screen.getByRole('button', { name: 'enviar-formulario' }))
}

describe('OnboardingPage — un fallo se muestra como fallo', () => {
  beforeEach(() => vi.spyOn(console, 'error').mockImplementation(() => {}))
  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('no inventa cifras de ejemplo cuando la API falla', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500 }))

    await enviar()

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())

    // Las cifras del viejo fallback demo no pueden aparecer nunca.
    for (const inventada of [/8\.500/, /22\.000/, /2\.500/]) {
      expect(screen.queryByText(inventada)).toBeNull()
    }
    // Ni el veredicto de viabilidad, que se construía sobre esas cifras.
    expect(screen.queryByText(/ES VIABLE/i)).toBeNull()
    expect(screen.getByText(/No se pudo calcular la proyección/i)).toBeInTheDocument()
  })

  it('tampoco inventa cifras cuando la red se cae', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network down')))

    await enviar()

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
    expect(screen.queryByText(/8\.500/)).toBeNull()
    expect(screen.getByText(/network down/i)).toBeInTheDocument()
  })

  it('un percentil ausente en una respuesta 200 no se convierte en Bs. 0', async () => {
    // La API responde OK pero sin p5/p95: no son ceros, no se calcularon.
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true, status: 200, json: async () => ({ p50: 8500 }),
    }))

    await enviar()

    await waitFor(() =>
      expect(screen.getAllByText(/No disponible/i).length).toBeGreaterThan(0))
    expect(screen.getByText('Bs. 8.500')).toBeInTheDocument()
    expect(screen.queryByText('Bs. 0')).toBeNull()
  })

  it('una respuesta completa sí muestra la proyección', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true, status: 200, json: async () => ({ p5: -2000, p50: 9000, p95: 21000 }),
    }))

    await enviar()

    await waitFor(() => expect(screen.getByText('Bs. 9.000')).toBeInTheDocument())
    expect(screen.queryByRole('alert')).toBeNull()
  })
})
