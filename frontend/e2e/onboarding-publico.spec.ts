import { expect, test, type Page } from '@playwright/test'

// El flujo público completo: elegir sector → declarar cifras → simular →
// ver el resultado. Corre contra el Django real, así que también sujeta el
// contrato entre el SPA y `/api/simulate/montecarlo/`, que es justo la ruta
// que el onboarding llamaba y que el backend no servía (404 → "no pudimos
// calcular tu proyección" para todo visitante sin cuenta).

async function completarOnboarding(page: Page) {
  await page.getByRole('button', { name: /Tienda o comercio/ }).click()
  await page.getByRole('button', { name: /Entre Bs\. 5,000 y Bs\. 20,000/ }).click()

  await page.getByPlaceholder('Ej: 8,000').fill('5000')
  await page.getByRole('button', { name: /Continuar/ }).click()

  await page.getByRole('button', { name: /Entre 1 y 3 años/ }).click()
  await page.getByRole('button', { name: /¿Cuánto voy a ganar\?/ }).click()
  await page.getByRole('button', { name: /12 meses/ }).click()

  // Último paso (opcional): se salta, que es el camino más corto y el que más
  // gente toma.
  await page.getByRole('button', { name: /Saltar este paso/ }).click()
}

test('un visitante sin cuenta obtiene su proyección', async ({ page }) => {
  const respuestas: number[] = []
  page.on('response', (r) => {
    if (r.url().includes('/api/simulate/montecarlo/')) respuestas.push(r.status())
  })

  await page.goto('/onboarding')
  await expect(page.getByText('¿Qué tipo de negocio tienes?')).toBeVisible()

  await completarOnboarding(page)

  // El backend responde de verdad: sin la ruta esto era 404.
  await expect.poll(() => respuestas, { timeout: 20_000 }).toContain(200)

  // Y el resultado se renderiza — no la pantalla de error.
  await expect(page.getByText(/No pudimos calcular tu proyección/)).toHaveCount(0)
  await expect(page.getByText(/escenario|proyección|resultado/i).first()).toBeVisible({ timeout: 20_000 })
})

test('el simulador público responde sin sesión iniciada', async ({ request }) => {
  const r = await request.post('/api/simulate/montecarlo/', {
    data: { ventas_mes: 12500, gastos_fijos: 5000, tipo_negocio: 'comercio', horizonte: 12, simulaciones: 2000 },
  })
  expect(r.status()).toBe(200)
  const d = await r.json()
  expect(d.p5).toBeLessThanOrEqual(d.p50)
  expect(d.p50).toBeLessThanOrEqual(d.p95)
  // La superficie pública calcula, no guarda estado del visitante.
  expect(d.persistido).toBe(false)
})
