import { useEffect, useMemo, useState } from 'react'
import { CheckCircle2, Database, FileUp, Loader2, TriangleAlert } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { fitModelDistributions, getBusinessModels, importModelFile, previewModelFile, type DistributionFitResult } from '@/lib/api'
import type { BusinessModel } from '@/types'

type Format = 'json' | 'csv' | 'xlsx'

function parsePreview(file: File, onPreview: (rows: Record<string, unknown>[]) => void) {
  if (file.name.toLowerCase().endsWith('.json')) {
    file.text().then((text) => {
      try {
        const parsed: unknown = JSON.parse(text)
        onPreview(Array.isArray(parsed) ? parsed.filter((row): row is Record<string, unknown> => typeof row === 'object' && row !== null).slice(0, 5) : [])
      } catch { onPreview([]) }
    })
  } else if (file.name.toLowerCase().endsWith('.csv')) {
    file.text().then((text) => {
      const [headerLine, ...lines] = text.split(/\r?\n/).filter(Boolean)
      const headers = (headerLine ?? '').split(',').map((header) => header.trim())
      onPreview(lines.slice(0, 5).map((line) => Object.fromEntries(line.split(',').map((value, index) => [headers[index] || 'column_' + (index + 1), value.trim()]))))
    })
  } else onPreview([])
}

export default function DataImports() {
  const [models, setModels] = useState<BusinessModel[]>([])
  const [modelId, setModelId] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<Record<string, unknown>[]>([])
  const [mappingText, setMappingText] = useState('{}')
  const [receipt, setReceipt] = useState<{ status: string; rows_imported: number; error_rows: { row: number; error: string }[] } | null>(null)
  const [serverPreview, setServerPreview] = useState<{ rows_total: number; error_rows: { row: number; error: string }[] } | null>(null)
  const [observationsText, setObservationsText] = useState('')
  const [fitResult, setFitResult] = useState<DistributionFitResult | null>(null)
  const [fitting, setFitting] = useState(false)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => { getBusinessModels().then((response) => { setModels(response.models); setModelId(String(response.models[0]?.id ?? '')) }).catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false)) }, [])

  const format = useMemo<Format>(() => {
    if (!file) return 'json'
    if (file.name.toLowerCase().endsWith('.csv')) return 'csv'
    if (file.name.toLowerCase().endsWith('.xlsx')) return 'xlsx'
    return 'json'
  }, [file])

  async function submit() {
    if (!file || !modelId) return
    setUploading(true); setError(''); setReceipt(null)
    try {
      const mapping = JSON.parse(mappingText) as Record<string, string>
      const response = await importModelFile(modelId, file, format, mapping)
      setReceipt(response.import)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo importar el archivo.') }
    finally { setUploading(false) }
  }

  function useSafeSample() {
    const rows = [
      { period: 1, demand: 82, unit_price: 14, unit_cost: 8 },
      { period: 2, demand: 91, unit_price: 14, unit_cost: 8 },
      { period: 3, demand: 87, unit_price: 14, unit_cost: 8 },
      { period: 4, demand: 103, unit_price: 14, unit_cost: 8 },
      { period: 5, demand: 98, unit_price: 14, unit_cost: 8 },
    ]
    const sample = new File(
      [JSON.stringify(rows, null, 2)],
      'findempro-sample-generic.json',
      { type: 'application/json' },
    )
    setFile(sample)
    setPreview(rows)
    setMappingText('{}')
    setError('')
  }

  async function validatePreview() {
    if (!file || !modelId) return
    setUploading(true); setError(''); setServerPreview(null)
    try {
      const mapping = JSON.parse(mappingText) as Record<string, string>
      const response = await previewModelFile(modelId, file, format, mapping)
      setServerPreview({ rows_total: response.rows_total, error_rows: response.error_rows })
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo validar la previsualización.') }
    finally { setUploading(false) }
  }

  async function fitDistributions() {
    if (!modelId) return
    setFitting(true); setError(''); setFitResult(null)
    try {
      const parsed: unknown = JSON.parse(observationsText)
      if (!Array.isArray(parsed) || parsed.some((value) => typeof value !== 'number')) throw new Error('Usa un arreglo JSON de números finitos.')
      setFitResult(await fitModelDistributions(modelId, parsed))
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudieron ajustar las distribuciones.') }
    finally { setFitting(false) }
  }

  if (loading) return <div role="status" className="flex h-full items-center justify-center"><Loader2 className="h-7 w-7 animate-spin text-muted-foreground" /></div>
  return <div className="flex h-full flex-col overflow-hidden">
    <header className="flex shrink-0 items-center gap-3 border-b border-border px-6 py-4"><Database className="h-5 w-5 text-primary" /><div><h1 className="text-base font-semibold">Datos del modelo</h1><p className="mt-0.5 text-xs text-muted-foreground">Importa observaciones con procedencia explícita y validación antes de simular.</p></div></header>
    <div className="grid flex-1 gap-6 overflow-y-auto p-6 lg:grid-cols-[minmax(0,1fr)_360px]">
      <Card><CardHeader><CardTitle className="text-sm">Importar archivo</CardTitle></CardHeader><CardContent className="space-y-4">
        {error && <div role="alert" className="rounded-md border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">{error}</div>}
        <label className="block text-xs"><span className="mb-1 block text-muted-foreground">Modelo destino</span><select value={modelId} onChange={(event) => setModelId(event.target.value)} className="w-full rounded-md border border-input bg-background px-3 py-2">{models.map((model) => <option key={model.id} value={model.id}>{model.name} · {model.business_name}</option>)}</select></label>
        <label className="flex min-h-32 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-primary/40 bg-primary/5 p-4 text-center"><FileUp className="h-7 w-7 text-primary" /><span className="mt-2 text-xs font-medium">{file?.name ?? 'Selecciona CSV, XLSX o JSON'}</span><span className="mt-1 text-[11px] text-muted-foreground">Máximo 2 MB · hasta 10.000 filas</span><input type="file" accept=".csv,.xlsx,.json" className="sr-only" onChange={(event) => { const next = event.target.files?.[0] ?? null; setFile(next); if (next) parsePreview(next, setPreview) }} /></label>
        <label className="block text-xs"><span className="mb-1 block text-muted-foreground">Mapeo opcional (JSON)</span><textarea value={mappingText} onChange={(event) => setMappingText(event.target.value)} className="min-h-20 w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-[11px]" aria-label="Mapeo de columnas" /></label>
        <div className="flex flex-wrap gap-2"><Button variant="outline" onClick={useSafeSample} disabled={uploading}>Usar muestra genérica segura</Button><Button variant="outline" onClick={validatePreview} disabled={!file || !modelId || uploading}>Validar previsualización</Button><Button onClick={submit} disabled={!file || !modelId || uploading} className="gap-2">{uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileUp className="h-4 w-4" />} Importar y validar</Button></div>
      </CardContent></Card>
      <div className="space-y-4">
        <Card><CardHeader><CardTitle className="text-sm">Laboratorio de distribuciones</CardTitle></CardHeader><CardContent className="space-y-2"><p className="text-[11px] text-muted-foreground">Propuestas condicionadas a tus observaciones. No se publican automáticamente en el modelo.</p><textarea aria-label="Observaciones estadísticas" value={observationsText} onChange={(event) => setObservationsText(event.target.value)} placeholder="[12, 14, 13, 18, 15]" className="min-h-16 w-full rounded-md border border-input bg-background px-2 py-1.5 font-mono text-[11px]" /><Button variant="outline" size="sm" onClick={() => void fitDistributions()} disabled={fitting || !observationsText.trim()}> {fitting ? <Loader2 className="mr-1.5 inline h-3.5 w-3.5 animate-spin" /> : null} Proponer ajustes</Button>{fitResult && (() => { const selectedName = fitResult.ranking.selected_distribution; const selected = fitResult.candidates.find((candidate) => candidate.distribution === selectedName); return <div className="rounded border border-primary/20 bg-primary/5 p-2 text-[11px]"><p className="font-medium">{selected ? `Candidato por AIC: ${selected.distribution}` : 'Ranking no comparable entre familias'}</p>{selected && <p className="mt-1 text-muted-foreground">AIC: {selected.aic.toFixed(2)} · {selected.test_name}: {selected.statistic.toFixed(3)}</p>}<p className="mt-1 text-muted-foreground">p-value: no calculado cuando los parámetros usan la misma muestra.</p>{fitResult.requires_review && <p className="mt-1 text-amber-300">Requiere revisión antes de guardar · {fitResult.provenance}</p>}</div> })()}</CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">Previsualización</CardTitle></CardHeader><CardContent>{preview.length ? <div className="overflow-auto"><table className="w-full text-left text-[11px]"><thead><tr>{Object.keys(preview[0]).map((key) => <th key={key} className="border-b border-border px-2 py-2 font-medium">{key}</th>)}</tr></thead><tbody>{preview.map((row, index) => <tr key={index}>{Object.keys(preview[0]).map((key) => <td key={key} className="border-b border-border/50 px-2 py-2 text-muted-foreground">{String(row[key] ?? '')}</td>)}</tr>)}</tbody></table></div> : <p className="text-xs text-muted-foreground">La vista previa local está disponible para CSV y JSON. XLSX se valida en el servidor.</p>}</CardContent></Card>
        {serverPreview && <Card className={serverPreview.error_rows.length ? 'border-amber-500/30' : 'border-emerald-500/30'}><CardHeader><CardTitle className="text-sm">Validación server-side</CardTitle></CardHeader><CardContent className="space-y-2 text-xs"><p>Filas detectadas: <strong>{serverPreview.rows_total}</strong></p><p className={serverPreview.error_rows.length ? 'text-amber-300' : 'text-emerald-300'}>Errores de fila: {serverPreview.error_rows.length}</p>{serverPreview.error_rows.slice(0, 5).map((row) => <p key={row.row + row.error} className="text-[11px] text-amber-300">Fila {row.row}: {row.error}</p>)}</CardContent></Card>}
        {receipt && <Card className={receipt.status === 'validated' ? 'border-emerald-500/30' : 'border-amber-500/30'}><CardHeader><CardTitle className="flex items-center gap-2 text-sm">{receipt.status === 'validated' ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> : <TriangleAlert className="h-4 w-4 text-amber-400" />} Recibo {receipt.status}</CardTitle></CardHeader><CardContent className="space-y-2 text-xs"><p>Filas importadas: <strong>{receipt.rows_imported}</strong></p>{receipt.error_rows.length > 0 && <p className="text-amber-300">Filas con error: {receipt.error_rows.length}</p>}<p className="text-muted-foreground">Procedencia: IMPORTED. Los datos no se consideran verdad histórica automáticamente.</p></CardContent></Card>}
      </div>
    </div>
  </div>
}
