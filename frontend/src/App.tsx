import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from '@/components/Layout'

// Code-splitting: cada página se carga bajo demanda para reducir el bundle inicial
// (antes ~783 kB en un solo chunk). Recharts y otras libs pesadas solo se descargan
// cuando el usuario entra a Simulate/Forecast.
const Dashboard = lazy(() => import('@/pages/Dashboard'))
const Businesses = lazy(() => import('@/pages/Businesses'))
const Simulate = lazy(() => import('@/pages/Simulate'))
const ForecastPage = lazy(() => import('@/pages/Forecast'))
const Reports = lazy(() => import('@/pages/Reports'))
const OnboardingPage = lazy(() => import('@/pages/OnboardingPage'))

function PageFallback() {
  return (
    <div
      role="status"
      aria-live="polite"
      style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '3rem' }}
    >
      <span>Cargando…</span>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <Suspense fallback={<PageFallback />}>
        <Routes>
          {/* Ruta pública — onboarding sin layout de navegación */}
          <Route path="/onboarding" element={<OnboardingPage />} />

          {/* Rutas con Layout */}
          <Route path="/*" element={
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/businesses" element={<Businesses />} />
                <Route path="/simulate" element={<Simulate />} />
                <Route path="/forecast" element={<ForecastPage />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Layout>
          } />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
