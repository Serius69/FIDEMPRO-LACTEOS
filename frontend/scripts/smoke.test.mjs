import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import { runInNewContext } from 'node:vm'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')

async function source(relativePath) {
  return readFile(resolve(root, relativePath), 'utf8')
}

test('critical frontend contracts', async (t) => {
  await t.test('application shell exposes model routes', async () => {
    const app = await source('src/App.tsx')
    for (const route of ['/models', '/models/:id', '/data', '/bom', '/processes', '/results']) {
      assert.match(app, new RegExp(route.replace(/[/:]/g, '\\$&')))
    }
  })
  await t.test('application shell keeps a mobile navigation path', async () => {
    const layout = await source('src/components/Layout.tsx')
    assert.match(layout, /Navegación móvil/)
    assert.match(layout, /md:hidden/)
  })
  await t.test('development proxy exposes the modeling API', async () => {
    const vite = await source('vite.config.ts')
    assert.match(vite, /['"]\/modeling['"]\s*:/)
  })
  await t.test('model builder exposes validation, engines, scenarios and diagrams', async () => {
    const builder = await source('src/pages/ModelBuilder.tsx')
    for (const contract of ['Validar modelo', 'Engine de simulación', 'Nuevo escenario', 'Vistas derivadas del modelo', 'Guardar plantilla propia', 'Exportar DSL', 'Siguiente trabajo recomendado', 'Faltan entradas']) {
      assert.match(builder, new RegExp(contract))
    }
    assert.match(builder, /Deshacer/)
    assert.match(builder, /Acercar canvas/)
    assert.match(builder, /Agregar relación causal/)
    assert.match(builder, /Minimapa del canvas/)
    assert.match(builder, /startNodeDrag/)
    assert.match(builder, /position:/)
  })
  await t.test('results exposes persisted comparison and report actions', async () => {
    const results = await source('src/pages/Results.tsx')
    assert.match(results, /compareModelRuns/)
    assert.match(results, /Descargar reporte CSV/)
    assert.match(results, /Seleccionar /)
    assert.match(results, /Cómo corregirlo/)
    assert.match(results, /run\.error\.where/)
    assert.match(results, /Reproducibilidad y límites/)
    assert.match(results, /traceability\.content_hash/)
  })
  await t.test('data imports expose server-side preview validation', async () => {
    const imports = await source('src/pages/DataImports.tsx')
    assert.match(imports, /Validar previsualización/)
    assert.match(imports, /previewModelFile/)
  })
  await t.test('API errors preserve corrective guidance', async () => {
    const api = await source('src/lib/api.ts')
    assert.match(api, /payload\.how_to_fix/)
    assert.match(api, /Cómo corregirlo/)
  })
  await t.test('data screen exposes review-only distribution fitting', async () => {
    const imports = await source('src/pages/DataImports.tsx')
    assert.match(imports, /Laboratorio de distribuciones/)
    assert.match(imports, /requires_review/)
  })
  await t.test('forecast chart uses the submitted history and labels starter data', async () => {
    const forecast = await source('src/pages/Forecast.tsx')
    assert.match(forecast, /setSubmittedHistory\(parsed\)/)
    assert.match(forecast, /\.\.\.submittedHistory\.map/)
    assert.doesNotMatch(forecast, /\.\.\.SAMPLE_DATA\.map/)
    assert.match(forecast, /EJEMPLO SINTÉTICO/)
  })
  await t.test('legacy report preview reconciles horizon ROI and unavailable investment metrics', async () => {
    const reportScript = await source('../findempro/static/js/report/create-simulation-report.js')
    const context = {
      console,
      document: { addEventListener() {} },
      window: { addEventListener() {} },
      setTimeout,
      clearTimeout,
      Intl,
    }
    runInNewContext(reportScript, context)

    const breakEven = context.performCalculations({ precio: 3, costo: 1, demanda: 10, gastosFijos: 10, inversion: 100, crecimiento: 0, horizonte: 10 })
    assert.equal(breakEven.utilidadNeta, 10)
    assert.equal(breakEven.roi, 0)
    assert.equal(breakEven.payback, 10)

    const unavailable = context.performCalculations({ precio: 2, costo: 1, demanda: 1, gastosFijos: 2, inversion: 0, crecimiento: 0, horizonte: 12 })
    assert.equal(unavailable.roi, null)
    assert.equal(unavailable.payback, 0)
  })
})
