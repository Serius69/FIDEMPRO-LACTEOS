import { expect, test } from '@playwright/test'
import { campo, erroresNoControlados, formatearComoLaPagina, iniciarSesion, irAlSpa, valorDeTarjeta } from './sesion'

// Gate de navegador de /simulate contra el Django REAL.
//
// Por qué existe: hasta b7567415b la página leía `time_series.periods` y
// `scenarios.pessimist` sobre un cuerpo donde ambas son LISTAS. El servidor
// respondía 200 y el render moría con `Cannot read properties of undefined
// (reading 'map')`. Ningún gate lo veía: el backend comprueba motor y estado
// HTTP, y vitest mockea `@/lib/api` entera. Sólo un navegador contra el
// servidor real prueba que el JSON que sale por el cable y la página que lo
// pinta son el mismo contrato.
//
// El camino es el del usuario: login de allauth → /simulate → botón Ejecutar →
// POST /simulate/api/v1/simulate/async/ (Celery eager en settings.e2e) →
// polling de /status/ → resultado en pantalla.

interface Escenario {
  name: string
  demand_percentile: number
  demand_value: number
  revenue: number
  gross_profit: number
  profit_margin_pct: number
}

interface ResultadoSimulacion {
  demand: { mean: number; std: number }
  revenue: { mean: number; p5: number; p95: number }
  profit: { mean: number; median: number; std: number; var_95: number; cvar_95: number }
  risk: { probability_of_loss: number; probability_breakeven: number; var_confidence_level: number }
  scenarios: Escenario[]
  time_series: { period: number; demand_mean: number; revenue_mean: number; profit_mean: number }[]
  metadata: { n_iterations: number; distribution_used: string; confidence_level: number }
}

test('la simulación Monte Carlo pinta en pantalla el resultado que devolvió el servidor', async ({ page }) => {
  const errores = erroresNoControlados(page)

  // El cuerpo REAL del servidor, capturado del cable: contra él se comprueba
  // que lo que se ve en pantalla son esos números y no otros.
  let resultado: ResultadoSimulacion | null = null
  const estados: number[] = []
  page.on('response', async (r) => {
    if (r.url().includes('/simulate/api/v1/simulate/async/')) estados.push(r.status())
    if (!r.url().includes('/simulate/api/v1/simulate/status/')) return
    const cuerpo = await r.json().catch(() => null)
    if (cuerpo?.state === 'SUCCESS') resultado = cuerpo.result as ResultadoSimulacion
  })

  await iniciarSesion(page)
  await irAlSpa(page, 'Simulación MC', 'Simulación Monte Carlo')

  await page.getByRole('button', { name: /Ejecutar Simulación/ }).click()

  // El bloque de resultados sólo se monta con `result` en el estado; antes del
  // arreglo el render de este mismo bloque reventaba y no llegaba a existir.
  await expect(page.getByText('Demanda media')).toBeVisible({ timeout: 120_000 })
  await expect(page.getByRole('alert')).toHaveCount(0)

  // Se encoló de verdad (202) y el estado terminó en SUCCESS con cuerpo.
  expect(estados).toContain(202)
  // El manejador de `response` es asíncrono: se espera a que haya leído el
  // cuerpo antes de comparar la pantalla contra él.
  await expect.poll(() => resultado !== null, { timeout: 20_000 }).toBe(true)
  const datos = resultado as unknown as ResultadoSimulacion

  // `time_series` es una LISTA de puntos por período: la página la recorre. Si
  // volviera a leerse como `time_series.periods`, esto es `undefined.map`.
  expect(Array.isArray(datos.time_series)).toBe(true)
  expect(datos.time_series.length).toBeGreaterThan(0)

  // `scenarios` es una LISTA de cinco escenarios nombrados, no un objeto con
  // `.pessimist`. Los cinco nombres tienen que estar en pantalla.
  expect(datos.scenarios).toHaveLength(5)
  for (const escenario of datos.scenarios) {
    const fila = page.locator('p').filter({ hasText: new RegExp(`^${escenario.name} `) })
    await expect(fila).toBeVisible()
    await expect(fila).toContainText(`percentil ${await formatearComoLaPagina(page, escenario.demand_percentile, 0)} de demanda`)
  }

  // Los números del cable, formateados con el mismo Intl que usa la página, en
  // la tarjeta que les corresponde.
  const pct = (n: number) => `${(n * 100).toFixed(1)}%`
  await expect(valorDeTarjeta(page, 'Demanda media'))
    .toHaveText(await formatearComoLaPagina(page, datos.demand.mean, 0))
  // La MEDIANA, no la media: el servidor emite `profit.median` desde b7567415b
  // y la tarjeta presenta el escenario típico, no el promedio.
  await expect(valorDeTarjeta(page, 'Beneficio típico (mediana)'))
    .toHaveText(`Bs. ${await formatearComoLaPagina(page, datos.profit.median, 0)}`)
  await expect(valorDeTarjeta(page, 'Ingresos esperados'))
    .toHaveText(`Bs. ${await formatearComoLaPagina(page, datos.revenue.mean, 0)}`)
  await expect(valorDeTarjeta(page, 'Probabilidad de pérdida'))
    .toHaveText(pct(datos.risk.probability_of_loss))
  // VaR/CVaR se rotulan con el nivel de confianza que el servidor dice haber
  // usado, no con un 95% fijo.
  await expect(valorDeTarjeta(page, `VaR ${pct(datos.risk.var_confidence_level)}`))
    .toHaveText(`Bs. ${await formatearComoLaPagina(page, datos.profit.var_95, 0)}`)

  // El pie declara la metadata que el servidor dice haber usado.
  await expect(page.getByText(new RegExp(`${datos.metadata.n_iterations.toLocaleString('en-US')} iteraciones`))).toBeVisible()
  await expect(page.getByText(new RegExp(`distribución ${datos.metadata.distribution_used}`))).toBeVisible()

  // Sharpe llega `null` con su motivo: la página lo dice, no inventa un número.
  await expect(page.getByText(/No aplica: el beneficio monetario no es una serie de retornos periodizados/)).toBeVisible()

  // Las gráficas se montaron de verdad (recharts dibujó su superficie SVG), y las DOS
  // en todos los anchos.
  //
  // Antes no era así: el panel de configuración tenía `w-72` fijo (288 px) dentro de un
  // contenedor `overflow-hidden`, así que a 360 px el bloque de resultados se quedaba con
  // ~72 px y recharts —que no dibuja nada en un contenedor de ancho 0— sólo alcanzaba a
  // pintar una. Eso era un defecto de layout real, no una limitación inevitable: la app
  // trae su propia navegación móvil, o sea que estos anchos se visitan. El panel ahora se
  // apila encima de los resultados por debajo de `md`, y las dos gráficas caben.
  await expect(page.locator('.recharts-surface')).toHaveCount(2)

  // La guarda del síntoma de producción: cero excepciones no controladas.
  expect(errores, `excepciones no controladas en la página: ${errores.join(' | ')}`).toEqual([])
})

test('un error del servidor se muestra como aviso, no como pantalla rota', async ({ page }) => {
  const errores = erroresNoControlados(page)

  await iniciarSesion(page)
  await irAlSpa(page, 'Simulación MC', 'Simulación Monte Carlo')

  // Demanda vacía → el backend responde 400 «Campo requerido faltante».
  await campo(page, 'Media de demanda (unidades)').fill('')
  await page.getByRole('button', { name: /Ejecutar Simulación/ }).click()

  const aviso = page.getByRole('alert')
  await expect(aviso).toBeVisible({ timeout: 60_000 })
  await expect(aviso).toContainText(/demand_mean/)
  // El formulario sigue en pie: el fallo no se llevó la página por delante.
  await expect(page.getByRole('button', { name: /Ejecutar Simulación/ })).toBeVisible()
  expect(errores, `excepciones no controladas en la página: ${errores.join(' | ')}`).toEqual([])
})
