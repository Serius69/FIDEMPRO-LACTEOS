import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, CheckCircle2, CircleDot, Download, GitBranch, Loader2, Redo2, Save, ShieldCheck, TrendingUp, Undo2, ZoomIn, ZoomOut } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { createModelScenario, createModelTemplate, createModelVersion, getBusinessModel, getModelDiagrams, getModelScenarios, runBusinessModel, runModelSensitivity, validateBusinessModel } from '@/lib/api'
import type { ModelReadiness, ModelVersion } from '@/types'

type ModelItem = { id?: string; name?: string; label?: string; expression?: string; unit?: string; initial?: number; value?: number; capacity?: number; hours_per_period?: number; cycle_time?: number; duration?: number; provenance?: string; position?: { x: number; y: number }; [key: string]: unknown }
type ModelSpec = Record<string, unknown> & { metadata?: { name?: string; description?: string; sector?: string }; variables?: ModelItem[]; stocks?: ModelItem[]; flows?: ModelItem[]; processes?: ModelItem[]; products?: ModelItem[]; materials?: ModelItem[]; services?: ModelItem[]; resources?: ModelItem[]; suppliers?: ModelItem[]; sales_channels?: ModelItem[]; employee_roles?: ModelItem[]; inventory_nodes?: ModelItem[]; equations?: ModelItem[]; causal_links?: ModelItem[] }
type Scenario = { id: string; name: string; label: string; changes: Record<string, number> }

const PALETTE = [
  ['stocks', 'Stock', 'Inventario, caja o capacidad'], ['flows', 'Flujo', 'Entradas y salidas'],
  ['processes', 'Proceso', 'Tareas y transformación'], ['resources', 'Recurso', 'Personas y máquinas'],
  ['employee_roles', 'Rol de personal', 'Capacidad y trabajo'], ['products', 'Producto', 'Producto o servicio'],
  ['materials', 'Material', 'Componente y costo de insumo'], ['services', 'Servicio', 'Blueprint de tareas y capacidad'],
  ['suppliers', 'Proveedor', 'Fuente de materiales y lead time'], ['sales_channels', 'Canal de venta', 'Ruta de ingresos y demanda'],
  ['inventory_nodes', 'Nodo de inventario', 'Ubicación o punto de stock'], ['equations', 'KPI / fórmula', 'Cálculo seguro'], ['causal_links', 'Relación causal', 'Explicación positiva/negativa'],
] as const

function items(spec: ModelSpec): { section: string; item: ModelItem }[] {
  return PALETTE.flatMap(([section]) => (spec[section] ?? []).map((item) => ({ section, item })))
}

function ReadinessSummary({ readiness }: { readiness?: ModelReadiness }) {
  if (!readiness) return <p className="text-[11px] leading-relaxed text-muted-foreground">Valida antes de simular para detectar referencias, ciclos, unidades y distribuciones incompletas.</p>
  return <div className="space-y-2 text-xs"><p>Completitud guardada: <strong>{readiness.score}%</strong></p>{readiness.missing.length ? <div className="rounded border border-amber-500/30 bg-amber-500/10 p-2"><p className="font-medium text-amber-200">Siguiente trabajo recomendado</p><ul className="mt-1 space-y-1 text-[10px] text-amber-100/80">{readiness.missing.map((dimension) => <li key={dimension}><span className="font-medium">{dimension}:</span> {readiness.actions?.[dimension] ?? 'Confirma esta dimensión antes de interpretar resultados.'}</li>)}</ul></div> : <p className="text-emerald-400">Las dimensiones configuradas están completas.</p>}</div>
}

export default function ModelBuilder() {
  const { id } = useParams<{ id: string }>()
  const [version, setVersion] = useState<ModelVersion | null>(null)
  const [spec, setSpec] = useState<ModelSpec>({})
  const [history, setHistory] = useState<ModelSpec[]>([])
  const [future, setFuture] = useState<ModelSpec[]>([])
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [dragging, setDragging] = useState<{ section: string; id: string; startX: number; startY: number; originX: number; originY: number } | null>(null)
  const [dragSnapshot, setDragSnapshot] = useState<ModelSpec | null>(null)
  const [panning, setPanning] = useState<{ startX: number; startY: number; originX: number; originY: number } | null>(null)
  const [name, setName] = useState('Modelo')
  const [loading, setLoading] = useState(true)
  const [validating, setValidating] = useState(false)
  const [saving, setSaving] = useState(false)
  const [savingTemplate, setSavingTemplate] = useState(false)
  const [running, setRunning] = useState(false)
  const [results, setResults] = useState<Record<string, Record<string, number>>>({})
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [selectedScenario, setSelectedScenario] = useState('')
  const [scenarioName, setScenarioName] = useState('')
  const [scenarioVariable, setScenarioVariable] = useState('demand')
  const [scenarioChange, setScenarioChange] = useState('0')
  const [templateName, setTemplateName] = useState('')
  const [selectedNodeKey, setSelectedNodeKey] = useState('')
  const [sensitivityVariable, setSensitivityVariable] = useState('demand')
  const [sensitivityChange, setSensitivityChange] = useState('1')
  const [sensitivityMetric, setSensitivityMetric] = useState<'profit' | 'completed' | 'queue_end' | 'utilization'>('profit')
  const [sensitivity, setSensitivity] = useState<{ variable: string; effect: number; change: number }[]>([])
  const [sensitivityRunning, setSensitivityRunning] = useState(false)
  const [engine, setEngine] = useState<'monte_carlo' | 'system_dynamics' | 'discrete_event'>('monte_carlo')
  const [validation, setValidation] = useState<{ valid: boolean; errors: { path: string; message: string }[]; warnings: { message: string }[]; readiness: ModelReadiness } | null>(null)
  const [diagrams, setDiagrams] = useState<Record<string, { title: string; nodes: { id: string; label: string; kind: string }[]; edges: { source: string; target: string; relation: string }[] }>>({})
  const [causalTarget, setCausalTarget] = useState('')
  const [causalPolarity, setCausalPolarity] = useState<'positive' | 'negative'>('positive')

  useEffect(() => {
    if (!id) return
    Promise.all([getBusinessModel(id), getModelScenarios(id), getModelDiagrams(id)]).then(([model, scenarioResponse, diagramResponse]) => {
      const current = model.current_version as ModelVersion | undefined
      setVersion(current ?? null)
      setSpec((current?.spec ?? {}) as ModelSpec)
      setHistory([])
      setFuture([])
      setPan({ x: 0, y: 0 })
      setName(model.name)
      setScenarios(scenarioResponse.scenarios)
      setDiagrams(diagramResponse.diagrams)
    }).finally(() => setLoading(false))
  }, [id])

  const nodes = useMemo(() => items(spec), [spec])
  const selectedNode = useMemo(() => nodes.find(({ section, item }) => `${section}:${item.id}` === selectedNodeKey) ?? null, [nodes, selectedNodeKey])
  const causalLinks = spec.causal_links ?? []

  async function runValidation() {
    if (!id) return
    setValidating(true)
    try { setValidation(await validateBusinessModel(id, spec)) } finally { setValidating(false) }
  }

  async function saveVersion() {
    if (!id) return
    setSaving(true)
    try {
      const response = await createModelVersion(id, spec)
      setVersion(response.version)
      setValidation(response.version.validation as typeof validation)
    } finally { setSaving(false) }
  }

  async function saveAsTemplate() {
    if (!templateName.trim()) return
    setSavingTemplate(true)
    try {
      await createModelTemplate({
        name: templateName.trim(),
        sector: String(spec.metadata?.sector ?? 'generic'),
        description: 'Plantilla creada desde un modelo editable; requiere confirmar sus parámetros.',
        spec,
      })
      setTemplateName('')
    } finally { setSavingTemplate(false) }
  }

  async function createScenario() {
    if (!id || !scenarioName.trim()) return
    const response = await createModelScenario(id, {
      name: scenarioName.trim(), label: 'CUSTOM', changes: { [scenarioVariable.trim() || 'demand']: Number(scenarioChange) || 0 },
    })
    setScenarios((current) => [...current, response.scenario])
    setSelectedScenario(response.scenario.id)
    setScenarioName('')
  }

  async function runSensitivity() {
    if (!id || !sensitivityVariable.trim()) return
    setSensitivityRunning(true)
    try {
      const metric = engine === 'discrete_event'
        ? (sensitivityMetric === 'profit' ? 'completed' : sensitivityMetric)
        : 'profit'
      const response = await runModelSensitivity(id, { changes: { [sensitivityVariable.trim()]: Number(sensitivityChange) || 0 }, iterations: 100, seed: 42, engine, metric })
      setSensitivity(response.result.factors.map((factor) => ({ variable: factor.variable, effect: factor.effect, change: factor.change })))
    } finally { setSensitivityRunning(false) }
  }

  async function runModel() {
    if (!id) return
    setRunning(true)
    try {
      const response = await runBusinessModel(id, { iterations: 100, seed: 42, engine, scenario_id: selectedScenario || undefined })
      if (response?.summary) setResults((current) => ({ ...current, [selectedScenario || 'base']: response.summary }))
    } finally { setRunning(false) }
  }

  function commitSpec(next: ModelSpec) {
    setHistory((current) => [...current, spec].slice(-30))
    setFuture([])
    setSpec(next)
  }

  function undo() {
    const previous = history[history.length - 1]
    if (!previous) return
    setFuture((current) => [spec, ...current].slice(0, 30))
    setHistory((current) => current.slice(0, -1))
    setSpec(previous)
  }

  function redo() {
    const next = future[0]
    if (!next) return
    setHistory((current) => [...current, spec].slice(-30))
    setFuture((current) => current.slice(1))
    setSpec(next)
  }

  function addComponent(section: string) {
    if (section === 'causal_links') return
    const key = section + '-' + Date.now()
    commitSpec({
      ...spec,
      [section]: [...((spec as Record<string, ModelItem[]>)[section] ?? []), { id: key, name: 'Nuevo ' + section }],
    })
  }

  function updateSelectedNode(field: string, rawValue: string) {
    if (!selectedNode?.item.id) return
    const numericFields = new Set(['value', 'initial', 'capacity', 'hours_per_period', 'cycle_time', 'duration'])
    const value: unknown = numericFields.has(field) ? (rawValue === '' ? undefined : Number(rawValue)) : rawValue
    commitSpec({
      ...spec,
      [selectedNode.section]: ((spec as Record<string, ModelItem[]>)[selectedNode.section] ?? []).map((item) => item.id === selectedNode.item.id ? { ...item, [field]: value } : item),
    })
  }

  function addCausalLink() {
    const source = selectedNode?.item.id
    if (!source || !causalTarget || source === causalTarget) return
    if (causalLinks.some((link) => link.source_id === source && link.target_id === causalTarget)) return
    commitSpec({
      ...spec,
      causal_links: [...causalLinks, { id: `causal-${Date.now()}`, source_id: source, target_id: causalTarget, polarity: causalPolarity }],
    })
  }

  function removeCausalLink(linkId: string) {
    commitSpec({ ...spec, causal_links: causalLinks.filter((link) => link.id !== linkId) })
  }

  function automaticPosition(index: number) {
    return { x: 100 + (index % 3) * 260, y: 110 + Math.floor(index / 3) * 130 }
  }

  function nodePosition(item: ModelItem, index: number) {
    return item.position && Number.isFinite(item.position.x) && Number.isFinite(item.position.y) ? item.position : automaticPosition(index)
  }

  function startNodeDrag(event: React.PointerEvent<SVGGElement>, section: string, item: ModelItem, index: number) {
    if (!item.id) return
    event.stopPropagation()
    event.currentTarget.setPointerCapture(event.pointerId)
    const position = nodePosition(item, index)
    setSelectedNodeKey(`${section}:${item.id}`)
    setDragSnapshot(spec)
    setDragging({ section, id: item.id, startX: event.clientX, startY: event.clientY, originX: position.x, originY: position.y })
  }

  function startCanvasPan(event: React.PointerEvent<SVGSVGElement>) {
    if (event.target !== event.currentTarget) return
    event.currentTarget.setPointerCapture(event.pointerId)
    setPanning({ startX: event.clientX, startY: event.clientY, originX: pan.x, originY: pan.y })
  }

  function moveCanvas(event: React.PointerEvent<SVGSVGElement>) {
    const rect = event.currentTarget.getBoundingClientRect()
    const unitsPerPixel = 900 / Math.max(rect.width, 1) / zoom
    if (dragging) {
      const dx = (event.clientX - dragging.startX) * unitsPerPixel
      const dy = (event.clientY - dragging.startY) * unitsPerPixel
      setSpec((current) => ({ ...current, [dragging.section]: ((current as Record<string, ModelItem[]>)[dragging.section] ?? []).map((item) => item.id === dragging.id ? { ...item, position: { x: Math.max(20, Math.min(780, dragging.originX + dx)), y: Math.max(20, Math.min(600, dragging.originY + dy)) } } : item) }))
    } else if (panning) {
      setPan({ x: panning.originX - (event.clientX - panning.startX) * unitsPerPixel, y: panning.originY - (event.clientY - panning.startY) * unitsPerPixel })
    }
  }

  function finishCanvasInteraction() {
    if (dragging && dragSnapshot) {
      setHistory((current) => [...current, dragSnapshot].slice(-30))
      setFuture([])
    }
    setDragging(null)
    setDragSnapshot(null)
    setPanning(null)
  }

  if (loading) return <div role="status" className="flex h-full items-center justify-center"><Loader2 className="h-7 w-7 animate-spin text-muted-foreground" /></div>

  return <div className="flex h-full flex-col overflow-hidden">
    <header className="flex shrink-0 items-center justify-between border-b border-border px-6 py-3">
      <div>
        <div className="flex items-center gap-2"><Link to="/models" className="text-xs text-muted-foreground hover:text-foreground">Modelos</Link><span className="text-xs text-muted-foreground">/</span><h1 className="text-sm font-semibold">{name}</h1><Badge variant="outline">v{version?.version ?? '—'}</Badge></div>
        <p className="mt-1 text-[11px] text-muted-foreground">Constructor visual · la versión ejecutada permanece inmutable.</p>
      </div>
      <div className="flex flex-wrap justify-end gap-2"><Button variant="outline" size="icon" aria-label="Deshacer" onClick={undo} disabled={!history.length}><Undo2 className="h-3.5 w-3.5" /></Button><Button variant="outline" size="icon" aria-label="Rehacer" onClick={redo} disabled={!future.length}><Redo2 className="h-3.5 w-3.5" /></Button><Button variant="outline" size="sm" className="gap-1.5" asChild><a href={`/modeling/models/${id}/export/`} download><Download className="h-3.5 w-3.5" /> Exportar DSL</a></Button><Button variant="outline" size="sm" className="gap-1.5" onClick={runValidation} disabled={validating}>{validating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ShieldCheck className="h-3.5 w-3.5" />} Validar modelo</Button><Button size="sm" className="gap-1.5" onClick={saveVersion} disabled={saving}>{saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />} Guardar versión</Button></div>
    </header>
    <div className="grid min-h-0 flex-1 grid-cols-[220px_minmax(0,1fr)_300px]">
      <aside className="overflow-y-auto border-r border-border bg-card/20 p-3" aria-label="Paleta de componentes">
        <p className="mb-3 px-2 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Componentes</p>
        <div className="space-y-2">{PALETTE.map(([key, label, description]) => <button key={key} type="button" onClick={() => addComponent(key)} className="w-full rounded-lg border border-border bg-card/50 p-3 text-left transition-colors hover:border-primary/50"><div className="flex items-center gap-2"><CircleDot className="h-3.5 w-3.5 text-primary" /><span className="text-xs font-medium">{label}</span></div><p className="mt-1 text-[10px] text-muted-foreground">{description}</p></button>)}</div>
        <div className="mt-5 rounded-lg border border-dashed border-primary/40 bg-primary/5 p-3"><p className="text-[11px] font-medium">Fuente de verdad</p><p className="mt-1 text-[10px] leading-relaxed text-muted-foreground">El canvas representa la especificación versionada; no guarda diagramas contradictorios.</p></div>
      </aside>
      <main className="relative min-w-0 overflow-auto bg-[radial-gradient(circle_at_1px_1px,hsl(var(--border)/.45)_1px,transparent_0)] [background-size:24px_24px]" aria-label="Canvas de modelo">
        <div className="absolute left-5 top-5 z-10 flex items-center gap-2 rounded-full border border-border bg-card/90 px-3 py-1.5 text-[10px] text-muted-foreground"><GitBranch className="h-3.5 w-3.5 text-primary" /> Estructura del negocio <span className="ml-2 border-l border-border pl-2">{Math.round(zoom * 100)}%</span><button type="button" aria-label="Alejar canvas" onClick={() => setZoom((value) => Math.max(0.6, Number((value - 0.1).toFixed(1))))}><ZoomOut className="h-3 w-3" /></button><button type="button" aria-label="Acercar canvas" onClick={() => setZoom((value) => Math.min(1.6, Number((value + 0.1).toFixed(1))))}><ZoomIn className="h-3 w-3" /></button><button type="button" aria-label="Centrar canvas" onClick={() => setPan({ x: 0, y: 0 })}>Centrar</button></div>
        <svg viewBox="0 0 900 650" className="h-full min-h-[650px] w-full touch-none" role="img" aria-label="Diagrama estructurado del modelo" onPointerDown={startCanvasPan} onPointerMove={moveCanvas} onPointerUp={finishCanvasInteraction} onPointerCancel={finishCanvasInteraction}><defs><marker id="arrow" viewBox="0 0 8 6" refX="6" refY="3" markerWidth="8" markerHeight="6" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="hsl(var(--primary))" /></marker></defs><g transform={`translate(${pan.x + (1 - zoom) * 450} ${pan.y + (1 - zoom) * 325}) scale(${zoom})`}>{causalLinks.map((link) => { const sourceIndex = nodes.findIndex(({ item }) => item.id === link.source_id); const targetIndex = nodes.findIndex(({ item }) => item.id === link.target_id); if (sourceIndex < 0 || targetIndex < 0) return null; const source = nodePosition(nodes[sourceIndex].item, sourceIndex); const target = nodePosition(nodes[targetIndex].item, targetIndex); return <line key={`causal-edge-${link.id}`} x1={source.x + 95} y1={source.y + 34} x2={target.x + 95} y2={target.y + 34} stroke={link.polarity === 'negative' ? 'hsl(var(--destructive))' : 'hsl(var(--primary))'} strokeWidth="2" strokeDasharray={link.polarity === 'negative' ? '6 3' : undefined} markerEnd="url(#arrow)" aria-label={`${String(link.source_id)} ${String(link.polarity)} ${String(link.target_id)}`} /> })}{nodes.slice(0, 12).map(({ section, item }, index) => { const position = nodePosition(item, index); const x = position.x; const y = position.y; return <g key={section + '-' + (item.id ?? index)} onPointerDown={(event) => startNodeDrag(event, section, item, index)} className="cursor-move"><rect x={x} y={y} width="190" height="68" rx="10" fill="hsl(var(--card))" stroke="hsl(var(--primary)/.65)" /><text x={x + 14} y={y + 23} fill="hsl(var(--foreground))" fontSize="12" fontWeight="600">{item.name ?? item.label ?? item.id ?? 'Componente'}</text><text x={x + 14} y={y + 43} fill="hsl(var(--muted-foreground))" fontSize="10">{section} · {item.unit ?? 'sin unidad'}</text></g> })}</g></svg>
        <div className="absolute bottom-5 right-5 rounded border border-border bg-card/90 p-2" aria-label="Minimapa del canvas"><p className="mb-1 text-[9px] text-muted-foreground">Minimapa</p><svg viewBox="0 0 900 650" className="h-20 w-28" role="img" aria-label="Vista minimizada del modelo"><rect width="900" height="650" fill="hsl(var(--background))" />{nodes.slice(0, 24).map(({ item }, index) => { const position = nodePosition(item, index); return <rect key={String(item.id) + '-mini'} x={position.x} y={position.y} width="190" height="68" rx="8" fill="hsl(var(--primary)/.35)" /> })}</svg></div>
        <div className="mx-6 mb-6 rounded-lg border border-border bg-card/80 p-4"><h2 className="text-xs font-semibold">Vista estructurada</h2><ul className="mt-2 grid grid-cols-2 gap-2 text-[11px]" aria-label="Componentes del modelo">{nodes.map(({ section, item }) => <li key={section + '-list-' + item.id}><button type="button" aria-pressed={selectedNodeKey === `${section}:${item.id}`} onClick={() => setSelectedNodeKey(`${section}:${item.id}`)} className={`w-full rounded border px-2 py-1 text-left ${selectedNodeKey === `${section}:${item.id}` ? 'border-primary bg-primary/10' : 'border-border'}`}><span className="text-muted-foreground">{section}:</span> {item.name ?? item.label ?? item.id}</button></li>)}</ul></div>
        {nodes.length === 0 && <div className="absolute inset-0 flex items-center justify-center"><div className="max-w-sm text-center"><GitBranch className="mx-auto h-10 w-10 text-muted-foreground/30" /><p className="mt-3 text-sm font-medium">Canvas listo para tu modelo</p><p className="mt-1 text-xs text-muted-foreground">Añade componentes desde la paleta o empieza desde una plantilla sectorial.</p></div></div>}
      </main>
      <aside className="overflow-y-auto border-l border-border bg-card/20 p-4" aria-label="Propiedades y validación">
        {selectedNode && <Card className="mb-3 border-primary/30 bg-primary/5"><CardHeader className="pb-2"><CardTitle className="text-xs">Propiedades del componente</CardTitle></CardHeader><CardContent className="space-y-2 text-xs"><p className="text-[10px] text-muted-foreground">{selectedNode.section} · {selectedNode.item.id}</p><label className="block"><span className="mb-1 block text-muted-foreground">Nombre</span><input value={String(selectedNode.item.name ?? selectedNode.item.label ?? '')} onChange={(event) => updateSelectedNode('name', event.target.value)} className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs" /></label><label className="block"><span className="mb-1 block text-muted-foreground">Unidad</span><input value={String(selectedNode.item.unit ?? '')} onChange={(event) => updateSelectedNode('unit', event.target.value)} placeholder="Bs, kg, hour…" className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs" /></label>{['variables', 'parameters', 'stocks', 'costs', 'revenues'].includes(selectedNode.section) && <label className="block"><span className="mb-1 block text-muted-foreground">Valor inicial</span><input type="number" value={selectedNode.item.value ?? selectedNode.item.initial ?? ''} onChange={(event) => updateSelectedNode('value', event.target.value)} className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs" /></label>}{['equations', 'costs', 'revenues', 'flows'].includes(selectedNode.section) && <label className="block"><span className="mb-1 block text-muted-foreground">Fórmula segura</span><input value={String(selectedNode.item.expression ?? '')} onChange={(event) => updateSelectedNode('expression', event.target.value)} placeholder="precio * demanda" className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs" /></label>}{selectedNode.section === 'resources' && <label className="block"><span className="mb-1 block text-muted-foreground">Capacidad</span><input type="number" value={selectedNode.item.capacity ?? ''} onChange={(event) => updateSelectedNode('capacity', event.target.value)} className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs" /></label>}<label className="block"><span className="mb-1 block text-muted-foreground">Procedencia</span><select value={String(selectedNode.item.provenance ?? 'USER_ENTERED')} onChange={(event) => updateSelectedNode('provenance', event.target.value)} className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs"><option value="USER_ENTERED">Ingresado por usuario</option><option value="IMPORTED">Importado</option><option value="ESTIMATED">Estimado</option><option value="AI_SUGGESTED">Sugerido por IA</option></select></label><div className="border-t border-border pt-2"><p className="mb-1 text-[10px] font-medium">Agregar relación causal</p><select aria-label="Destino causal" value={causalTarget} onChange={(event) => setCausalTarget(event.target.value)} className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs"><option value="">Selecciona destino</option>{nodes.filter(({ item }) => item.id && item.id !== selectedNode.item.id && !causalLinks.some((link) => link.source_id === selectedNode.item.id && link.target_id === item.id)).map(({ item, section }) => <option key={section + item.id} value={item.id}>{item.name ?? item.id}</option>)}</select><div className="mt-1 flex gap-1"><select aria-label="Polaridad causal" value={causalPolarity} onChange={(event) => setCausalPolarity(event.target.value as 'positive' | 'negative')} className="min-w-0 flex-1 rounded-md border border-input bg-background px-2 py-1.5 text-xs"><option value="positive">Positiva</option><option value="negative">Negativa</option></select><Button variant="outline" size="sm" onClick={addCausalLink} disabled={!causalTarget}>Conectar</Button></div></div></CardContent></Card>}
        <Card className="border-border bg-card/60"><CardHeader className="pb-2"><CardTitle className="text-xs">Propiedades del modelo</CardTitle></CardHeader><CardContent className="space-y-3 text-xs"><label className="block"><span className="mb-1 block text-muted-foreground">Nombre</span><input value={name} onChange={(event) => setName(event.target.value)} className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs" /></label><div><span className="text-muted-foreground">Schema</span><span className="ml-2">{version?.schema_version ?? '1.0'}</span></div><div><span className="text-muted-foreground">Hash</span><code className="mt-1 block truncate text-[10px] text-primary">{version?.content_hash ?? '—'}</code></div>
          <label className="block"><span className="mb-1 block text-muted-foreground">Escenario</span><select value={selectedScenario} onChange={(event) => setSelectedScenario(event.target.value)} className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs"><option value="">BASE</option>{scenarios.map((scenario) => <option key={scenario.id} value={scenario.id}>{scenario.name}</option>)}</select></label>
          <label className="block text-[11px] text-muted-foreground">Engine<select aria-label="Engine de simulación" value={engine} onChange={(event) => setEngine(event.target.value as typeof engine)} className="mt-1 w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs"><option value="monte_carlo">Monte Carlo</option><option value="system_dynamics">System dynamics</option><option value="discrete_event">Discrete event</option></select></label><Button size="sm" className="w-full gap-1.5" onClick={runModel} disabled={running || !version}>{running ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <GitBranch className="h-3.5 w-3.5" />} Ejecutar escenario</Button>
          {Object.entries(results).length > 0 && <div className="rounded-md bg-primary/10 p-2 text-[11px]"><p className="font-medium">Comparación reproducible · seed 42</p>{Object.entries(results).map(([scenarioKey, summary]) => <div key={scenarioKey} className="mt-2 border-t border-border/60 pt-2"><p className="font-medium">{scenarioKey === 'base' ? 'BASE' : scenarios.find((scenario) => scenario.id === scenarioKey)?.name ?? 'CUSTOM'}</p><p className="mt-1 text-muted-foreground">Media: <strong className="text-foreground">{summary.mean?.toFixed(2)}</strong> · P5: {summary.p5?.toFixed(2)} · P95: {summary.p95?.toFixed(2)}</p></div>)}</div>}
        </CardContent></Card>
        <Card className="mt-3 border-border bg-card/60"><CardHeader className="pb-2"><CardTitle className="text-xs">Nuevo escenario</CardTitle></CardHeader><CardContent className="space-y-2"><input aria-label="Nombre del escenario" value={scenarioName} onChange={(event) => setScenarioName(event.target.value)} placeholder="Ej. Costos altos" className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs" /><label className="block text-[11px] text-muted-foreground">Variable<label className="sr-only" htmlFor="scenario-variable">Variable del escenario</label><input id="scenario-variable" value={scenarioVariable} onChange={(event) => setScenarioVariable(event.target.value)} className="mt-1 w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs" /></label><label className="block text-[11px] text-muted-foreground">Cambio aditivo en la unidad declarada<label className="sr-only" htmlFor="scenario-change">Cambio del escenario</label><input id="scenario-change" type="number" value={scenarioChange} onChange={(event) => setScenarioChange(event.target.value)} className="mt-1 w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs" /></label><Button variant="outline" size="sm" className="w-full" onClick={createScenario} disabled={!scenarioName.trim() || !scenarioVariable.trim()}>Guardar escenario</Button></CardContent></Card>
        <Card className="mt-3 border-border bg-card/60"><CardHeader className="pb-2"><CardTitle className="text-xs">Convertir en plantilla</CardTitle></CardHeader><CardContent className="space-y-2"><p className="text-[10px] leading-relaxed text-muted-foreground">Guarda la estructura validada como punto de partida reutilizable. No publica datos privados como verdad compartida.</p><input aria-label="Nombre de la plantilla" value={templateName} onChange={(event) => setTemplateName(event.target.value)} placeholder="Ej. Taller de reparación" className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs" /><Button variant="outline" size="sm" className="w-full" onClick={saveAsTemplate} disabled={savingTemplate || !templateName.trim()}>{savingTemplate ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Guardar plantilla propia'}</Button></CardContent></Card>
        <Card className="mt-3 border-border bg-card/60"><CardHeader className="pb-2"><CardTitle className="flex items-center gap-2 text-xs"><TrendingUp className="h-3.5 w-3.5 text-primary" /> Sensibilidad</CardTitle></CardHeader><CardContent className="space-y-2"><p className="text-[10px] leading-relaxed text-muted-foreground">Prueba un cambio aditivo explícito con la misma semilla; no supone elasticidades desconocidas.</p><input aria-label="Variable de sensibilidad" value={sensitivityVariable} onChange={(event) => setSensitivityVariable(event.target.value)} className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs" /><input aria-label="Cambio de sensibilidad" type="number" value={sensitivityChange} onChange={(event) => setSensitivityChange(event.target.value)} className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs" /><label className="block text-[11px] text-muted-foreground">Métrica<select aria-label="Métrica de sensibilidad" value={sensitivityMetric} onChange={(event) => setSensitivityMetric(event.target.value as typeof sensitivityMetric)} className="mt-1 w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs"><option value="profit">Resultado / profit</option><option value="completed" disabled={engine !== 'discrete_event'}>Trabajo completado</option><option value="queue_end" disabled={engine !== 'discrete_event'}>Cola final</option><option value="utilization" disabled={engine !== 'discrete_event'}>Utilización</option></select></label><p className="text-[10px] text-muted-foreground">Engine: {engine === 'discrete_event' ? 'eventos discretos' : engine === 'system_dynamics' ? 'dinámica de sistemas' : 'Monte Carlo'} · seed 42</p><Button variant="outline" size="sm" className="w-full gap-1.5" onClick={runSensitivity} disabled={sensitivityRunning || !version}>{sensitivityRunning ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <TrendingUp className="h-3.5 w-3.5" />} Ejecutar sensibilidad</Button>{sensitivity.map((factor) => <p key={factor.variable} className="text-[11px] text-muted-foreground">{factor.variable}: efecto <strong className={factor.effect >= 0 ? 'text-emerald-400' : 'text-rose-300'}>{factor.effect.toFixed(2)}</strong> por cambio {factor.change}</p>)}</CardContent></Card>
        <Card className="mt-3 border-border bg-card/60"><CardHeader className="pb-2"><CardTitle className="text-xs">Vistas derivadas del modelo</CardTitle></CardHeader><CardContent className="space-y-2">{Object.entries(diagrams).map(([key, diagram]) => <div key={key} className="rounded border border-border px-2 py-1.5"><div className="flex items-center justify-between text-[11px]"><span className="font-medium">{diagram.title}</span><span className="text-muted-foreground">{diagram.nodes.length} nodos · {diagram.edges.length} relaciones</span></div><ul className="mt-1 space-y-0.5 text-[10px] text-muted-foreground" aria-label={diagram.title}>{diagram.edges.slice(0, 3).map((edge, index) => <li key={edge.source + edge.target + index}>{edge.source} → {edge.target} · {edge.relation}</li>)}</ul></div>)}{Object.keys(diagrams).length === 0 && <p className="text-[11px] text-muted-foreground">Aún no hay relaciones derivables.</p>}<div className="border-t border-border pt-2"><p className="mb-1 text-[10px] font-medium">Relaciones causales editables</p>{causalLinks.length ? causalLinks.map((link) => <div key={link.id} className="flex items-center justify-between gap-2 text-[10px]"><span>{String(link.source_id)} → {String(link.target_id)} · {link.polarity === 'negative' ? '−' : '+'}</span><button type="button" aria-label="Eliminar relación causal" onClick={() => removeCausalLink(String(link.id))} className="text-rose-300 hover:text-rose-200">Eliminar</button></div>) : <p className="text-[10px] text-muted-foreground">Selecciona un nodo para conectar una relación.</p>}</div></CardContent></Card>
        <Card className="mt-3 border-border bg-card/60"><CardHeader className="pb-2"><CardTitle className="flex items-center gap-2 text-xs"><ShieldCheck className="h-3.5 w-3.5 text-primary" /> Validación y preparación</CardTitle></CardHeader><CardContent>{validation ? <div className="space-y-2 text-xs">{validation.valid ? <p className="flex items-center gap-1.5 text-emerald-400"><CheckCircle2 className="h-3.5 w-3.5" /> Modelo válido</p> : <p className="flex items-center gap-1.5 text-rose-400"><AlertTriangle className="h-3.5 w-3.5" /> Hay errores que resolver</p>}<p>Completitud: <strong>{validation.readiness.score}%</strong></p>{validation.readiness.missing.length > 0 && <div className="rounded border border-amber-500/30 bg-amber-500/10 p-2"><p className="font-medium text-amber-200">Faltan entradas para una simulación más completa</p><ul className="mt-1 space-y-1 text-[10px] text-amber-100/80">{validation.readiness.missing.map((dimension) => <li key={dimension}><span className="font-medium">{dimension}:</span> {validation.readiness.actions?.[dimension] ?? 'Añade y confirma esta dimensión del modelo.'}</li>)}</ul></div>}{validation.errors.map((error) => <p key={error.path + error.message} className="text-[10px] text-rose-300">{error.path}: {error.message}</p>)}{validation.warnings.map((warning, index) => <p key={index} className="text-[10px] text-amber-300">{warning.message}</p>)}</div> : <ReadinessSummary readiness={version?.validation?.readiness} />}</CardContent></Card>
      </aside>
    </div>
  </div>
}
