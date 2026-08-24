import { defineConfig, devices } from '@playwright/test'

// Gate de navegador del onboarding público contra el backend REAL.
// El SPA arranca en la raíz en dev y proxya /api a Django (vite.config.ts), que
// es exactamente el camino por el que el visitante anónimo llega al simulador.
const executablePath = process.env.PLAYWRIGHT_EXECUTABLE_PATH
const python = process.env.FINDEMPRO_E2E_PYTHON ?? 'python3'
const sqlite = process.env.FINDEMPRO_E2E_SQLITE ?? '/tmp/findempro-e2e.sqlite3'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  reporter: [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:5188',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    launchOptions: executablePath ? { executablePath } : undefined,
    // El SPA no registra service worker hoy; si lo hiciera, las peticiones que
    // pasaran por él dejarían de verse desde el test.
    serviceWorkers: 'block',
  },
  webServer: [
    {
      command: `DJANGO_ENV=development SECRET_KEY=dev-only DEBUG=True ALLOWED_HOSTS=127.0.0.1,localhost DB_ENGINE=django.db.backends.sqlite3 DB_NAME=${sqlite} ${python} manage.py runserver 127.0.0.1:8000 --noreload`,
      cwd: '../findempro',
      url: 'http://127.0.0.1:8000/health/live/',
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 5188',
      url: 'http://127.0.0.1:5188',
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
  projects: [
    { name: 'desktop-1440', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'tablet-768', use: { ...devices['Desktop Chrome'], viewport: { width: 768, height: 1024 } } },
    { name: 'mobile-360', use: { ...devices['Desktop Chrome'], viewport: { width: 360, height: 800 } } },
  ],
})
