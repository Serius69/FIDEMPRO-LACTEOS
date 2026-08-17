import { useEffect, useMemo, useState } from 'react'
import { CheckCircle2, Loader2, Plus, Save, Trash2, Workflow } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { createModelVersion, getBusinessModel, getBusinessModels } from '@/lib/api'
import type { BusinessModel, ModelVersion } from '@/types'

type Resource = { id: string; name?: string; capacity?: number }
type Step = { id: string; name?: string; resource_id?: string; cycle_time?: number; failure_probability?: number; rework_probability?: number; queue_capacity?: number }
type Process = { id: string; name?: string; steps: Step[] }
type ServiceTask = { id: string; name?: string; duration?: number; role_id?: string; consumables?: string[] }
type Service = { id: string; name?: string; tasks: ServiceTask[] }
type Spec = Record<string, unknown> & { resources?: Resource[]; processes?: Process[]; services?: Service[] }

export default function ProcessBuilder() {
  const [models, setModels] = useState<BusinessModel[]>([])
  const [modelId, setModelId] = useState('')
  const [version, setVersion] = useState<ModelVersion | null>(null)
  const [spec, setSpec] = useState<Spec>({})
  const [processIndex, setProcessIndex] = useState(0)
  const [serviceIndex, setServiceIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getBusinessModels().then((response) => { setModels(response.models); if (response.models[0]) setModelId(response.models[0].id) }).catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!modelId) return
    setLoading(true)
    getBusinessModel(modelId).then((model) => {
      const current = model.current_version as ModelVersion | undefined
      setVersion(current ?? null); setSpec((current?.spec ?? {}) as Spec); setProcessIndex(0); setServiceIndex(0); setSaved(false)
    }).catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false))
  }, [modelId])

  const resources = useMemo(() => spec.resources ?? [], [spec.resources])
  const processes = useMemo(() => spec.processes ?? [], [spec.processes])
  const services = useMemo(() => spec.services ?? [], [spec.services])
  const process = processes[processIndex]
  const service = services[serviceIndex]

  function updateSpec(patch: Partial<Spec>) { setSpec((current) => ({ ...current, ...patch })); setSaved(false) }
  function addProcess() { const next = [...processes, { id: 'process-' + Date.now(), name: 'Nuevo proceso', steps: [] }]; updateSpec({ processes: next }); setProcessIndex(next.length - 1) }
  function addStep() { if (!process) return; updateSpec({ processes: processes.map((item, index) => index === processIndex ? { ...item, steps: [...item.steps, { id: 'step-' + Date.now(), name: 'Nueva tarea', cycle_time: 1, failure_probability: 0, rework_probability: 0 }] } : item) }) }
  function updateStep(index: number, patch: Partial<Step>) { if (!process) return; updateSpec({ processes: processes.map((item, itemIndex) => itemIndex === processIndex ? { ...item, steps: item.steps.map((step, stepIndex) => stepIndex === index ? { ...step, ...patch } : step) } : item) }) }
  function removeStep(index: number) { if (!process) return; updateSpec({ processes: processes.map((item, itemIndex) => itemIndex === processIndex ? { ...item, steps: item.steps.filter((_, stepIndex) => stepIndex !== index) } : item) }) }
  function addService() { const next = [...services, { id: 'service-' + Date.now(), name: 'Nuevo servicio', tasks: [] }]; updateSpec({ services: next }); setServiceIndex(next.length - 1) }
  function addTask() { if (!service) return; updateSpec({ services: services.map((item, index) => index === serviceIndex ? { ...item, tasks: [...item.tasks, { id: 'task-' + Date.now(), name: 'Nueva tarea', duration: 1 }] } : item) }) }
  function updateTask(index: number, patch: Partial<ServiceTask>) { if (!service) return; updateSpec({ services: services.map((item, itemIndex) => itemIndex === serviceIndex ? { ...item, tasks: item.tasks.map((task, taskIndex) => taskIndex === index ? { ...task, ...patch } : task) } : item) }) }
  function removeTask(index: number) { if (!service) return; updateSpec({ services: services.map((item, itemIndex) => itemIndex === serviceIndex ? { ...item, tasks: item.tasks.filter((_, taskIndex) => taskIndex !== index) } : item) }) }
  async function save() { if (!modelId) return; setSaving(true); setError(''); try { const response = await createModelVersion(modelId, spec); setVersion(response.version); setSaved(true) } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo guardar el proceso.') } finally { setSaving(false) } }

  if (loading) return <div role="status" className="flex h-full items-center justify-center"><Loader2 className="h-7 w-7 animate-spin text-muted-foreground" /></div>
  return <div className="flex h-full flex-col overflow-hidden">
    <header className="flex shrink-0 items-center justify-between border-b border-border px-6 py-4"><div className="flex items-center gap-3"><Workflow className="h-5 w-5 text-primary" /><div><h1 className="text-base font-semibold">Procesos y servicios</h1><p className="mt-0.5 text-xs text-muted-foreground">Pasos, recursos, capacidad, fallos y tareas de prestación.</p></div></div><Button onClick={save} disabled={saving || !version} className="gap-1.5">{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : saved ? <CheckCircle2 className="h-4 w-4" /> : <Save className="h-4 w-4" />} {saved ? 'Versión guardada' : 'Guardar versión'}</Button></header>
    <div className="flex flex-1 flex-col gap-5 overflow-y-auto p-6">
      {error && <div role="alert" className="rounded-md border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">{error}</div>}
      <Card><CardContent className="flex flex-wrap items-end gap-4 p-4"><label className="min-w-[280px] flex-1 text-xs"><span className="mb-1 block text-muted-foreground">Modelo / versión</span><select value={modelId} onChange={(event) => setModelId(event.target.value)} className="w-full rounded-md border border-input bg-background px-3 py-2">{models.map((model) => <option key={model.id} value={model.id}>{model.name} · v{typeof model.current_version === 'number' ? model.current_version : version?.version ?? '—'}</option>)}</select></label><div className="text-xs text-muted-foreground">Recursos configurados: <strong>{resources.length}</strong></div></CardContent></Card>
      <div className="grid gap-5 xl:grid-cols-2">
        <Card><CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle className="text-sm">Flujo de proceso</CardTitle><Button size="sm" variant="outline" onClick={addProcess} className="gap-1"><Plus className="h-3.5 w-3.5" /> Proceso</Button></CardHeader><CardContent>{processes.length === 0 ? <p className="py-8 text-center text-xs text-muted-foreground">Crea un proceso para comenzar.</p> : <><select aria-label="Proceso activo" value={processIndex} onChange={(event) => setProcessIndex(Number(event.target.value))} className="mb-3 w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs">{processes.map((item, index) => <option key={item.id} value={index}>{item.name ?? item.id}</option>)}</select><div className="mb-3 flex justify-end"><Button size="sm" variant="outline" onClick={addStep} className="gap-1"><Plus className="h-3.5 w-3.5" /> Paso</Button></div><div className="space-y-2">{process?.steps.map((step, index) => <div key={step.id} className="grid grid-cols-[1fr_80px_80px_80px_32px] items-center gap-2 rounded-md border border-border p-2 text-xs"><input aria-label="Nombre del paso" value={step.name ?? ''} onChange={(event) => updateStep(index, { name: event.target.value })} className="rounded border border-input bg-background px-2 py-1.5" /><input aria-label="Tiempo de ciclo" type="number" min="0" step="0.01" value={step.cycle_time ?? 0} onChange={(event) => updateStep(index, { cycle_time: Number(event.target.value) })} className="rounded border border-input bg-background px-2 py-1.5" placeholder="min" /><select aria-label="Recurso" value={step.resource_id ?? ''} onChange={(event) => updateStep(index, { resource_id: event.target.value })} className="rounded border border-input bg-background px-1 py-1.5"><option value="">Recurso</option>{resources.map((resource) => <option key={resource.id} value={resource.id}>{resource.name ?? resource.id}</option>)}</select><input aria-label="Probabilidad de fallo" type="number" min="0" max="1" step="0.01" value={step.failure_probability ?? 0} onChange={(event) => updateStep(index, { failure_probability: Number(event.target.value) })} className="rounded border border-input bg-background px-2 py-1.5" placeholder="fallo" /><Button variant="ghost" size="icon" aria-label="Eliminar paso" onClick={() => removeStep(index)}><Trash2 className="h-4 w-4 text-rose-400" /></Button></div>)}</div></>}</CardContent></Card>
        <Card><CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle className="text-sm">Service blueprint</CardTitle><Button size="sm" variant="outline" onClick={addService} className="gap-1"><Plus className="h-3.5 w-3.5" /> Servicio</Button></CardHeader><CardContent>{services.length === 0 ? <p className="py-8 text-center text-xs text-muted-foreground">Crea un servicio para modelar tareas y personal.</p> : <><select aria-label="Servicio activo" value={serviceIndex} onChange={(event) => setServiceIndex(Number(event.target.value))} className="mb-3 w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs">{services.map((item, index) => <option key={item.id} value={index}>{item.name ?? item.id}</option>)}</select><div className="mb-3 flex justify-end"><Button size="sm" variant="outline" onClick={addTask} className="gap-1"><Plus className="h-3.5 w-3.5" /> Tarea</Button></div><div className="space-y-2">{service?.tasks.map((task, index) => <div key={task.id} className="grid grid-cols-[1fr_100px_1fr_32px] items-center gap-2 rounded-md border border-border p-2 text-xs"><input aria-label="Nombre de tarea" value={task.name ?? ''} onChange={(event) => updateTask(index, { name: event.target.value })} className="rounded border border-input bg-background px-2 py-1.5" /><input aria-label="Duración de tarea" type="number" min="0.01" step="0.01" value={task.duration ?? 0} onChange={(event) => updateTask(index, { duration: Number(event.target.value) })} className="rounded border border-input bg-background px-2 py-1.5" placeholder="minutos" /><select aria-label="Rol de tarea" value={task.role_id ?? ''} onChange={(event) => updateTask(index, { role_id: event.target.value })} className="rounded border border-input bg-background px-1 py-1.5"><option value="">Rol / recurso</option>{resources.map((resource) => <option key={resource.id} value={resource.id}>{resource.name ?? resource.id}</option>)}</select><Button variant="ghost" size="icon" aria-label="Eliminar tarea" onClick={() => removeTask(index)}><Trash2 className="h-4 w-4 text-rose-400" /></Button></div>)}</div></>}</CardContent></Card>
      </div>
    </div>
  </div>
}
