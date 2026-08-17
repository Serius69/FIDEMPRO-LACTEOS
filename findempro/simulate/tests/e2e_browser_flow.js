/**
 * E2E de navegador — flujo crítico de FindemproAI.
 *
 * Se ejecuta contra una instancia desechable (`findempro.settings.e2e`, SQLite en
 * archivo temporal). No toca ninguna base real ni el cluster.
 *
 *   E2E_BASE_URL=http://127.0.0.1:18800 \
 *   E2E_USER=e2e E2E_PASSWORD=... \
 *   node simulate/tests/e2e_browser_flow.js
 *
 * `PLAYWRIGHT_MODULE` permite apuntar a una instalación existente de Playwright
 * cuando el proyecto no la declara como dependencia.
 */
const PLAYWRIGHT_MODULE = process.env.PLAYWRIGHT_MODULE || 'playwright';
const { chromium } = require(PLAYWRIGHT_MODULE);

const BASE = process.env.E2E_BASE_URL || 'http://127.0.0.1:18800';
const USER = process.env.E2E_USER || 'e2e';
const PASSWORD = process.env.E2E_PASSWORD;
const OTHER_USER = process.env.E2E_OTHER_USER || 'e2e-otro';
const OTHER_PASSWORD = process.env.E2E_OTHER_PASSWORD || PASSWORD;

if (!PASSWORD) {
  console.error('Falta E2E_PASSWORD.');
  process.exit(2);
}

let ok = 0;
const failures = [];

function check(label, condition, detail = '') {
  if (condition) {
    ok += 1;
    console.log(`  OK   ${label}`);
  } else {
    failures.push(`${label} — ${detail}`);
    console.log(`  FALLA ${label} — ${detail}`);
  }
}

/** Errores de consola que revelan un fallo real de la página. */
function relevantConsoleErrors(messages) {
  return messages.filter((text) =>
    !/favicon|Failed to load resource: the server responded with a status of 404/i.test(text));
}

async function login(context, username, password) {
  const page = await context.newPage();
  await page.goto(`${BASE}/account/login/`, { waitUntil: 'domcontentloaded' });
  await page.fill('input[name="login"]', username);
  await page.fill('input[name="password"]', password);
  await Promise.all([
    page.waitForLoadState('domcontentloaded'),
    page.click('button[type="submit"], input[type="submit"]'),
  ]);
  return page;
}

/** Llama a la API del producto reutilizando la sesión del navegador. */
async function api(page, method, path, body) {
  return page.evaluate(async ({ method, path, body }) => {
    const csrf = document.cookie.split('; ')
      .find((c) => c.startsWith('csrftoken='))?.split('=')[1];
    const response = await fetch(path, {
      method,
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        ...(csrf ? { 'X-CSRFToken': csrf } : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    let payload = null;
    try { payload = await response.json(); } catch { payload = null; }
    return { status: response.status, payload };
  }, { method, path, body });
}

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.E2E_CHROMIUM_PATH || undefined,
    args: ['--no-sandbox'],
  });
  const context = await browser.newContext();
  const consoleErrors = [];
  context.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });

  try {
    console.log('== 1. Login ==');
    const page = await login(context, USER, PASSWORD);
    check('el login deja una sesión activa',
      !page.url().includes('/account/login'), page.url());

    console.log('\n== 2. Dashboard y negocio ==');
    await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });
    check('el dashboard carga', page.url().endsWith('/') && !page.url().includes('login'));
    await page.goto(`${BASE}/business/list/`, { waitUntil: 'domcontentloaded' });
    check('el listado de negocios carga',
      (await page.content()).includes('Negocio E2E'), 'no aparece el negocio sembrado');

    const businesses = await api(page, 'GET', '/modeling/businesses/');
    check('la API de negocios responde', businesses.status === 200, String(businesses.status));
    const businessId = businesses.payload?.businesses?.[0]?.id;
    check('el negocio del dueño está disponible', Boolean(businessId),
      JSON.stringify(businesses.payload)?.slice(0, 200));

    console.log('\n== 3. Modelo, validación y datos ==');
    const templates = await api(page, 'GET', '/modeling/templates/');
    check('el catálogo de plantillas responde', templates.status === 200, String(templates.status));
    const template = templates.payload?.templates?.[0];
    check('hay al menos una plantilla sintética', Boolean(template));

    let modelId = null;
    if (businessId && template) {
      const created = await api(page, 'POST', '/modeling/models/', {
        business_id: businessId,
        name: 'Modelo E2E',
        sector: template.sector,
        spec: template.spec,
      });
      check('se crea un modelo desde la plantilla',
        [200, 201].includes(created.status),
        `${created.status} ${JSON.stringify(created.payload)?.slice(0, 300)}`);
      modelId = created.payload?.model?.id;
    }

    if (modelId) {
      const validation = await api(page, 'POST', `/modeling/models/${modelId}/validate/`, {});
      check('la validación del modelo responde',
        [200, 400].includes(validation.status), String(validation.status));

      const preview = await api(page, 'POST', `/modeling/models/${modelId}/imports/`, {
        preview: true, rows: [], mapping: {},
      });
      check('la importación de datos valida la entrada en vez de romper',
        [200, 201, 400, 422].includes(preview.status), String(preview.status));

      console.log('\n== 4. Simulación, progreso y resultados ==');
      const run = await api(page, 'POST', `/modeling/models/${modelId}/simulate/`, {
        iterations: 200, seed: 20260817, engine: 'monte_carlo',
      });
      check('la simulación arranca o rechaza con motivo',
        [200, 201, 202, 400, 409, 422].includes(run.status),
        `${run.status} ${JSON.stringify(run.payload)?.slice(0, 300)}`);

      const runId = run.payload?.run?.id ?? run.payload?.id ?? run.payload?.run_id;
      if (runId) {
        let detail = null;
        for (let attempt = 0; attempt < 30; attempt += 1) {
          detail = await api(page, 'GET', `/modeling/runs/${runId}/`);
          const state = detail.payload?.status ?? detail.payload?.state;
          if (['completed', 'failed', 'cancelled', 'COMPLETED', 'FAILED'].includes(state)) break;
          await page.waitForTimeout(500);
        }
        const state = detail?.payload?.status ?? detail?.payload?.state;
        check('la ejecución termina en un estado explícito',
          ['completed', 'COMPLETED'].includes(state), String(state));
        check('el resultado declara la semilla usada',
          detail?.payload?.seed !== undefined || detail?.payload?.metadata?.seed !== undefined,
          JSON.stringify(detail?.payload)?.slice(0, 200));

        console.log('\n== 5. Escenarios y reporte ==');
        const scenarios = await api(page, 'GET', `/modeling/models/${modelId}/scenarios/`);
        check('los escenarios del modelo responden', scenarios.status === 200, String(scenarios.status));
        const report = await api(page, 'GET', `/modeling/runs/${runId}/report/`);
        check('el reporte de la ejecución responde',
          [200, 404].includes(report.status), String(report.status));
      }

      console.log('\n== 6. Casos negativos ==');
      const badEquation = await api(page, 'POST', `/modeling/models/${modelId}/scenarios/`, {
        label: 'Ecuación inválida', changes: { 'no.existe': 1 },
      });
      check('un símbolo desconocido se rechaza',
        [400, 422].includes(badEquation.status), String(badEquation.status));

      const nanChange = await api(page, 'POST', `/modeling/models/${modelId}/scenarios/`, {
        label: 'No finito', changes: { demand: 'NaN' },
      });
      check('un valor no finito se rechaza',
        [400, 422].includes(nanChange.status), String(nanChange.status));

      const badSeed = await api(page, 'POST', `/modeling/models/${modelId}/simulate/`, {
        iterations: 'muchas', seed: 'x',
      });
      check('iteraciones/semilla inválidas devuelven 400, no un 500',
        [400, 422].includes(badSeed.status), String(badSeed.status));

      const malformed = await page.evaluate(async (id) => {
        const csrf = document.cookie.split('; ')
          .find((c) => c.startsWith('csrftoken='))?.split('=')[1];
        const response = await fetch(`/modeling/models/${id}/simulate/`, {
          method: 'POST', credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json', ...(csrf ? { 'X-CSRFToken': csrf } : {}) },
          body: '{no es json',
        });
        return response.status;
      }, modelId);
      check('un JSON malformado devuelve 400, no un 500', malformed === 400, String(malformed));
    }

    console.log('\n== 7. Autorización entre dueños ==');
    if (modelId && OTHER_PASSWORD) {
      const otherContext = await browser.newContext();
      try {
        const otherPage = await login(otherContext, OTHER_USER, OTHER_PASSWORD);
        if (!otherPage.url().includes('/account/login')) {
          const stolen = await api(otherPage, 'GET', `/modeling/models/${modelId}/`);
          check('otro dueño no accede al modelo ajeno',
            [403, 404].includes(stolen.status), String(stolen.status));
          const stolenRun = await api(otherPage, 'POST', `/modeling/models/${modelId}/simulate/`, {
            iterations: 10, seed: 1,
          });
          check('otro dueño no puede simular el modelo ajeno',
            [403, 404].includes(stolenRun.status), String(stolenRun.status));
        } else {
          check('sesión del segundo dueño', false, 'no se pudo iniciar sesión');
        }
      } finally {
        await otherContext.close();
      }
    }

    const anonymous = await browser.newContext();
    try {
      const anonPage = await anonymous.newPage();
      const response = await anonPage.goto(`${BASE}/modeling/businesses/`,
        { waitUntil: 'domcontentloaded' });
      check('sin sesión la API de negocios no entrega datos',
        [302, 401, 403].includes(response.status()) || anonPage.url().includes('/account/login'),
        String(response.status()));
    } finally {
      await anonymous.close();
    }

    console.log('\n== 8. Consola del navegador ==');
    const errors = relevantConsoleErrors(consoleErrors);
    check('el flujo no deja errores de consola', errors.length === 0, errors.slice(0, 3).join(' | '));
  } finally {
    await context.close();
    await browser.close();
  }

  console.log(`\n${'='.repeat(55)}`);
  console.log(`OK: ${ok}   FALLAS: ${failures.length}`);
  failures.forEach((item) => console.log(`  - ${item}`));
  process.exit(failures.length ? 1 : 0);
})().catch((error) => {
  console.error('E2E abortado:', error);
  process.exit(2);
});
