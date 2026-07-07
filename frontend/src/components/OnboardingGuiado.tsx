import { useState, useEffect } from 'react'

const PASOS = [
  {
    id: 'tipo_negocio',
    pregunta: '¿Qué tipo de negocio tienes?',
    subtitulo: 'Esto nos ayuda a darte ejemplos que tengan sentido para ti.',
    tipo: 'opciones',
    opciones: [
      { valor: 'comercio',     emoji: '🏪', texto: 'Tienda o comercio'         },
      { valor: 'manufactura',  emoji: '🏭', texto: 'Fabrico o produzco algo'    },
      { valor: 'servicios',    emoji: '💼', texto: 'Ofrezco servicios'          },
      { valor: 'agropecuario', emoji: '🌾', texto: 'Agropecuario o alimentos'   },
      { valor: 'otro',         emoji: '📦', texto: 'Otro tipo de negocio'       },
    ],
  },
  {
    id: 'ventas_mes',
    pregunta: '¿Cuánto vendiste el mes pasado, más o menos?',
    subtitulo: 'No tiene que ser exacto. Un estimado está bien.',
    tipo: 'slider',
    opciones: [
      { valor: '5000',    texto: 'Menos de Bs. 5,000'           },
      { valor: '12500',   texto: 'Entre Bs. 5,000 y Bs. 20,000'  },
      { valor: '60000',   texto: 'Entre Bs. 20,000 y Bs. 100,000'},
      { valor: '100001',  texto: 'Más de Bs. 100,000'            },
    ],
  },
  {
    id: 'gastos_fijos',
    pregunta: '¿Cuánto gastas cada mes en cosas fijas?',
    subtitulo: 'Por ejemplo: alquiler, sueldos, servicios básicos.',
    tipo: 'numerico',
    ayuda: '💡 Suma: alquiler + sueldos + agua/luz/teléfono',
    placeholder: 'Ej: 8,000',
    moneda: 'BOB',
  },
  {
    id: 'tiempo_operando',
    pregunta: '¿Cuánto tiempo lleva operando tu negocio?',
    subtitulo: 'Esto afecta la confiabilidad de las proyecciones.',
    tipo: 'opciones',
    opciones: [
      { valor: 'nuevo',    emoji: '🌱', texto: 'Menos de 1 año'      },
      { valor: '1_3',      emoji: '📈', texto: 'Entre 1 y 3 años'    },
      { valor: '3_10',     emoji: '🏢', texto: 'Entre 3 y 10 años'   },
      { valor: 'maduro',   emoji: '🏆', texto: 'Más de 10 años'      },
    ],
  },
  {
    id: 'objetivo',
    pregunta: '¿Qué quieres saber sobre tu negocio?',
    subtitulo: 'Podemos empezar por lo que más te interesa.',
    tipo: 'opciones',
    opciones: [
      { valor: 'rentabilidad', emoji: '💰', texto: '¿Cuánto voy a ganar?'      },
      { valor: 'riesgo',       emoji: '🛡',  texto: '¿Cuál es el riesgo?'       },
      { valor: 'precio',       emoji: '🏷',  texto: '¿Cómo fijar el precio?'    },
      { valor: 'credito',      emoji: '🏦', texto: '¿Puedo obtener un crédito?' },
    ],
  },
  {
    id: 'horizonte',
    pregunta: '¿Para qué período quieres la proyección?',
    subtitulo: 'Mientras más largo, menos precisa pero más útil para planear.',
    tipo: 'opciones',
    opciones: [
      { valor: '3',  emoji: '📅', texto: '3 meses'  },
      { valor: '6',  emoji: '📆', texto: '6 meses'  },
      { valor: '12', emoji: '📊', texto: '12 meses' },
      { valor: '36', emoji: '🔭', texto: '3 años'   },
    ],
  },
  {
    id: 'nombre_negocio',
    pregunta: '¿Cómo se llama tu negocio?',
    subtitulo: 'Opcional — pero lo usaremos en tu reporte personalizado.',
    tipo: 'texto',
    placeholder: 'Ej: Panadería Doña Carmen',
    opcional: true,
  },
]

const CLAVE_GUARDADO = 'findempro_onboarding'

interface Respuestas { [key: string]: string }

interface OnboardingGuiadoProps {
  onCompletado: (respuestas: Respuestas) => void
}

export function OnboardingGuiado({ onCompletado }: OnboardingGuiadoProps) {
  const [pasoActual, setPasoActual] = useState(0)
  const [respuestas, setRespuestas] = useState<Respuestas>({})
  const [valorInput,  setValorInput]  = useState('')

  // Restaurar progreso guardado
  useEffect(() => {
    try {
      const guardado = JSON.parse(localStorage.getItem(CLAVE_GUARDADO) ?? 'null')
      if (guardado?.respuestas) {
        setRespuestas(guardado.respuestas)
        setPasoActual(Math.min(guardado.paso ?? 0, PASOS.length - 1))
      }
    } catch { /* ignore */ }
  }, [])

  // Guardar progreso en cada paso
  useEffect(() => {
    try {
      localStorage.setItem(CLAVE_GUARDADO, JSON.stringify({ respuestas, paso: pasoActual }))
    } catch { /* ignore */ }
  }, [respuestas, pasoActual])

  const paso = PASOS[pasoActual]
  const esUltimoPaso = pasoActual === PASOS.length - 1
  const pct = ((pasoActual) / PASOS.length) * 100

  const responder = (valor: string) => {
    const nuevas = { ...respuestas, [paso.id]: valor }
    setRespuestas(nuevas)
    avanzar(nuevas)
  }

  const avanzar = (nuevasRespuestas = respuestas) => {
    if (esUltimoPaso) {
      localStorage.removeItem(CLAVE_GUARDADO)
      onCompletado(nuevasRespuestas)
    } else {
      setPasoActual(p => p + 1)
      setValorInput('')
    }
  }

  const retroceder = () => {
    if (pasoActual > 0) {
      setPasoActual(p => p - 1)
      setValorInput(respuestas[PASOS[pasoActual - 1].id] ?? '')
    }
  }

  const saltarOpcional = () => avanzar()

  return (
    <div className="min-h-screen bg-[#F8F7F4] flex flex-col items-center justify-start px-4 pt-8 pb-16">
      <div className="w-full max-w-lg">
        {/* Encabezado */}
        <div className="flex items-center gap-3 mb-8">
          {pasoActual > 0 && (
            <button type="button"
              onClick={retroceder}
              className="text-gray-400 hover:text-gray-700 transition-colors text-lg"
              aria-label="Volver al paso anterior"
            >
              ←
            </button>
          )}
          <div className="flex-1">
            <div className="flex justify-between text-xs text-gray-500 mb-1.5">
              <span>Paso {pasoActual + 1} de {PASOS.length}</span>
              <span>ya casi terminas</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-2 bg-green-500 rounded-full transition-all duration-400"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        </div>

        {/* Pregunta */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 leading-tight">{paso.pregunta}</h1>
          <p className="text-gray-500 mt-2 text-sm">{paso.subtitulo}</p>
          {paso.opcional && (
            <span className="inline-block mt-2 text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
              Opcional
            </span>
          )}
        </div>

        {/* Opciones */}
        {paso.tipo === 'opciones' && (
          <div className="grid grid-cols-2 gap-3">
            {paso.opciones?.map(op => (
              <button type="button"
                key={op.valor}
                onClick={() => responder(op.valor)}
                className={`flex flex-col items-center gap-2 p-4 rounded-2xl border-2 transition-all active:scale-95 text-center ${
                  respuestas[paso.id] === op.valor
                    ? 'border-green-500 bg-green-50 shadow-md'
                    : 'border-gray-200 bg-white hover:border-green-300 hover:bg-green-50/50'
                }`}
              >
                {'emoji' in op && <span className="text-3xl">{op.emoji}</span>}
                <span className="text-sm font-medium text-gray-800 leading-tight">{op.texto}</span>
              </button>
            ))}
          </div>
        )}

        {/* Slider de rangos */}
        {paso.tipo === 'slider' && (
          <div className="flex flex-col gap-3">
            {paso.opciones?.map(op => (
              <button type="button"
                key={op.valor}
                onClick={() => responder(op.valor)}
                className={`w-full text-left px-5 py-4 rounded-2xl border-2 transition-all active:scale-[0.98] ${
                  respuestas[paso.id] === op.valor
                    ? 'border-green-500 bg-green-50 shadow-md'
                    : 'border-gray-200 bg-white hover:border-green-300'
                }`}
              >
                <span className="font-medium text-gray-800">{op.texto}</span>
              </button>
            ))}
          </div>
        )}

        {/* Numérico */}
        {paso.tipo === 'numerico' && (
          <div className="flex flex-col gap-4">
            {paso.ayuda && (
              <div className="bg-amber-50 rounded-xl p-3 text-sm text-amber-800">
                {paso.ayuda}
              </div>
            )}
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 font-medium">Bs.</span>
              <input
                type="number"
                value={valorInput}
                onChange={e => setValorInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && valorInput && responder(valorInput)}
                placeholder={paso.placeholder ?? '0'}
                className="w-full pl-12 pr-4 py-4 rounded-2xl border-2 border-gray-200 text-xl font-bold focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100 transition-all"
                inputMode="decimal"
                autoFocus
              />
            </div>
            <button type="button"
              onClick={() => valorInput && responder(valorInput)}
              disabled={!valorInput}
              className="w-full py-4 rounded-2xl bg-green-600 hover:bg-green-700 disabled:opacity-40 text-white font-bold text-lg active:scale-95 transition-all"
            >
              Continuar →
            </button>
          </div>
        )}

        {/* Texto libre */}
        {paso.tipo === 'texto' && (
          <div className="flex flex-col gap-4">
            <input
              type="text"
              value={valorInput}
              onChange={e => setValorInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && avanzar({ ...respuestas, [paso.id]: valorInput })}
              placeholder={paso.placeholder ?? 'Escribe aquí...'}
              className="w-full px-4 py-4 rounded-2xl border-2 border-gray-200 text-lg focus:outline-none focus:border-green-500 transition-all"
              autoFocus
            />
            <div className="flex gap-3">
              {paso.opcional && (
                <button type="button"
                  onClick={saltarOpcional}
                  className="flex-1 py-3 rounded-2xl border border-gray-200 text-gray-500 font-medium hover:bg-gray-50 transition-all"
                >
                  Saltar este paso
                </button>
              )}
              <button type="button"
                onClick={() => avanzar({ ...respuestas, [paso.id]: valorInput })}
                className="flex-1 py-3 rounded-2xl bg-green-600 text-white font-bold hover:bg-green-700 active:scale-95 transition-all"
              >
                {esUltimoPaso ? '✓ Ver mi análisis' : 'Continuar →'}
              </button>
            </div>
          </div>
        )}

        {/* Indicador guardado */}
        <p className="text-xs text-center text-gray-400 mt-6">
          💾 Progreso guardado — puedes cerrar y retomar después
        </p>
      </div>
    </div>
  )
}

export default OnboardingGuiado
