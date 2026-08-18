import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// Testing Library no limpia el DOM entre tests automáticamente cuando no se
// usa el entrypoint /vitest de testing-library con auto-cleanup; lo hacemos
// explícito para que cada test empiece con un DOM limpio.
afterEach(() => {
  cleanup()
})

// jsdom no implementa ResizeObserver; lo usan recharts (ResponsiveContainer)
// y algunos primitivos de Radix (posicionamiento de popovers). Un stub simple
// alcanza porque los tests no dependen de mediciones reales de layout.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
// @ts-expect-error -- polyfill mínimo solo para el entorno de test
globalThis.ResizeObserver = globalThis.ResizeObserver ?? ResizeObserverStub

// jsdom tampoco implementa PointerEvent.hasPointerCapture/setPointerCapture,
// que Radix UI (Select, etc.) invoca al interactuar. Sin esto, cualquier test
// que abra un <Select> de Radix lanza "target.hasPointerCapture is not a function".
if (typeof window !== 'undefined') {
  const proto = window.HTMLElement.prototype as unknown as {
    hasPointerCapture?: (id: number) => boolean
    setPointerCapture?: (id: number) => void
    releasePointerCapture?: (id: number) => void
    scrollIntoView?: () => void
  }
  proto.hasPointerCapture = proto.hasPointerCapture ?? (() => false)
  proto.setPointerCapture = proto.setPointerCapture ?? (() => {})
  proto.releasePointerCapture = proto.releasePointerCapture ?? (() => {})
  proto.scrollIntoView = proto.scrollIntoView ?? (() => {})
}
