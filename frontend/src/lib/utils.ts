import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export const cn = (...i: ClassValue[]) => twMerge(clsx(i))

export const BUSINESS_TYPES: Record<number, string> = {
  1: 'Lácteos', 2: 'Agricultura', 3: 'Consumo Masivo', 4: 'Panadería',
  5: 'Carnicería', 6: 'Abarrotes', 7: 'Otro', 8: 'Manufactura Alimentaria',
  9: 'Manufactura', 10: 'Retail', 11: 'Mayorista', 12: 'Servicios',
  13: 'Salud', 14: 'Educación', 15: 'Logística', 16: 'Hospitalidad',
  17: 'Tecnología', 18: 'Construcción', 19: 'Financiero',
}

export const DISTRIBUTIONS = [
  { value: 'normal', label: 'Normal (Gaussiana)' },
  { value: 'lognormal', label: 'Log-Normal' },
  { value: 'gamma', label: 'Gamma' },
  { value: 'uniform', label: 'Uniforme' },
  { value: 'exponential', label: 'Exponencial' },
]

export const RISK_COLORS: Record<string, string> = {
  low: 'text-emerald-400', medium: 'text-amber-400', high: 'text-red-400',
  'bajo': 'text-emerald-400', 'medio': 'text-amber-400', 'alto': 'text-red-400',
}

export function fmtNum(n: number | null | undefined, decimals = 2): string {
  if (n == null) return '—'
  return n.toLocaleString('es-BO', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

export function fmtPct(n: number | null | undefined): string {
  if (n == null) return '—'
  return `${(n * 100).toFixed(1)}%`
}

export function fmtDate(d: string): string {
  return new Date(d).toLocaleDateString('es-BO', { day: '2-digit', month: 'short', year: 'numeric' })
}
