import { useState } from 'react'
import { OnboardingGuiado } from '@/components/OnboardingGuiado'
import { ResultadoSimulacion } from '@/components/ResultadoSimulacion'

interface Escenarios {
  p5: number
  p50: number
  p95: number
}

interface EstadoOnboarding {
  fase: 'formulario' | 'calculando' | 'resultado'
  escenarios: Escenarios | null
  tipoNegocio: string
  horizonte: number
  nombreNegocio: string
  error: string | null
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
          p5: data.p5 ?? data.percentil_5 ?? 0,
          p50: data.p50 ?? data.percentil_50 ?? 0,
          p95: data.p95 ?? data.percentil_95 ?? 0,
        },
        tipoNegocio: String(respuestas.tipo_negocio || 'comercio'),
        horizonte: Number(respuestas.horizonte) || 12,
        nombreNegocio: String(respuestas.nombre_negocio || 'Mi negocio'),
        error: null,
      })
    } catch (err) {
      setEstado(prev => ({
        ...prev,
        fase: 'resultado',
        // Fallback demo si la API falla — muestra igual el resultado
        escenarios: { p5: -2500, p50: 8500, p95: 22000 },
        error: 'Usamos datos de ejemplo — conectá tu API para resultados reales.',
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
