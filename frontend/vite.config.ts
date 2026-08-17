import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// En producción el SPA se sirve bajo /app/ (Django mantiene su UI en /).
// En dev el server corre en la raíz (:5177) con proxy hacia Django.
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/app/' : '/',
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  server: {
    port: 5177,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true, cookieDomainRewrite: 'localhost' },
      '/simulate': { target: 'http://localhost:8000', changeOrigin: true },
      '/business': { target: 'http://localhost:8000', changeOrigin: true },
      '/report': { target: 'http://localhost:8000', changeOrigin: true },
      '/user': { target: 'http://localhost:8000', changeOrigin: true },
      '/account': { target: 'http://localhost:8000', changeOrigin: true },
      '/health': { target: 'http://localhost:8000', changeOrigin: true },
      '/modeling': { target: 'http://localhost:8000', changeOrigin: true },
      '/static': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
}))
