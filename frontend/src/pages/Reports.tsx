import { useEffect, useState } from 'react'
import { FileText, Loader2, Download, ExternalLink, RefreshCw } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getReports } from '@/lib/api'
import { backendUrl } from '@/lib/config'
import { fmtDate } from '@/lib/utils'
import type { Report } from '@/types'

export default function Reports() {
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  function load() {
    setLoading(true); setError('')
    getReports()
      .then(setReports)
      .catch((e) => setError(e instanceof Error ? e.message : 'Error'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <header className="flex items-center justify-between px-6 py-4 border-b border-border shrink-0">
        <div>
          <h1 className="text-base font-semibold">Reportes</h1>
          <p className="text-xs text-muted-foreground mt-0.5">{reports.length} reporte(s) disponibles</p>
        </div>
        <div className="flex gap-2">
          <Button type="button" variant="outline" size="sm" onClick={load} disabled={loading} className="gap-1.5" aria-label={loading ? 'Actualizando...' : 'Actualizar reportes'}>
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} aria-hidden="true" />
          </Button>
          <Button type="button" size="sm" className="gap-1.5" asChild>
            <a href={backendUrl('/report/create/')} target="_blank" rel="noreferrer">
              <FileText className="h-4 w-4" /> Crear reporte
            </a>
          </Button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-6 space-y-5">
        {error && (
          <div className="rounded-lg bg-amber-500/10 border border-amber-500/30 p-4 text-sm text-amber-400">
            {error}{' '}
            <a href={backendUrl('/report/list/')} target="_blank" rel="noreferrer" className="underline">Ver en Django →</a>
          </div>
        )}

        {loading ? (
          <div role="status" aria-label="Cargando reportes..." className="flex items-center justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-hidden="true" /></div>
        ) : reports.length === 0 ? (
          <div className="flex flex-col items-center gap-4 py-16 text-center">
            <FileText className="h-12 w-12 text-muted-foreground/30" />
            <div>
              <p className="text-sm font-medium">No hay reportes disponibles</p>
              <p className="text-xs text-muted-foreground mt-1">Genera tu primer reporte desde una simulación completada.</p>
            </div>
            <Button type="button" variant="outline" size="sm" asChild>
              <a href={backendUrl('/report/create/')} target="_blank" rel="noreferrer">Crear reporte en Django</a>
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {reports.map((r) => (
              <Card key={r.id}>
                <CardContent className="p-4">
                  <div className="flex items-start gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary shrink-0">
                      <FileText className="h-5 w-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-sm font-medium">{r.title ?? `Reporte #${r.id}`}</h3>
                        <Badge variant={r.is_active ? 'success' : 'secondary'}>{r.status ?? 'draft'}</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        Creado: {fmtDate(r.date_created)} · Actualizado: {fmtDate(r.last_updated)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Button type="button" variant="ghost" size="sm" className="gap-1.5 text-xs" asChild>
                        <a href={backendUrl(`/report/pdf/download/${r.id}/`)} target="_blank" rel="noreferrer">
                          <Download className="h-3.5 w-3.5" /> PDF
                        </a>
                      </Button>
                      <Button type="button" variant="outline" size="sm" className="gap-1.5 text-xs" asChild>
                        <a href={backendUrl(`/report/detail/${r.id}/`)} target="_blank" rel="noreferrer">
                          <ExternalLink className="h-3.5 w-3.5" /> Ver
                        </a>
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
