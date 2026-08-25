import { expect, test } from '@playwright/test'
import { erroresNoControlados, formatearComoLaPagina, iniciarSesion, irAlSpa, valorDeTarjeta } from './sesion'

// Gate de navegador de /forecast contra el Django REAL.
//
// Por qué existe: hasta b7567415b la página hacía `result.forecast.map(...)`
// sobre un cuerpo donde `forecast` es un OBJETO con series paralelas
// (`values`, `ci_lower`, `ci_upper`). El servidor respondía 200 y el render
// moría con `Cannot read properties of undefined (reading 'map')`. La tabla de
// valores pronosticados y la gráfica no llegaban a existir.

interface ResultadoPronostico {
  forecast: {
    periods: number
    values: number[]
    ci_lower: number[]
    ci_upper: number[]
    method_used: string
    confidence_level: number
    mape: number | null
    rmse: number | null
  }
}

test('el pronóstico pinta la tabla y la gráfica con los valores que devolvió el servidor', async ({ page }) => {
  const errores = erroresNoControlados(page)

  let resultado: ResultadoPronostico | null = null
  const estados: number[] = []
  page.on('response', async (r) => {
    if (!r.url().includes('/simulate/api/v1/forecast/')) return
    estados.push(r.status())
    const cuerpo = await r.json().catch(() => null)
    if (cuerpo?.forecast) resultado = cuerpo as ResultadoPronostico
  })

  await iniciarSesion(page)
  await irAlSpa(page, 'Pronóstico', 'Pronóstico de Demanda')

  await page.getByRole('button', { name: 'Generar Pronóstico' }).click()

  await expect(page.getByText('Valores pronosticados')).toBeVisible({ timeout: 60_000 })
  await expect(page.getByRole('alert')).toHaveCount(0)

  expect(estados).toContain(200)
  // El manejador de `response` es asíncrono: se espera a que haya leído el
  // cuerpo antes de comparar la pantalla contra él.
  await expect.poll(() => resultado !== null, { timeout: 20_000 }).toBe(true)
  const { forecast } = resultado as unknown as ResultadoPronostico

  // `forecast` es un OBJETO con series paralelas. Si volviera a tratarse como
  // un array, `forecast.values` sería `undefined` y la tabla no existiría.
  expect(Array.isArray(forecast.values)).toBe(true)
  expect(forecast.values).toHaveLength(forecast.periods)
  expect(forecast.ci_lower).toHaveLength(forecast.periods)
  expect(forecast.ci_upper).toHaveLength(forecast.periods)

  // Una fila por período pronosticado, con los tres números del cable.
  const filas = page.locator('table tbody tr')
  await expect(filas).toHaveCount(forecast.periods)
  for (let i = 0; i < forecast.periods; i += 1) {
    const fila = filas.nth(i)
    await expect(fila).toContainText(`+${i + 1}`)
    await expect(fila).toContainText(await formatearComoLaPagina(page, forecast.values[i], 0))
    await expect(fila).toContainText(await formatearComoLaPagina(page, forecast.ci_lower[i], 0))
    await expect(fila).toContainText(await formatearComoLaPagina(page, forecast.ci_upper[i], 0))
  }

  // Las tarjetas de calidad declaran lo que el servidor dice haber usado.
  await expect(valorDeTarjeta(page, 'Método usado')).toHaveText(forecast.method_used)
  await expect(valorDeTarjeta(page, 'Confianza')).toHaveText(`${(forecast.confidence_level * 100).toFixed(0)}%`)
  // RMSE viajaba permanentemente en None antes del arreglo; ahora es un número.
  expect(forecast.rmse).not.toBeNull()
  await expect(valorDeTarjeta(page, 'RMSE (unidades)')).toHaveText(await formatearComoLaPagina(page, forecast.rmse as number, 2))
  await expect(valorDeTarjeta(page, 'MAPE')).toHaveText(
    forecast.mape == null ? '—' : `${await formatearComoLaPagina(page, forecast.mape, 2)}%`,
  )

  // La gráfica compuesta (histórico + pronóstico + IC) se montó de verdad.
  await expect(page.locator('.recharts-surface')).toHaveCount(1)

  // La guarda del síntoma de producción: cero excepciones no controladas.
  expect(errores, `excepciones no controladas en la página: ${errores.join(' | ')}`).toEqual([])
})

test('menos de cinco observaciones se rechazan en el formulario, sin llamar al servidor', async ({ page }) => {
  const errores = erroresNoControlados(page)
  const llamadas: string[] = []
  page.on('request', (r) => {
    if (r.url().includes('/simulate/api/v1/forecast/')) llamadas.push(r.url())
  })

  await iniciarSesion(page)
  await irAlSpa(page, 'Pronóstico', 'Pronóstico de Demanda')

  await page.getByPlaceholder('100, 120, 115, 130, ...').fill('10, 20, 30')
  await page.getByRole('button', { name: 'Generar Pronóstico' }).click()

  const aviso = page.getByRole('alert')
  await expect(aviso).toBeVisible()
  await expect(aviso).toContainText('Ingresa al menos 5 puntos históricos.')
  expect(llamadas).toEqual([])
  expect(errores, `excepciones no controladas en la página: ${errores.join(' | ')}`).toEqual([])
})
