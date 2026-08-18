import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ErrorBoundary from '@/components/ErrorBoundary'

// El ErrorBoundary es la última línea de defensa contra la pantalla en
// blanco: si un componente hijo lanza durante el render, la app entera no
// puede desaparecer sin explicación. Estos tests son de comportamiento real
// (montan un árbol que lanza de verdad), no de implementación interna.

function Bomb(): never {
  throw new Error('boom: fallo real de render')
}

function Calm() {
  return <p>contenido normal</p>
}

describe('ErrorBoundary', () => {
  it('renders children normally when nothing throws', () => {
    render(
      <ErrorBoundary>
        <Calm />
      </ErrorBoundary>,
    )
    expect(screen.getByText('contenido normal')).toBeInTheDocument()
  })

  it('catches a render error from a descendant and shows a recovery screen instead of crashing', () => {
    // React llama a console.error para errores no capturados; lo silenciamos
    // solo para no ensuciar la salida del test runner, no para ocultar un fallo.
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(
      <ErrorBoundary>
        <Bomb />
      </ErrorBoundary>,
    )

    // El fallback debe ser un error explícito, no una vista vacía ni el
    // contenido "exitoso" que se esperaba renderizar.
    const alert = screen.getByRole('alert')
    expect(alert).toHaveTextContent('Algo salió mal')
    expect(screen.queryByText('contenido normal')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Recargar página' })).toBeInTheDocument()

    consoleError.mockRestore()
  })

  it('"Reintentar" resets the boundary so a subsequently-fixed subtree can render again', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})

    let shouldThrow = true
    function Flaky() {
      if (shouldThrow) throw new Error('boom')
      return <p>recuperado</p>
    }

    const { rerender } = render(
      <ErrorBoundary>
        <Flaky />
      </ErrorBoundary>,
    )

    expect(screen.getByRole('alert')).toBeInTheDocument()

    // Se "arregla" la causa del error antes de reintentar (igual que un
    // usuario real reintentando después de que, p.ej., el estado padre cambió).
    shouldThrow = false
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    rerender(
      <ErrorBoundary>
        <Flaky />
      </ErrorBoundary>,
    )

    expect(screen.getByText('recuperado')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()

    consoleError.mockRestore()
  })
})
