import { useState, useRef } from 'react'

// Diccionario de términos financieros → lenguaje boliviano simple
export const TERMINOS_SIMPLES: Record<string, { simple: string; explicacion: string; ejemplo?: string }> = {
  'VaR': {
    simple:     '¿Cuánto podrías perder en el peor caso?',
    explicacion:'El VaR mide la pérdida máxima que podría tener tu negocio en un período dado.',
    ejemplo:    'Si tu VaR es Bs. 5,000, significa que en el peor caso perderías hasta Bs. 5,000 en un mes.',
  },
  'Tasa de descuento': {
    simple:     '¿Cuánto vale para ti el dinero hoy vs en el futuro?',
    explicacion:'La tasa de descuento refleja que Bs. 1,000 hoy vale más que Bs. 1,000 en un año.',
    ejemplo:    'Si usas 10%, significa que prefieres recibir Bs. 1,000 hoy antes que Bs. 1,100 el próximo año.',
  },
  'Flujo de caja proyectado': {
    simple:     '¿Cuánta plata entra y sale cada mes?',
    explicacion:'Es el registro de todo el dinero que entra (ventas, préstamos) y sale (gastos, deudas) de tu negocio.',
    ejemplo:    'Si vendes Bs. 30,000 y gastas Bs. 22,000, tu flujo de caja es positivo: Bs. 8,000.',
  },
  'Simulación Monte Carlo': {
    simple:     'Probamos miles de escenarios distintos para tu negocio',
    explicacion:'En vez de predecir el futuro con un solo número, calculamos miles de posibles resultados y vemos cuáles son más probables.',
    ejemplo:    'Como lanzar un dado 10,000 veces para saber qué número sale más seguido.',
  },
  'Percentil P5': {
    simple:     'En el peor 5% de los casos...',
    explicacion:'Solo en 5 de cada 100 escenarios posibles, el resultado sería peor que esto.',
    ejemplo:    'Si el P5 es Bs. 5,000, solo en los peores 5 años de cada 100 ganarías menos de Bs. 5,000.',
  },
  'Percentil P95': {
    simple:     'En el mejor 95% de los casos...',
    explicacion:'En 95 de cada 100 escenarios posibles, el resultado sería mejor que el P5.',
    ejemplo:    'Si el P95 es Bs. 80,000, en la mayoría de escenarios ganarías hasta Bs. 80,000.',
  },
  'Capital de trabajo': {
    simple:     'La plata que necesitas para operar día a día',
    explicacion:'Es el dinero disponible para pagar gastos diarios: insumos, sueldos, servicios básicos, antes de cobrar tus ventas.',
    ejemplo:    'Si tienes que pagar Bs. 15,000 cada mes antes de cobrar, ese es tu capital de trabajo mínimo.',
  },
  'Punto de equilibrio': {
    simple:     '¿Cuánto necesitas vender para no perder plata?',
    explicacion:'Es el nivel de ventas donde tus ingresos igualan exactamente tus gastos — ni ganar ni perder.',
    ejemplo:    'Si tu punto de equilibrio es 200 panes por día, necesitas vender más de 200 para ganar algo.',
  },
  'EBITDA': {
    simple:     'Ganancia antes de impuestos y deudas',
    explicacion:'Es la ganancia de tu negocio antes de descontar impuestos, deudas e inversiones en equipos.',
    ejemplo:    'Si vendes Bs. 100,000 y gastas Bs. 70,000 en operación, tu EBITDA es Bs. 30,000.',
  },
  'TIR': {
    simple:     '¿Cuánto rinde tu inversión por año?',
    explicacion:'La Tasa Interna de Retorno es como el "interés" que te da tu propio negocio anualmente.',
    ejemplo:    'Si tu TIR es 25%, tu inversión rinde más que un depósito bancario que da 5-8% al año.',
  },
  'Volatilidad': {
    simple:     '¿Cuánto suben y bajan tus ventas?',
    explicacion:'Alta volatilidad significa que tus ventas cambian mucho de un mes al otro. Baja volatilidad = negocio más predecible.',
    ejemplo:    'Una heladería tiene alta volatilidad (vende mucho en verano, poco en invierno). Un supermercado tiene baja volatilidad.',
  },
  'WACC': {
    simple:     'Costo total de financiar tu negocio',
    explicacion:'Combina el costo de los préstamos que tienes y lo que esperan ganar los dueños del negocio.',
    ejemplo:    'Si tienes un préstamo al 12% y los socios esperan ganar 18%, tu WACC estará entre esos dos valores.',
  },
}

interface TooltipSimpleProps {
  termino: string
  children?: React.ReactNode
  className?: string
}

export function TooltipSimple({ termino, children, className = '' }: TooltipSimpleProps) {
  const [abierto, setAbierto] = useState(false)
  const btnRef = useRef<HTMLButtonElement>(null)
  const info   = TERMINOS_SIMPLES[termino]

  if (!info) {
    return <span className={className}>{children ?? termino}</span>
  }

  return (
    <span className={`relative inline-flex items-center gap-1 ${className}`}>
      <span>{children ?? termino}</span>
      <button
        ref={btnRef}
        type="button"
        onClick={() => setAbierto(a => !a)}
        onBlur={() => setTimeout(() => setAbierto(false), 150)}
        className="w-4 h-4 rounded-full bg-gray-200 hover:bg-green-200 text-gray-500 hover:text-green-700 text-xs font-bold flex items-center justify-center transition-colors shrink-0"
        aria-label={`¿Qué significa ${termino}?`}
        aria-expanded={abierto}
      >
        ?
      </button>

      {abierto && (
        <div
          role="tooltip"
          className="absolute bottom-full left-0 mb-2 w-72 bg-white rounded-2xl shadow-xl border border-gray-100 p-4 z-30 text-left"
        >
          {/* Triángulo */}
          <div className="absolute -bottom-2 left-4 w-4 h-4 bg-white border-r border-b border-gray-100 rotate-45"/>

          <div className="flex items-start gap-2 mb-2">
            <span className="text-green-600 font-bold text-sm shrink-0" aria-hidden="true">💡</span>
            <p className="font-semibold text-green-700 text-sm">{info.simple}</p>
          </div>

          <p className="text-xs text-gray-600 leading-relaxed mb-2">{info.explicacion}</p>

          {info.ejemplo && (
            <div className="bg-gray-50 rounded-xl p-2">
              <p className="text-xs text-gray-500"><strong>Ejemplo:</strong> {info.ejemplo}</p>
            </div>
          )}
        </div>
      )}
    </span>
  )
}

export default TooltipSimple
