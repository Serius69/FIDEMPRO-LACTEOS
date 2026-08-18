import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { OnboardingGuiado } from '@/components/OnboardingGuiado'

// El wizard guiado es la puerta de entrada de datos financieros del negocio
// (ventas, gastos fijos, horizonte). Verificamos que: (1) avanza paso a paso
// según el tipo de respuesta, (2) al terminar entrega TODAS las respuestas
// reales acumuladas (no un objeto vacío ni valores inventados), y (3)
// persiste/restaura el progreso en localStorage para que un dueño de PYME
// pueda cerrar la pestaña y retomar donde quedó.

function fillWholeWizard() {
  fireEvent.click(screen.getByRole('button', { name: /Tienda o comercio/ })) // tipo_negocio
  fireEvent.click(screen.getByRole('button', { name: 'Entre Bs. 5,000 y Bs. 20,000' })) // ventas_mes
  fireEvent.change(screen.getByPlaceholderText('Ej: 8,000'), { target: { value: '8000' } })
  fireEvent.click(screen.getByRole('button', { name: 'Continuar →' })) // gastos_fijos
  fireEvent.click(screen.getByRole('button', { name: /Entre 1 y 3 años/ })) // tiempo_operando
  fireEvent.click(screen.getByRole('button', { name: /¿Cuánto voy a ganar\?/ })) // objetivo
  fireEvent.click(screen.getByRole('button', { name: /12 meses/ })) // horizonte
}

beforeEach(() => {
  window.localStorage.clear()
})

describe('OnboardingGuiado', () => {
  it('starts on step 1 of 7 with the business-type question', () => {
    render(<OnboardingGuiado onCompletado={vi.fn()} />)
    expect(screen.getByText('Paso 1 de 7')).toBeInTheDocument()
    expect(screen.getByText('¿Qué tipo de negocio tienes?')).toBeInTheDocument()
  })

  it('advances through every step and calls onCompletado with the REAL accumulated answers, including the optional final field left blank', () => {
    const onCompletado = vi.fn()
    render(<OnboardingGuiado onCompletado={onCompletado} />)

    fillWholeWizard()
    expect(screen.getByText('¿Cómo se llama tu negocio?')).toBeInTheDocument()

    // Campo opcional: se salta explícitamente sin escribir nada.
    fireEvent.click(screen.getByRole('button', { name: 'Saltar este paso' }))

    expect(onCompletado).toHaveBeenCalledTimes(1)
    expect(onCompletado).toHaveBeenCalledWith({
      tipo_negocio: 'comercio',
      ventas_mes: '12500',
      gastos_fijos: '8000',
      tiempo_operando: '1_3',
      objetivo: 'rentabilidad',
      horizonte: '12',
    })
  })

  it('completes with a typed business name when the optional field is filled instead of skipped', () => {
    const onCompletado = vi.fn()
    render(<OnboardingGuiado onCompletado={onCompletado} />)
    fillWholeWizard()

    fireEvent.change(screen.getByPlaceholderText('Ej: Panadería Doña Carmen'), { target: { value: 'Mi Tienda' } })
    fireEvent.click(screen.getByRole('button', { name: '✓ Ver mi análisis' }))

    expect(onCompletado).toHaveBeenCalledWith(expect.objectContaining({ nombre_negocio: 'Mi Tienda' }))
  })

  it('does not let the user submit an empty numeric answer for gastos_fijos', () => {
    render(<OnboardingGuiado onCompletado={vi.fn()} />)
    fireEvent.click(screen.getByRole('button', { name: /Tienda o comercio/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Entre Bs. 5,000 y Bs. 20,000' }))

    expect(screen.getByText('¿Cuánto gastas cada mes en cosas fijas?')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Continuar →' })).toBeDisabled()
  })

  it('lets the user go back and change a previous answer', () => {
    render(<OnboardingGuiado onCompletado={vi.fn()} />)
    fireEvent.click(screen.getByRole('button', { name: /Tienda o comercio/ }))
    expect(screen.getByText('Paso 2 de 7')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Volver al paso anterior' }))
    expect(screen.getByText('Paso 1 de 7')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /Fabrico o produzco algo/ }))
    expect(screen.getByText('Paso 2 de 7')).toBeInTheDocument()
  })

  it('persists progress to localStorage on each step and restores it on remount', () => {
    const { unmount } = render(<OnboardingGuiado onCompletado={vi.fn()} />)
    fireEvent.click(screen.getByRole('button', { name: /Tienda o comercio/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Entre Bs. 5,000 y Bs. 20,000' }))
    expect(screen.getByText('Paso 3 de 7')).toBeInTheDocument()
    unmount()

    render(<OnboardingGuiado onCompletado={vi.fn()} />)
    expect(screen.getByText('Paso 3 de 7')).toBeInTheDocument()
    expect(screen.getByText('¿Cuánto gastas cada mes en cosas fijas?')).toBeInTheDocument()
  })

  it('clears the saved progress once the wizard is completed', () => {
    render(<OnboardingGuiado onCompletado={vi.fn()} />)
    fillWholeWizard()
    fireEvent.click(screen.getByRole('button', { name: 'Saltar este paso' }))
    expect(window.localStorage.getItem('findempro_onboarding')).toBeNull()
  })
})
