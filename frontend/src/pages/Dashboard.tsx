import { useEffect, useState } from 'react'
import { Building2, PlayCircle, AlertTriangle, Loader2, RefreshCw, TrendingUp } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getDashboardData, getDashboardSummary } from '@/lib/api'
import { backendUrl } from '@/lib/config'
import { fmtDate } from '@/lib/utils'
import type { DashboardData, DashboardSummary } from '@/types'

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true); setError('')
    const [d, s] = await Promise.allSettled([getDashboardData(), getDashboardSummary()])
    if (d.status === 'fulfilled') setData(d.value)
    if (s.status === 'fulfilled') setSummary(s.value)
    if (d.status === 'rejected' && s.status === 'rejected') setError('No se pudo conectar con el backend Django')
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const kpis = [
    { label: 'Negocios', value: data?.businesses_count ?? summary?.total_businesses ?? '—', icon: <Building2 className="h-4 w-4" />, color: 'text-primary' },
    { label: 'Simulaciones', value: data?.simulations_count ?? summary?.active_simulations ?? '—', icon: <PlayCircle className="h-4 w-4" />, color: 'text-blue-400' },
    { label: 'Alertas pendientes', value: summary?.pending_alerts ?? (data?.risk_alerts?.length ?? '—'), icon: <AlertTriangle className="h-4 w-4" />, color: 'text-amber-400' },
    { label: 'Último análisis', value: data?.recent_simulations?.[0] ? fmtDate(data.recent_simulations[0].date_created) : '—', icon: <TrendingUp className="h-4 w-4" />, color: 'text-emerald-400' },
  ]

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <header className="flex items-center justify-between px-6 py-4 border-b border-border shrink-0">
        <div>
          <h1 className="text-base font-semibold">Dashboard</h1>
          <p className="text-xs text-muted-foreground mt-0.5">Findempro AI · Simulación Monte Carlo para PYMES</p>
        </div>
        <Button type="button" variant="outline" size="sm" onClick={load} disabled={loading} className="gap-1.5">
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} aria-hidden="true" /> Actualizar
        </Button>
      </header>

      <div className="flex-1 overflow-y-auto p-6 space-y-5">
        {error && (
          <div className="rounded-lg bg-amber-500/10 border border-amber-500/30 p-4 text-sm text-amber-400">
            <strong>Backend Django no alcanzable.</strong> Asegúrate de que el servidor corra en localhost:8000 y que estés autenticado.{' '}
            <a href={backendUrl('/account/login/?next=/')} className="underline hover:text-amber-300">Iniciar sesión →</a>
          </div>
        )}

        {loading && !data ? (
          <div role="status" aria-label="Cargando datos..." className="flex items-center justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-hidden="true" /></div>
        ) : (
          <>
            <div className="grid grid-cols-4 gap-4">
              {kpis.map(({ label, value, icon, color }) => (
                <Card key={label}><CardContent className="p-4">
                  <div className="flex justify-between items-start">
                    <p className="text-xs text-muted-foreground">{label}</p>
                    <span className={color}>{icon}</span>
                  </div>
                  <p className={`text-2xl font-bold mt-2 ${color}`}>{value}</p>
                </CardContent></Card>
              ))}
            </div>

            {data?.recent_simulations && data.recent_simulations.length > 0 && (
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm">Simulaciones recientes</CardTitle></CardHeader>
                <CardContent className="p-0">
                  <table className="w-full text-xs">
                    <thead><tr className="border-b border-border">
                      {['ID', 'Estado', 'Período', 'Confianza', 'Fecha'].map((h) => (
                        <th key={h} scope="col" className="px-4 py-2 text-left font-medium text-muted-foreground">{h}</th>
                      ))}
                    </tr></thead>
                    <tbody>
                      {data.recent_simulations.map((s) => (
                        <tr key={s.id} className="border-b border-border/50 hover:bg-muted/20">
                          <td className="px-4 py-2 text-muted-foreground">#{s.id}</td>
                          <td className="px-4 py-2">
                            <Badge variant={s.status === 'completed' ? 'success' : s.status === 'failed' ? 'danger' : s.status === 'processing' ? 'info' : 'secondary'}>
                              {s.status}
                            </Badge>
                          </td>
                          <td className="px-4 py-2">{s.quantity_time} {s.unit_time}</td>
                          <td className="px-4 py-2">{(s.confidence_level * 100).toFixed(0)}%</td>
                          <td className="px-4 py-2 text-muted-foreground">{fmtDate(s.date_created)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            )}

            {data?.risk_alerts && data.risk_alerts.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-400" /> Alertas de Riesgo
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {data.risk_alerts.map((alert) => (
                      <div key={alert.id} className="flex items-start gap-3 rounded-lg border border-border p-3">
                        <div className={`mt-1 h-2 w-2 rounded-full shrink-0 ${alert.level === 'high' ? 'bg-red-400' : alert.level === 'medium' ? 'bg-amber-400' : 'bg-emerald-400'}`} />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm">{alert.message}</p>
                          <p className="text-[11px] text-muted-foreground mt-0.5">{fmtDate(alert.created_at)}</p>
                        </div>
                        <Badge variant={alert.level === 'high' ? 'danger' : alert.level === 'medium' ? 'warning' : 'success'}>{alert.level}</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Quick actions */}
            <div className="grid grid-cols-3 gap-4">
              {[
                { label: 'Nueva Simulación', desc: 'Ejecuta Monte Carlo con 10,000 escenarios', href: '/simulate', icon: '🎲' },
                { label: 'Ver Negocios', desc: 'Gestiona tus empresas y productos', href: '/businesses', icon: '🏢' },
                { label: 'Generar Reporte', desc: 'PDF con análisis completo', href: '/reports', icon: '📊' },
              ].map(({ label, desc, href, icon }) => (
                <a key={label} href={href} className="flex items-start gap-3 rounded-xl border border-border bg-card/50 p-4 hover:border-primary/50 hover:bg-primary/5 transition-colors">
                  <span className="text-2xl shrink-0">{icon}</span>
                  <div>
                    <p className="text-sm font-medium">{label}</p>
                    <p className="text-[11px] text-muted-foreground mt-0.5">{desc}</p>
                  </div>
                </a>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
