// Copyright (c) 2025-2026 Sergio Denis Troche Mayta. Todos los derechos reservados.
// Software propietario de Kapitalya — kapitalya.com.bo
// Prohibida su copia, distribución o uso sin autorización escrita expresa.

/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL del backend Django para enlaces server-rendered. Vacío = same-origin. */
  readonly VITE_BACKEND_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
