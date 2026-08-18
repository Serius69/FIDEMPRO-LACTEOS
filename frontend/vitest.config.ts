import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

// Runner de tests de COMPONENTES (vitest + Testing Library + jsdom).
// Separado del smoke de contratos (`npm test` = node --test scripts/*.test.mjs,
// sigue intacto) y de `vite build` (este archivo no participa del build de
// producción ni del tsconfig del proyecto app, ver tests/tsconfig.json).
export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/**/*.test.{ts,tsx}'],
    css: false,
    restoreMocks: true,
  },
})
