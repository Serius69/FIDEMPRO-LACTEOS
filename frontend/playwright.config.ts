import { defineConfig, devices } from '@playwright/test'
import { CLAVE_E2E, CORREO_E2E, USUARIO_E2E } from './e2e/sesion'

// Gate de navegador contra el backend REAL: el onboarding público y las dos
// páginas autenticadas del SPA (Simulación Monte Carlo y Pronóstico).
// El SPA arranca en la raíz en dev y proxya /api, /simulate y /account a Django
// (vite.config.ts), que es exactamente el camino por el que llega el usuario.
const executablePath = process.env.PLAYWRIGHT_EXECUTABLE_PATH
const python = process.env.FINDEMPRO_E2E_PYTHON ?? 'python3'
const sqlite = process.env.FINDEMPRO_E2E_SQLITE ?? '/tmp/findempro-e2e.sqlite3'

// `findempro.settings.e2e` (no `development`) por dos razones que el E2E
// autenticado necesita y development no da:
//   · CELERY_TASK_ALWAYS_EAGER — `/simulate/api/v1/simulate/async/` encola en
//     Celery; sin worker el navegador esperaría para siempre.
//   · CSRF_TRUSTED_ORIGINS con el origen de Vite — el POST autenticado sale de
//     127.0.0.1:5188 y Django lo ve con otro host; sin declararlo es 403.
// DJANGO_ENV=testing es obligatorio: `settings/__init__.py` importa
// `development` por defecto ANTES de que se resuelva DJANGO_SETTINGS_MODULE, y
// development exige SECRET_KEY y lee `.env.development`.
const djangoEnv = [
  `DJANGO_ENV=testing`,
  `DJANGO_SETTINGS_MODULE=findempro.settings.e2e`,
  `E2E_SQLITE_PATH=${sqlite}`,
  `SECRET_KEY=e2e-insecure-key-1234567890-only-for-browser-tests`,
  `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver`,
].join(' ')

// Base desechable y sembrada desde cero en cada corrida: migrate + el usuario
// con el que el spec inicia sesión. `ensure_superuser` es idempotente y deja el
// email verificado, así que allauth no intenta mandar el correo de confirmación.
const djangoCommand = [
  `rm -f ${sqlite}`,
  `${djangoEnv} ${python} manage.py migrate --noinput`,
  `${djangoEnv} FINDEMPRO_SUPERUSER_PASSWORD='${CLAVE_E2E}' ${python} manage.py ensure_superuser --username '${USUARIO_E2E}' --email '${CORREO_E2E}'`,
  `${djangoEnv} ${python} manage.py runserver 127.0.0.1:8000 --noreload`,
].join(' && ')

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  // Este host es compartido y la simulación Monte Carlo corre DENTRO del
  // request (Celery eager): los 30 s por defecto no alcanzan cuando la máquina
  // está cargada, y un gate que se cae por eso no dice nada del producto.
  timeout: 180_000,
  expect: { timeout: 20_000 },
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
      command: djangoCommand,
      cwd: '../findempro',
      url: 'http://127.0.0.1:8000/health/live/',
      reuseExistingServer: false,
      timeout: 300_000,
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 5188',
      url: 'http://127.0.0.1:5188',
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
  projects: [
    { name: 'desktop-1440', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'tablet-768', use: { ...devices['Desktop Chrome'], viewport: { width: 768, height: 1024 } } },
    { name: 'mobile-360', use: { ...devices['Desktop Chrome'], viewport: { width: 360, height: 800 } } },
  ],
})
