// Copyright (c) 2025-2026 Sergio Denis Troche Mayta. Todos los derechos reservados.
// Software propietario de Kapitalya — kapitalya.com.bo
// Prohibida su copia, distribución o uso sin autorización escrita expresa.

import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

/**
 * Límite de error a nivel de aplicación. Captura cualquier excepción de render
 * en el árbol de componentes y muestra una pantalla de recuperación con marca
 * Kapitalya en lugar de dejar la pantalla en blanco (white-screen-of-death).
 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Observabilidad: integrable con Sentry / OTEL si se configura en el proyecto.
    console.error('[ErrorBoundary] Error no controlado en la interfaz:', error, info.componentStack)
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null })
  }

  render(): ReactNode {
    if (!this.state.hasError) return this.props.children

    const isDev = import.meta.env.DEV

    return (
      <div
        role="alert"
        aria-live="assertive"
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px',
          background: '#f5f7fa',
          fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
        }}
      >
        <div
          style={{
            maxWidth: '480px',
            width: '100%',
            background: '#ffffff',
            borderRadius: '12px',
            boxShadow: '0 4px 24px rgba(26, 58, 92, 0.12)',
            padding: '40px 32px',
            textAlign: 'center',
            borderTop: '4px solid #e8b800',
          }}
        >
          <div aria-hidden="true" style={{ fontSize: '48px', lineHeight: 1, marginBottom: '16px' }}>
            ⚠️
          </div>
          <h1 style={{ fontSize: '22px', fontWeight: 700, color: '#1a3a5c', margin: '0 0 8px' }}>
            Algo salió mal
          </h1>
          <p style={{ fontSize: '15px', color: '#4b5563', lineHeight: 1.5, margin: '0 0 24px' }}>
            Ocurrió un error inesperado en la aplicación. Puedes reintentar la operación o recargar la página.
          </p>

          {isDev && this.state.error && (
            <pre
              style={{
                textAlign: 'left',
                background: '#fef2f2',
                color: '#991b1b',
                border: '1px solid #fecaca',
                borderRadius: '6px',
                padding: '12px',
                fontSize: '12px',
                overflowX: 'auto',
                margin: '0 0 24px',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {this.state.error.message}
            </pre>
          )}

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={this.handleReset}
              style={{
                background: '#1a3a5c',
                color: '#ffffff',
                border: 'none',
                borderRadius: '8px',
                padding: '10px 20px',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Reintentar
            </button>
            <button
              type="button"
              onClick={() => window.location.reload()}
              style={{
                background: 'transparent',
                color: '#1a3a5c',
                border: '1px solid #cbd5e1',
                borderRadius: '8px',
                padding: '10px 20px',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Recargar página
            </button>
          </div>
        </div>
      </div>
    )
  }
}
