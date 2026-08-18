import { useState } from 'react'
import { OnboardingGuiado } from '@/components/OnboardingGuiado'
import { ResultadoSimulacion } from '@/components/ResultadoSimulacion'

// Un percentil ausente vale null, no 0: "no lo calculamos" no es "da cero".
interface Escenarios {
  p5: number | null
  p50: number | null
  p95: number | null
}

interface EstadoOnboarding {
  fase: 'formulario' | 'calculando' | 'resultado' | 'error'
  escenarios: Escenarios | null
  tipoNegocio: string
  horizonte: number
  nombreNegocio: string
  error: string | null
}

function numeroObservado(valor: unknown): number | null {
  if (valor == null) return null
  const n = Number(valor)
  return Number.isFinite(n) ? n : null
}

export default function OnboardingPage() {
  const [estado, setEstado] = useState<EstadoOnboarding>({
    fase: 'formulario',
    escenarios: null,
    tipoNegocio: 'comercio',
    horizonte: 12,
    nombreNegocio: 'Mi negocio',
    error: null,
  })

  async function handleRespuestas(respuestas: Record<string, string | number>) {
    setEstado(prev => ({ ...prev, fase: 'calculando', error: null }))

    try {
      const res = await fetch('/api/simulate/montecarlo/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ventas_mes: Number(respuestas.ventas_mes) || 10000,
          gastos_fijos: Number(respuestas.gastos_fijos) || 5000,
          tiempo_operando: Number(respuestas.tiempo_operando) || 12,
          tipo_negocio: respuestas.tipo_negocio || 'comercio',
          horizonte: Number(respuestas.horizonte) || 12,
          simulaciones: 5000,
        }),
      })

      if (!res.ok) throw new Error(`Error ${res.status}`)
      const data = await res.json()

      setEstado({
        fase: 'resultado',
        escenarios: {
          p5: numeroObservado(data.p5 ?? data.percentil_5),
          p50: numeroObservado(data.p50 ?? data.percentil_50),
          p95: numeroObservado(data.p95 ?? data.percentil_95),
        },
        tipoNegocio: String(respuestas.tipo_negocio || 'comercio'),
        horizonte: Number(respuestas.horizonte) || 12,
        nombreNegocio: String(respuestas.nombre_negocio || 'Mi negocio'),
        error: null,
      })
    } catch (err) {
      // Antes esto inventaba una proyección de ejemplo (-2500 / 8500 / 22000) y
      // la mostraba en la MISMA vista de resultado: el usuario leía cifras que
      // nadie calculó como si fueran las de su negocio. Un fallo se muestra
      // como un fallo.
      setEstado(prev => ({
        ...prev,
        fase: 'error',
        escenarios: null,
        error: err instanceof Error
          ? `No pudimos calcular tu proyección: ${err.message}`
          : 'No pudimos calcular tu proyección.',
      }))
    }
  }

  function reiniciar() {
    setEstado({
      fase: 'formulario',
      escenarios: null,
      tipoNegocio: 'comercio',
      horizonte: 12,
      nombreNegocio: 'Mi negocio',
      error: null,
    })
  }

  if (estado.fase === 'formulario') {
    return (
      <div className="flex-1 overflow-auto bg-background">
        <OnboardingGuiado onCompletado={handleRespuestas} />
      </div>
    )
  }

  if (estado.fase === 'calculando') {
    return (
      <div className="flex-1 flex items-center justify-center bg-background">
        <div role="status" aria-label="Corriendo 5.000 simulaciones Monte Carlo…" className="text-center space-y-4">
          <div className="relative mx-auto w-16 h-16" aria-hidden="true">
            <div className="absolute inset-0 rounded-full border-4 border-primary/20" />
            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-primary animate-spin" />
          </div>
          <p className="text-sm text-muted-foreground" aria-hidden="true">
            Corriendo 5.000 simulaciones Monte Carlo…
          </p>
          <p className="text-xs text-muted-foreground/60">
            Calculamos escenarios para tu negocio
          </p>
        </div>
      </div>
    )
  }

  if (estado.fase === 'error') {
    return (
      <div className="flex-1 overflow-auto bg-background">
        <div className="max-w-2xl mx-auto mt-8 px-4 space-y-4">
          <div
            role="alert"
            className="rounded-lg border border-red-500/30 bg-red-500/5 px-4 py-3 text-sm text-red-600 dark:text-red-400"
          >
            <p className="font-semibold">No se pudo calcular la proyección</p>
            <p className="mt-1">{estado.error}</p>
            <p className="mt-2 text-xs opacity-80">
              No mostramos cifras de ejemplo: serían inventadas y no dicen nada
              sobre tu negocio.
            </p>
          </div>
          <button
            type="button"
            onClick={reiniciar}
            className="rounded-lg border px-4 py-2 text-sm font-medium hover:bg-muted"
          >
            Volver a intentar
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-auto bg-background">
      {estado.error && (
        <div className="max-w-2xl mx-auto mt-4 px-4">
          <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/5 px-4 py-3 text-sm text-yellow-600 dark:text-yellow-400">
            {estado.error}
          </div>
        </div>
      )}
      {estado.escenarios && (
        <ResultadoSimulacion
          escenarios={estado.escenarios}
          tipoNegocio={estado.tipoNegocio}
          horizonte={estado.horizonte}
          nombreNegocio={estado.nombreNegocio}
          onNuevaSim={reiniciar}
        />
      )}
    </div>
  )
}
