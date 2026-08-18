import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { TooltipSimple } from '@/components/TooltipSimple'

// TooltipSimple traduce jerga financiera a lenguaje simple para PYMES
// bolivianas. Lo importante en términos de comportamiento: (1) un término
// conocido puede abrirse/cerrarse y muestra la explicación real del
// diccionario (no un placeholder genérico), y (2) un término NO reconocido
// no debe fingir tener una explicación — debe degradar a texto plano.

describe('TooltipSimple', () => {
  it('renders a known term as plain text with a help toggle, closed by default', () => {
    render(<TooltipSimple termino="VaR" />)
    expect(screen.getByText('VaR')).toBeInTheDocument()
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: '¿Qué significa VaR?' })).toHaveAttribute('aria-expanded', 'false')
  })

  it('opens the tooltip with the real explanation text for the term, not a generic stub', () => {
    render(<TooltipSimple termino="VaR" />)
    fireEvent.click(screen.getByRole('button', { name: '¿Qué significa VaR?' }))

    const tooltip = screen.getByRole('tooltip')
    expect(tooltip).toHaveTextContent('¿Cuánto podrías perder en el peor caso?')
    expect(tooltip).toHaveTextContent('El VaR mide la pérdida máxima')
    expect(screen.getByRole('button', { name: '¿Qué significa VaR?' })).toHaveAttribute('aria-expanded', 'true')
  })

  it('toggles closed again on a second click', () => {
    render(<TooltipSimple termino="TIR" />)
    const button = screen.getByRole('button', { name: '¿Qué significa TIR?' })
    fireEvent.click(button)
    expect(screen.getByRole('tooltip')).toBeInTheDocument()
    fireEvent.click(button)
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })

  it('does NOT fabricate an explanation for an unrecognized term — falls back to plain text with no help button', () => {
    render(<TooltipSimple termino="Este término no existe en el diccionario">Texto visible</TooltipSimple>)
    expect(screen.getByText('Texto visible')).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })

  it('falls back to the term itself as visible text when no children are provided', () => {
    render(<TooltipSimple termino="Un término desconocido" />)
    expect(screen.getByText('Un término desconocido')).toBeInTheDocument()
  })
})
