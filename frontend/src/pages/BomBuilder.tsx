import { useEffect, useMemo, useState } from 'react'
import { Boxes, CheckCircle2, Loader2, Plus, Save, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { createModelVersion, getBusinessModel, getBusinessModels } from '@/lib/api'
import type { BusinessModel, ModelVersion } from '@/types'

type Entry = { id: string; name?: string; unit?: string }
type Component = { component_id: string; quantity: number; unit?: string; waste_pct?: number; yield_pct?: number; lead_time?: number }
type Bom = { id: string; product_id: string; items: Component[] }
type Spec = Record<string, unknown> & { products?: Entry[]; materials?: Entry[]; boms?: Bom[] }

export default function BomBuilder() {
  const [models, setModels] = useState<BusinessModel[]>([])
  const [modelId, setModelId] = useState('')
  const [version, setVersion] = useState<ModelVersion | null>(null)
  const [spec, setSpec] = useState<Spec>({})
  const [bomIndex, setBomIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getBusinessModels().then((response) => {
      setModels(response.models)
      if (response.models[0]) setModelId(response.models[0].id)
    }).catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!modelId) return
    setLoading(true)
    getBusinessModel(modelId).then((model) => {
      const current = model.current_version as ModelVersion | undefined
      setVersion(current ?? null)
      setSpec((current?.spec ?? {}) as Spec)
      setBomIndex(0)
      setSaved(false)
    }).catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false))
  }, [modelId])

  const products = useMemo(() => spec.products ?? [], [spec.products])
  const materials = useMemo(() => spec.materials ?? [], [spec.materials])
  const components = useMemo(() => [...products, ...materials], [products, materials])
  const boms = spec.boms ?? []
  const currentBom = boms[bomIndex]

  function updateBoms(next: Bom[]) {
    setSpec((current) => ({ ...current, boms: next }))
    setSaved(false)
  }

  function createBom() {
    const product = products[0]
    if (!product) return
    updateBoms([...boms, { id: 'bom-' + Date.now(), product_id: product.id, items: [] }])
    setBomIndex(boms.length)
  }

  function updateCurrentBom(patch: Partial<Bom>) {
    if (!currentBom) return
    updateBoms(boms.map((bom, index) => index === bomIndex ? { ...bom, ...patch } : bom))
  }

  function addComponent() {
    if (!currentBom || !components[0]) return
    updateCurrentBom({ items: [...currentBom.items, { component_id: components[0].id, quantity: 1, unit: 'unit', waste_pct: 0, yield_pct: 100 }] })
  }

  function updateComponent(index: number, patch: Partial<Component>) {
    if (!currentBom) return
    updateCurrentBom({ items: currentBom.items.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } : item) })
  }

  async function save() {
    if (!modelId) return
    setSaving(true); setError('')
    try {
      const response = await createModelVersion(modelId, spec)
      setVersion(response.version); setSaved(true)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo guardar la BOM.') }
    finally { setSaving(false) }
  }

  if (loading) return <div role="status" className="flex h-full items-center justify-center"><Loader2 className="h-7 w-7 animate-spin text-muted-foreground" /></div>
  return <div className="flex h-full flex-col overflow-hidden">
    <header className="flex shrink-0 items-center justify-between border-b border-border px-6 py-4"><div className="flex items-center gap-3"><Boxes className="h-5 w-5 text-primary" /><div><h1 className="text-base font-semibold">Productos y BOM</h1><p className="mt-0.5 text-xs text-muted-foreground">Estructura multinivel de materiales, cantidades, desperdicio y rendimiento.</p></div></div><Button onClick={save} disabled={saving || !version} className="gap-1.5">{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : saved ? <CheckCircle2 className="h-4 w-4" /> : <Save className="h-4 w-4" />} {saved ? 'Versión guardada' : 'Guardar versión'}</Button></header>
    <div className="flex flex-1 flex-col gap-5 overflow-y-auto p-6">
      {error && <div role="alert" className="rounded-md border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">{error}</div>}
      <Card><CardContent className="flex flex-wrap items-end gap-4 p-4"><label className="min-w-[280px] flex-1 text-xs"><span className="mb-1 block text-muted-foreground">Modelo / versión</span><select value={modelId} onChange={(event) => setModelId(event.target.value)} className="w-full rounded-md border border-input bg-background px-3 py-2">{models.map((model) => <option key={model.id} value={model.id}>{model.name} · v{typeof model.current_version === 'number' ? model.current_version : version?.version ?? '—'}</option>)}</select></label><div className="text-xs text-muted-foreground">Hash: <code className="text-primary">{version?.content_hash?.slice(0, 12) ?? '—'}</code></div></CardContent></Card>
      {products.length === 0 ? <Card><CardContent className="py-12 text-center text-sm text-muted-foreground">Este modelo aún no tiene productos. Añádelos desde el constructor visual antes de crear una BOM.</CardContent></Card> : <div className="grid min-h-0 gap-5 lg:grid-cols-[260px_minmax(0,1fr)]">
        <Card><CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle className="text-sm">BOMs del modelo</CardTitle><Button variant="outline" size="icon" aria-label="Nueva BOM" onClick={createBom}><Plus className="h-4 w-4" /></Button></CardHeader><CardContent className="space-y-2">{boms.map((bom, index) => <button key={bom.id} type="button" onClick={() => setBomIndex(index)} className={'w-full rounded-md border p-3 text-left text-xs ' + (index === bomIndex ? 'border-primary bg-primary/10' : 'border-border hover:border-primary/50')}><p className="font-medium">{products.find((product) => product.id === bom.product_id)?.name ?? bom.product_id}</p><p className="mt-1 text-muted-foreground">{bom.items.length} componentes</p></button>)}{boms.length === 0 && <p className="text-xs text-muted-foreground">Crea la primera BOM con el botón +.</p>}</CardContent></Card>
        <Card><CardHeader className="flex-row items-center justify-between space-y-0"><div><CardTitle className="text-sm">Árbol de componentes</CardTitle>{currentBom && <select aria-label="Producto terminado" value={currentBom.product_id} onChange={(event) => updateCurrentBom({ product_id: event.target.value })} className="mt-2 rounded-md border border-input bg-background px-2 py-1.5 text-xs">{products.map((product) => <option key={product.id} value={product.id}>{product.name ?? product.id}</option>)}</select>}</div><Button size="sm" variant="outline" onClick={addComponent} disabled={!currentBom} className="gap-1.5"><Plus className="h-3.5 w-3.5" /> Componente</Button></CardHeader><CardContent>{currentBom ? <div className="overflow-x-auto"><table className="w-full min-w-[680px] text-left text-xs"><thead><tr className="border-b border-border text-muted-foreground"><th className="px-2 py-2">Componente</th><th className="px-2 py-2">Cantidad</th><th className="px-2 py-2">Unidad</th><th className="px-2 py-2">Desperdicio %</th><th className="px-2 py-2">Rendimiento %</th><th className="px-2 py-2">Acción</th></tr></thead><tbody>{currentBom.items.map((item, index) => <tr key={index} className="border-b border-border/50"><td className="px-2 py-2"><select value={item.component_id} onChange={(event) => updateComponent(index, { component_id: event.target.value })} className="rounded-md border border-input bg-background px-2 py-1.5">{components.map((component) => <option key={component.id} value={component.id}>{component.name ?? component.id}</option>)}</select></td><td className="px-2 py-2"><input type="number" min="0.0001" step="0.0001" value={item.quantity} onChange={(event) => updateComponent(index, { quantity: Number(event.target.value) })} className="w-24 rounded-md border border-input bg-background px-2 py-1.5" /></td><td className="px-2 py-2"><input value={item.unit ?? ''} onChange={(event) => updateComponent(index, { unit: event.target.value })} className="w-20 rounded-md border border-input bg-background px-2 py-1.5" /></td><td className="px-2 py-2"><input type="number" min="0" max="99.99" step="0.01" value={item.waste_pct ?? 0} onChange={(event) => updateComponent(index, { waste_pct: Number(event.target.value) })} className="w-20 rounded-md border border-input bg-background px-2 py-1.5" /></td><td className="px-2 py-2"><input type="number" min="0" max="100" step="0.01" value={item.yield_pct ?? 100} onChange={(event) => updateComponent(index, { yield_pct: Number(event.target.value) })} className="w-20 rounded-md border border-input bg-background px-2 py-1.5" /></td><td className="px-2 py-2"><Button variant="ghost" size="icon" aria-label="Eliminar componente" onClick={() => updateCurrentBom({ items: currentBom.items.filter((_, itemIndex) => itemIndex !== index) })}><Trash2 className="h-4 w-4 text-rose-400" /></Button></td></tr>)}</tbody></table>{currentBom.items.length === 0 && <p className="py-8 text-center text-xs text-muted-foreground">Añade componentes para construir el árbol del producto.</p>}</div> : <p className="py-12 text-center text-xs text-muted-foreground">Selecciona o crea una BOM.</p>}</CardContent></Card>
      </div>}
    </div>
  </div>
}
