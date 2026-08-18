import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, BarChart3, CheckCircle2, Download, GitCompareArrows, Loader2, LineChart, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cancelModelRun, compareModelRuns, getModelRuns, type ModelRunComparison, type ModelRunHistory } from '@/lib/api'

function number(value?: number) { return typeof value === 'number' ? value.toFixed(2) : '—' }

export default function Results() {
  const [runs, setRuns] = useState<ModelRunHistory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState<string[]>([])
  const [comparison, setComparison] = useState<{ baseline_run_id: string; comparisons: ModelRunComparison[] } | null>(null)

  async function load() {
    setLoading(true)
    setError('')
    try { setRuns((await getModelRuns()).runs) } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudieron cargar los resultados.') } finally { setLoading(false) }
  }

  useEffect(() => { void load() }, [])

  function toggleSelected(id: string) {
    setSelected((current) => current.includes(id) ? current.filter((value) => value !== id) : current.length < 10 ? [...current, id] : current)
    setComparison(null)
  }

  async function compareSelected() {
    if (selected.length < 2) return
    setError('')
    try { setComparison(await compareModelRuns(selected)) } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudieron comparar las ejecuciones.') }
  }

  async function cancelRun(id: string) {
    try { await cancelModelRun(id); await load() } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo cancelar la ejecución.') }
  }

  const completed = useMemo(() => runs.filter((run) => run.status === 'completed'), [runs])

  return <div className="flex h-full flex-col overflow-hidden">
    <header className="flex shrink-0 items-center justify-between border-b border-border px-6 py-4">
      <div className="flex items-center gap-3"><LineChart className="h-5 w-5 text-primary" /><div><h1 className="text-base font-semibold">Resultados y riesgo</h1><p className="mt-0.5 text-xs text-muted-foreground">Historial persistido por versión, escenario, semilla e incertidumbre.</p></div></div>
      <div className="flex gap-2"><Button variant="outline" size="sm" onClick={() => void compareSelected()} disabled={selected.length < 2} className="gap-1.5"><GitCompareArrows className="h-3.5 w-3.5" /> Comparar ({selected.length})</Button><Button variant="outline" size="sm" onClick={() => void load()} disabled={loading} className="gap-1.5"><RefreshCw className={'h-3.5 w-3.5 ' + (loading ? 'animate-spin' : '')} /> Actualizar</Button></div>
    </header>
    <div className="flex-1 overflow-y-auto p-6">
      {error && <div role="alert" className="mb-4 rounded-md border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">{error}</div>}
      {loading ? <div role="status" className="flex justify-center py-20"><Loader2 className="h-7 w-7 animate-spin text-muted-foreground" /></div> : runs.length === 0 ? <Card><CardContent className="flex flex-col items-center gap-3 py-16 text-center"><BarChart3 className="h-10 w-10 text-muted-foreground/40" /><p className="text-sm font-medium">Aún no hay resultados persistidos.</p><p className="max-w-md text-xs text-muted-foreground">Ejecuta un escenario desde un modelo versionado para ver sus percentiles, riesgo y trazabilidad.</p></CardContent></Card> : <>
        <div className="mb-5 grid gap-4 sm:grid-cols-3"><Card><CardContent className="p-4"><p className="text-xs text-muted-foreground">Ejecuciones</p><p className="mt-1 text-2xl font-semibold">{runs.length}</p></CardContent></Card><Card><CardContent className="p-4"><p className="text-xs text-muted-foreground">Completadas</p><p className="mt-1 text-2xl font-semibold text-emerald-400">{completed.length}</p></CardContent></Card><Card><CardContent className="p-4"><p className="text-xs text-muted-foreground">Con incertidumbre</p><p className="mt-1 text-2xl font-semibold text-primary">{completed.filter((run) => run.summary.p5 !== undefined && run.summary.p95 !== undefined).length}</p></CardContent></Card></div>
        {comparison && <Card className="mb-5"><CardHeader><CardTitle className="text-sm">Comparación de escenarios</CardTitle></CardHeader><CardContent className="overflow-auto"><table className="w-full text-left text-xs"><thead><tr><th className="pb-2">Escenario</th><th className="pb-2">Media</th><th className="pb-2">Δ media</th><th className="pb-2">P5</th><th className="pb-2">Δ P5</th><th className="pb-2">P95</th><th className="pb-2">No atendida</th><th className="pb-2">Δ no atendida</th><th className="pb-2">Servicio</th><th className="pb-2">Δ servicio</th></tr></thead><tbody>{comparison.comparisons.map((item) => <tr key={item.run_id} className="border-t border-border"><td className="py-2 font-medium">{item.scenario}{item.run_id === comparison.baseline_run_id ? ' · baseline' : ''}</td><td className="py-2">{number(item.summary.mean)}</td><td className="py-2">{number(item.delta.mean)}</td><td className="py-2">{number(item.summary.p5)}</td><td className="py-2">{number(item.delta.p5)}</td><td className="py-2">{number(item.summary.p95)}</td><td className="py-2">{number(item.summary.mean_unmet_demand)}</td><td className="py-2">{number(item.delta.mean_unmet_demand)}</td><td className="py-2">{item.summary.mean_stock_service_level === undefined ? '—' : (item.summary.mean_stock_service_level * 100).toFixed(1) + '%'}</td><td className="py-2">{item.delta.mean_stock_service_level === undefined ? '—' : (item.delta.mean_stock_service_level * 100).toFixed(1) + ' pp'}</td></tr>)}</tbody></table></CardContent></Card>}
        <div className="grid gap-4 lg:grid-cols-2">{runs.map((run) => <Card key={run.id}><CardHeader className="pb-2"><div className="flex items-start justify-between gap-3"><div className="flex gap-2"><input type="checkbox" aria-label={'Seleccionar ' + run.scenario} checked={selected.includes(run.id)} disabled={run.status !== 'completed'} onChange={() => toggleSelected(run.id)} className="mt-1" /><div><CardTitle className="text-sm">{run.model}</CardTitle><p className="mt-1 text-xs text-muted-foreground">{run.business} · v{run.version} · {run.scenario}</p></div></div>{run.status === 'completed' ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> : run.status === 'failed' ? <AlertTriangle className="h-4 w-4 text-rose-300" /> : <Loader2 className="h-4 w-4 animate-spin text-primary" />}</div></CardHeader><CardContent><div className="grid grid-cols-4 gap-2 text-xs"><div><p className="text-muted-foreground">Media</p><p className="mt-1 font-medium">{number(run.summary.mean)}</p></div><div><p className="text-muted-foreground">P5</p><p className="mt-1 font-medium">{number(run.summary.p5)}</p></div><div><p className="text-muted-foreground">P95</p><p className="mt-1 font-medium">{number(run.summary.p95)}</p></div><div><p className="text-muted-foreground">P pérdida</p><p className="mt-1 font-medium">{run.summary.probability_loss === undefined ? '—' : (run.summary.probability_loss * 100).toFixed(1) + '%'}</p></div></div>{(run.summary.mean_unmet_demand !== undefined || run.summary.mean_stock_service_level !== undefined) && <div className="mt-3 grid grid-cols-2 gap-2 rounded border border-amber-500/30 bg-amber-500/10 p-2 text-[11px]"><div><p className="text-amber-100/70">Demanda no atendida</p><p className="font-medium text-amber-100">{number(run.summary.mean_unmet_demand)}</p></div><div><p className="text-amber-100/70">Nivel de servicio inventario</p><p className="font-medium text-amber-100">{run.summary.mean_stock_service_level === undefined ? '—' : (run.summary.mean_stock_service_level * 100).toFixed(1) + '%'}</p></div></div>}{run.summary.financial && <div className="mt-3 grid gap-1 rounded border border-primary/20 bg-primary/5 p-2 text-[11px] text-muted-foreground"><span>Finanzas explícitas · Ingresos: {run.summary.financial.mean_revenue ?? run.summary.financial.revenue ?? "—"} · COGS: {run.summary.financial.cogs ?? "—"} · Costos: {run.summary.financial.mean_total_cost ?? run.summary.financial.total_cost ?? "—"}</span><span>Margen de contribución: {run.summary.financial.mean_contribution_margin ?? run.summary.financial.contribution_margin ?? "—"} · Resultado operativo: {run.summary.financial.mean_operating_result ?? run.summary.financial.operating_result ?? "—"} · ROI: {run.summary.financial.roi ?? "—"}</span></div>}{run.traceability && <div className="mt-3 rounded border border-border bg-muted/20 p-2 text-[11px] text-muted-foreground"><p className="font-medium text-foreground">Reproducibilidad y límites</p><p className="mt-1">Modelo v{run.traceability.model_version ?? run.version} · schema {run.traceability.schema_version ?? '—'} · {run.traceability.iterations ?? '—'} iteraciones</p><p>Seed: {run.traceability.seed ?? 'no fijada'} · engine: {run.traceability.engine ?? run.engine}</p><p className="mt-1 break-all text-[10px]">Hash: {run.traceability.content_hash ?? run.content_hash}</p><p className="mt-1 text-[10px]">Resultado condicional a datos, parámetros, supuestos, distribuciones y escenario; no es una garantía de la realidad.</p></div>}<p className="mt-4 border-t border-border pt-3 text-[11px] text-muted-foreground">Engine: {run.engine} · seed: {run.seed ?? 'no fijada'} · hash: {run.content_hash.slice(0, 12)}</p>{run.error && <div role="alert" className="mt-2 rounded border border-rose-500/30 bg-rose-500/10 p-2 text-xs text-rose-300"><p>{run.error.message}</p><p className="mt-1 text-rose-200/80">Dónde: {run.error.where} · Código: {run.error.code}</p><p className="mt-1 text-rose-200/80">Cómo corregirlo: {run.error.how_to_fix}</p></div>}{(run.status === 'queued' || run.status === 'running') && <Button variant="outline" size="sm" className="mt-3 text-rose-300" onClick={() => void cancelRun(run.id)}>Cancelar ejecución</Button>}{run.status === 'completed' && <a href={'/modeling/runs/' + run.id + '/report/'} className="mt-3 inline-flex items-center gap-1.5 text-xs text-primary hover:underline" download><Download className="h-3.5 w-3.5" /> Descargar reporte CSV</a>}</CardContent></Card>)}</div>
      </>}
    </div>
  </div>
}
