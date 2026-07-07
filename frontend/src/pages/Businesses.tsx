import { useEffect, useState } from 'react'
import { Building2, Loader2, ExternalLink } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getBusinessDetails } from '@/lib/api'
import { backendUrl } from '@/lib/config'
import { BUSINESS_TYPES, fmtDate } from '@/lib/utils'

const SAMPLE_IDS = [1, 2, 3, 4, 5]

export default function Businesses() {
  const [businesses, setBusinesses] = useState<Record<number, unknown>[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.allSettled(SAMPLE_IDS.map((id) => getBusinessDetails(id)))
      .then((results) => {
        const ok = results.filter((r) => r.status === 'fulfilled').map((r) => (r as PromiseFulfilledResult<unknown>).value)
        setBusinesses(ok as Record<number, unknown>[])
        if (ok.length === 0) setError('No se encontraron negocios o no tienes acceso.')
      })
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <header className="flex items-center justify-between px-6 py-4 border-b border-border shrink-0">
        <div>
          <h1 className="text-base font-semibold">Negocios</h1>
          <p className="text-xs text-muted-foreground mt-0.5">{businesses.length} negocio(s) accesibles</p>
        </div>
        <Button type="button" variant="outline" size="sm" className="gap-1.5" asChild>
          <a href={backendUrl('/business/create/')} target="_blank" rel="noreferrer">
            <ExternalLink className="h-3.5 w-3.5" /> Crear en Django
          </a>
        </Button>
      </header>

      <div className="flex-1 overflow-y-auto p-6 space-y-5">
        {error && (
          <div className="rounded-lg bg-amber-500/10 border border-amber-500/30 p-4 text-sm text-amber-400">
            {error}{' '}
            <a href={backendUrl('/business/list/')} target="_blank" rel="noreferrer" className="underline">Ver en Django →</a>
          </div>
        )}

        {loading ? (
          <div role="status" aria-label="Cargando negocios..." className="flex items-center justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-hidden="true" /></div>
        ) : businesses.length > 0 ? (
          <div className="grid grid-cols-2 gap-4">
            {businesses.map((b: Record<string, unknown>, i) => (
              <Card key={i}>
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/15 text-primary shrink-0">
                        <Building2 className="h-4 w-4" />
                      </div>
                      <CardTitle className="text-sm">{String(b.name ?? 'Sin nombre')}</CardTitle>
                    </div>
                    <Badge variant={(b.is_active as boolean) ? 'success' : 'secondary'}>
                      {(b.is_active as boolean) ? 'Activo' : 'Inactivo'}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-1.5 text-xs text-muted-foreground">
                    <p>Tipo: <span className="text-foreground">{BUSINESS_TYPES[b.type as number] ?? `Tipo ${String(b.type)}`}</span></p>
                    {b.date_created ? <p>Creado: {fmtDate(String(b.date_created))}</p> : null}
                    {b.last_updated ? <p>Actualizado: {fmtDate(String(b.last_updated))}</p> : null}
                  </div>
                  <div className="mt-3 flex gap-2">
                    <Button type="button" variant="outline" size="sm" className="text-xs gap-1" asChild>
                      <a href={backendUrl(`/business/overview/${b.id}/`)} target="_blank" rel="noreferrer">
                        <ExternalLink className="h-3 w-3" /> Ver detalle
                      </a>
                    </Button>
                    <Button type="button" variant="ghost" size="sm" className="text-xs gap-1" asChild>
                      <a href={`/simulate?business_id=${b.id}`}>Simular →</a>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4 py-16 text-center">
            <Building2 className="h-12 w-12 text-muted-foreground/30" />
            <div>
              <p className="text-sm font-medium">No hay negocios disponibles</p>
              <p className="text-xs text-muted-foreground mt-1">Crea uno desde el panel de Django o verifica tu sesión.</p>
            </div>
            <Button type="button" variant="outline" size="sm" asChild>
              <a href={backendUrl('/business/create/')} target="_blank" rel="noreferrer">
                Crear negocio en Django
              </a>
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
