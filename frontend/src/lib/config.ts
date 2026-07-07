// Copyright (c) 2025-2026 Sergio Denis Troche Mayta. Todos los derechos reservados.
// Software propietario de Kapitalya — kapitalya.com.bo

// Base URL del backend Django para enlaces directos a páginas server-rendered
// (admin, swagger, /business/create, descarga de PDF, login).
//
// Las llamadas a la API (ver api.ts) usan rutas relativas y pasan por el
// reverse-proxy same-origin, así que NO usan esta constante.
//
// - Desarrollo (sin env): apunta a http://localhost:8000 para que /admin y /swagger
//   funcionen aunque el Vite dev server corra en otro puerto.
// - Producción (sin env): cadena vacía → enlaces relativos al mismo origen
//   (el reverse-proxy enruta /admin, /swagger, /business, /report a Django).
// - Override en cualquier entorno definiendo VITE_BACKEND_URL en el .env del build.
export const BACKEND_URL: string =
  import.meta.env.VITE_BACKEND_URL ?? (import.meta.env.DEV ? 'http://localhost:8000' : '')

/** Construye una URL hacia una página/endpoint server-rendered de Django. */
export function backendUrl(path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`
  return `${BACKEND_URL}${p}`
}
