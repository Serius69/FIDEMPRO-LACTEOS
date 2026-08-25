import { expect, type Page } from '@playwright/test'

// Utilidades compartidas por los specs que entran a la parte autenticada del
// SPA (Simulación y Pronóstico). No es un archivo de test: Playwright sólo
// recoge `*.spec.ts`.

/**
 * Credenciales del usuario desechable que `playwright.config.ts` siembra en la
 * base SQLite del E2E antes de levantar Django. Se leen de aquí también desde
 * la config para que el seed y el login no puedan desincronizarse.
 */
export const USUARIO_E2E = process.env.FINDEMPRO_E2E_USER ?? 'e2e'
export const CORREO_E2E = process.env.FINDEMPRO_E2E_EMAIL ?? 'e2e@findempro.test'
export const CLAVE_E2E = process.env.FINDEMPRO_E2E_PASSWORD ?? 'e2e-desechable-1234'

/**
 * Inicia sesión por el formulario REAL de allauth (`/account/login/`), servido
 * por Django y proxyado por el dev-server de Vite, de modo que la cookie de
 * sesión y la de CSRF queden en el mismo origen desde el que el SPA hace fetch.
 * No hay atajo por API: es el camino por el que llega el usuario.
 */
export async function iniciarSesion(page: Page): Promise<void> {
  await page.goto('/account/login/')
  await page.locator('#id_login').fill(USUARIO_E2E)
  await page.locator('#id_password').fill(CLAVE_E2E)
  await Promise.all([
    page.waitForURL((url) => !url.pathname.startsWith('/account/login'), { timeout: 30_000 }),
    page.locator('form[action*="/account/login/"] button[type="submit"], form[action*="/account/login/"] input[type="submit"]').first().click(),
  ])
  // Si allauth rechazó las credenciales vuelve a pintar el formulario.
  await expect(page.locator('#id_password')).toHaveCount(0)
}

/**
 * Acumula toda excepción NO CONTROLADA de la página.
 *
 * Es exactamente el síntoma de producción que arregló b7567415b: el servidor
 * respondía 200 y el render explotaba con `undefined.map`, dejando la pantalla
 * en manos del ErrorBoundary. Un array no vacío al final del test significa que
 * el contrato entre el JSON real y la página se volvió a romper.
 */
export function erroresNoControlados(page: Page): string[] {
  const errores: string[] = []
  page.on('pageerror', (e) => errores.push(e.message))
  return errores
}

/**
 * Formatea un número con el MISMO `Intl` que usa la página (`fmtNum`,
 * es-BO), dentro del navegador, para poder afirmar sobre el texto exacto que
 * el usuario ve sin depender del ICU de Node.
 */
export function formatearComoLaPagina(page: Page, valor: number, decimales = 0): Promise<string> {
  return page.evaluate(
    ([n, d]) => (n as number).toLocaleString('es-BO', {
      minimumFractionDigits: d as number,
      maximumFractionDigits: d as number,
    }),
    [valor, decimales] as [number, number],
  )
}

/**
 * Localiza el VALOR de una tarjeta de KPI a partir de su etiqueta.
 *
 * Las tarjetas son `<p>etiqueta</p><p>valor</p>`, a veces con la etiqueta
 * envuelta junto al icono. Buscar el valor por su texto suelto choca con el
 * mismo número en los `<select>` del formulario, así que se ancla en la
 * etiqueta.
 */
export function valorDeTarjeta(page: Page, etiqueta: string) {
  // `normalize-space(.)` y NO `normalize-space(text())`: la etiqueta se escribe como
  // `<p>VaR {fmtPct(...)}</p>`, que en el DOM son DOS nodos de texto ("VaR " y "95.0%").
  // `text()` en XPath devuelve sólo el primero, así que comparar contra "VaR 95.0%" nunca
  // casaba. `.` concatena el contenido del elemento, que es lo que el usuario lee.
  const x = `normalize-space(.)=${JSON.stringify(etiqueta)}`
  return page.locator(`xpath=//p[${x}]/following-sibling::p[1] | //p[${x}]/../following-sibling::p[1]`)
}

/**
 * Localiza el `input` de un campo del formulario por el texto de su etiqueta.
 * Los `Label` del SPA no llevan `htmlFor`, así que `getByLabel` no los ve.
 */
export function campo(page: Page, etiqueta: string) {
  return page.locator(
    `xpath=//label[normalize-space(.)=${JSON.stringify(etiqueta)}]/following-sibling::input[1]`,
  )
}

/**
 * Navega a una página del SPA **por dentro**, haciendo clic en su enlace del
 * menú, en vez de `page.goto('/ruta')`.
 *
 * No es un capricho: en dev el SPA se sirve en la raíz y `vite.config.ts`
 * proxya `/simulate` a Django (lo necesita, porque `/simulate/api/v1/…` es del
 * backend). Un `goto('/simulate')` por tanto NO llega a la ruta de React —
 * llega a la vista Django `simulate_init_view.AppsView`. En producción no
 * colisionan porque el SPA se sirve bajo `/app/`, pero en dev sí.
 *
 * Entrar por el menú también es lo que hace el usuario, así que el gate mide el
 * camino real y de paso cubre que el enlace exista.
 *
 * El menú está duplicado (barra lateral `md:flex` y barra móvil `md:hidden`),
 * así que se filtra por el que de verdad se ve en este viewport.
 */
export async function irAlSpa(page: Page, enlace: string, titulo: RegExp | string): Promise<void> {
  if (new URL(page.url(), 'http://127.0.0.1:5188').pathname !== '/') {
    await page.goto('/')
  }
  await page.getByRole('link', { name: enlace }).locator('visible=true').first().click()
  await expect(page.getByRole('heading', { name: titulo })).toBeVisible({ timeout: 30_000 })
}
