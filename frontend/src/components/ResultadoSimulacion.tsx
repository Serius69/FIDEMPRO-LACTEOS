import { useState, useCallback } from 'react'
import { TooltipSimple } from './TooltipSimple'

interface Escenarios {
  p5:  number   // peor caso
  p50: number   // probable
  p95: number   // optimista
}

interface ResultadoSimulacionProps {
  escenarios: Escenarios
  tipoNegocio: string      // 'comercio' | 'manufactura' | 'servicios' | 'agropecuario' | 'otro'
  horizonte:   number      // meses
  nombreNegocio?: string
  onDescargar?: () => void
  onNuevaSim?:  () => void
}

// Traduce un monto en bolivianos a un ejemplo concreto según tipo de negocio
function calcularEquivalente(monto: number, tipoNegocio: string): string {
  if (monto <= 0) return ''

  const ejemplos: Record<string, { unidad: string; precioPromedio: number }> = {
    comercio:     { unidad: 'artículos de Bs. 50',     precioPromedio: 50    },
    manufactura:  { unidad: 'unidades producidas de Bs. 80', precioPromedio: 80 },
    servicios:    { unidad: 'servicios de Bs. 200',    precioPromedio: 200   },
    agropecuario: { unidad: 'kg de producción de Bs. 25', precioPromedio: 25 },
    otro:         { unidad: 'ventas de Bs. 100',        precioPromedio: 100  },
  }

  const e = ejemplos[tipoNegocio] ?? ejemplos.otro
  const cantidad = Math.round(monto / e.precioPromedio)

  return `como vender ${cantidad.toLocaleString('es-BO')} ${e.unidad}`
}

function formatBOB(n: number): string {
  return `Bs. ${n.toLocaleString('es-BO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
}

function formatBOBMes(n: number): string {
  return `Bs. ${(n / 12).toLocaleString('es-BO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
}

export function ResultadoSimulacion({
  escenarios,
  tipoNegocio,
  horizonte,
  nombreNegocio,
  onDescargar,
  onNuevaSim,
}: ResultadoSimulacionProps) {
  const esViable = escenarios.p50 > 0
  const reservaRecomendada = Math.round(escenarios.p5 * 0.15 / 1000) * 1000
  const [copiado, setCopiado] = useState(false)

  const compartirWhatsApp = useCallback(async () => {
    const nombre = nombreNegocio ? `*${nombreNegocio}*` : 'mi negocio'
    const texto = [
      `📊 *Proyección financiera — ${nombre}*`,
      `Horizonte: ${horizonte} meses`,
      '',
      `✅ Optimista (95%): ${formatBOB(escenarios.p95)}`,
      `👍 Probable (50%): ${formatBOB(escenarios.p50)}`,
      `⚠️ Difícil (5%): ${formatBOB(escenarios.p5)}`,
      '',
      esViable
        ? `💡 Negocio *viable*. Reserva mínima recomendada: ${formatBOB(reservaRecomendada)}`
        : '⚠️ El negocio *necesita ajustes* antes de ser viable.',
      '',
      'Simulado con FindemproAI — findemproai.com',
    ].join('\n')

    if (navigator.share) {
      try {
        await navigator.share({ title: `Proyección — ${nombreNegocio ?? 'negocio'}`, text: texto })
      } catch { /* cancelado */ }
    } else {
      const waUrl = `https://wa.me/?text=${encodeURIComponent(texto)}`
      window.open(waUrl, '_blank', 'noopener,noreferrer')
    }
  }, [escenarios, horizonte, nombreNegocio, esViable, reservaRecomendada])

  const copiarResultados = useCallback(async () => {
    const texto = [
      `Proyección financiera — ${nombreNegocio ?? 'negocio'}`,
      `Horizonte: ${horizonte} meses`,
      `Optimista: ${formatBOB(escenarios.p95)}`,
      `Probable: ${formatBOB(escenarios.p50)}`,
      `Difícil: ${formatBOB(escenarios.p5)}`,
    ].join('\n')
    try {
      await navigator.clipboard.writeText(texto)
      setCopiado(true)
      setTimeout(() => setCopiado(false), 2000)
    } catch { /* sin permisos */ }
  }, [escenarios, horizonte, nombreNegocio])

  return (
    <div className="min-h-screen bg-[#F8F7F4] px-4 py-8 flex flex-col items-center gap-6">
      <div className="w-full max-w-lg flex flex-col gap-6">

        {/* Encabezado */}
        <div className="text-center">
          <p className="text-sm text-green-600 font-semibold uppercase tracking-widest mb-1">Análisis completado</p>
          <h1 className="text-2xl font-bold text-gray-900">
            {nombreNegocio ? `Proyección para ${nombreNegocio}` : 'Tu proyección financiera'}
          </h1>
          <p className="text-gray-500 mt-1 text-sm">
            Basado en <TooltipSimple termino="Simulación Monte Carlo">10,000 escenarios simulados</TooltipSimple> para los próximos {horizonte} meses
          </p>
        </div>

        {/* Escenario optimista */}
        <EscenarioCard
          emoji="😊"
          tipo="optimista"
          colorBg="bg-green-50"
          colorBorde="border-green-200"
          colorTitulo="text-green-700"
          titulo="Si todo va bien"
          subtitulo="En 9 de cada 10 escenarios posibles"
          valor={formatBOB(escenarios.p95)}
          detalle={`${formatBOBMes(escenarios.p95)} por mes en promedio`}
          equivalente={calcularEquivalente(escenarios.p95, tipoNegocio)}
        />

        {/* Escenario probable */}
        <EscenarioCard
          emoji="👍"
          tipo="probable"
          colorBg="bg-blue-50"
          colorBorde="border-blue-200"
          colorTitulo="text-blue-700"
          titulo="Lo más probable"
          subtitulo="El escenario normal — mitad arriba, mitad abajo"
          valor={formatBOB(escenarios.p50)}
          detalle={`${formatBOBMes(escenarios.p50)} por mes`}
          equivalente={calcularEquivalente(escenarios.p50, tipoNegocio)}
          destacado
        />

        {/* Escenario difícil */}
        <EscenarioCard
          emoji="😟"
          tipo="dificil"
          colorBg="bg-orange-50"
          colorBorde="border-orange-200"
          colorTitulo="text-orange-700"
          titulo="Si las cosas van mal"
          subtitulo="Solo en el peor 5% de los casos"
          valor={formatBOB(escenarios.p5)}
          detalle={`${formatBOBMes(escenarios.p5)} por mes`}
          equivalente={calcularEquivalente(escenarios.p5, tipoNegocio)}
        />

        {/* Recomendación principal */}
        <div className={`rounded-2xl p-5 border-2 ${esViable ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
          <div className="flex items-start gap-3">
            <span className="text-2xl shrink-0" aria-hidden="true">{esViable ? '💡' : '⚠'}</span>
            <div>
              <p className={`font-bold text-lg ${esViable ? 'text-green-800' : 'text-red-800'}`}>
                {esViable
                  ? 'Tu negocio ES VIABLE según estos datos.'
                  : 'El negocio necesita ajustes antes de ser viable.'
                }
              </p>
              <p className={`text-sm mt-2 ${esViable ? 'text-green-700' : 'text-red-700'}`}>
                {esViable
                  ? `Para cubrirte ante el peor escenario, te recomendamos tener al menos ${formatBOB(reservaRecomendada)} de reserva.`
                  : 'Revisa tus gastos fijos y el precio de venta antes de continuar.'
                }
              </p>
            </div>
          </div>
        </div>

        {/* Nota metodológica — accesible pero discreta */}
        <div className="bg-gray-50 rounded-xl p-4">
          <p className="text-xs text-gray-500 leading-relaxed">
            <strong>¿Cómo calculamos esto?</strong> Usamos{' '}
            <TooltipSimple termino="Simulación Monte Carlo">simulación Monte Carlo</TooltipSimple>{' '}
            con los datos que ingresaste. Los resultados son proyecciones, no garantías.{' '}
            El{' '}<TooltipSimple termino="Percentil P5">P5</TooltipSimple>{' '}
            y el{' '}<TooltipSimple termino="Percentil P95">P95</TooltipSimple>{' '}
            representan el rango de incertidumbre.
          </p>
        </div>

        {/* Acciones */}
        <div className="flex flex-col gap-3">
          {/* Compartir — WhatsApp (Bolivia es muy WhatsApp) */}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={compartirWhatsApp}
              aria-label="Compartir resultados por WhatsApp"
              className="flex-1 py-3.5 rounded-2xl bg-[#25D366] text-white font-semibold hover:bg-[#20b958] active:scale-95 transition-all flex items-center justify-center gap-2"
            >
              <span aria-hidden="true">💬</span> Compartir por WhatsApp
            </button>
            <button
              type="button"
              onClick={copiarResultados}
              aria-label={copiado ? 'Resultados copiados' : 'Copiar resultados al portapapeles'}
              className="px-4 py-3.5 rounded-2xl border-2 border-gray-200 text-gray-500 hover:bg-gray-50 active:scale-95 transition-all flex items-center gap-1.5 shrink-0"
            >
              <span aria-hidden="true">{copiado ? '✓' : '📋'}</span>
              <span className="text-sm">{copiado ? 'Copiado' : 'Copiar'}</span>
            </button>
          </div>

          <div className="flex gap-3">
            {onDescargar && (
              <button
                type="button"
                onClick={onDescargar}
                aria-label="Descargar proyección en PDF"
                className="flex-1 py-4 rounded-2xl border-2 border-green-500 text-green-700 font-semibold hover:bg-green-50 active:scale-95 transition-all flex items-center justify-center gap-2"
              >
                <span aria-hidden="true">📄</span> Descargar PDF
              </button>
            )}
            {onNuevaSim && (
              <button
                type="button"
                onClick={onNuevaSim}
                className="flex-1 py-4 rounded-2xl bg-green-600 text-white font-bold hover:bg-green-700 active:scale-95 transition-all"
              >
                Nueva simulación
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

interface EscenarioCardProps {
  emoji: string
  tipo: string
  colorBg: string
  colorBorde: string
  colorTitulo: string
  titulo: string
  subtitulo: string
  valor: string
  detalle: string
  equivalente: string
  destacado?: boolean
}

function EscenarioCard({
  emoji, colorBg, colorBorde, colorTitulo,
  titulo, subtitulo, valor, detalle, equivalente, destacado,
}: EscenarioCardProps) {
  return (
    <div className={`rounded-2xl p-5 border ${colorBg} ${colorBorde} ${destacado ? 'ring-2 ring-blue-300 shadow-md' : ''}`}>
      <div className="flex items-start gap-3 mb-3">
        <span className="text-2xl" aria-hidden="true">{emoji}</span>
        <div>
          <p className={`font-bold text-lg ${colorTitulo}`}>{titulo}</p>
          <p className="text-xs text-gray-500 mt-0.5">{subtitulo}</p>
        </div>
      </div>
      <p className="text-3xl font-extrabold text-gray-900 mb-1">{valor}</p>
      <p className="text-sm text-gray-600">{detalle}</p>
      {equivalente && (
        <p className="text-xs text-gray-500 mt-2 italic">
          Eso es {equivalente}.
        </p>
      )}
    </div>
  )
}

export default ResultadoSimulacion
