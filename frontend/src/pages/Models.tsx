import { useEffect, useState } from 'react'
import { Boxes, ChevronRight, Loader2, Network, Plus, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { createBusinessModel, getBusinessModels, getModelTemplates, getOwnedBusinesses } from '@/lib/api'
import type { BusinessModel, ModelTemplate } from '@/types'

export default function Models() {
  const [models, setModels] = useState<BusinessModel[]>([])
  const [templates, setTemplates] = useState<ModelTemplate[]>([])
  const [businesses, setBusinesses] = useState<{ id: number; name: string; sector: string }[]>([])
  const [selectedBusiness, setSelectedBusiness] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState('')
  const [creating, setCreating] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getBusinessModels(), getModelTemplates(), getOwnedBusinesses()])
      .then(([modelResponse, templateResponse, businessResponse]) => { setModels(modelResponse.models); setTemplates(templateResponse.templates); setBusinesses(businessResponse.businesses); setSelectedBusiness(String(businessResponse.businesses[0]?.id ?? '')); setSelectedTemplate(templateResponse.templates[0]?.slug ?? '') })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false))
  }, [])

  async function createFromTemplate() {
    const business = businesses.find((item) => String(item.id) === selectedBusiness)
    const template = templates.find((item) => item.slug === selectedTemplate)
    if (!business || !template) return
    setCreating(true)
    try {
      const response = await createBusinessModel({ business_id: business.id, name: `${template.name} · modelo`, sector: template.sector, spec: template.spec })
      setModels((current) => [...current, { ...response.model, business_name: business.name, current_version: response.model.version.version, readiness: response.model.version.validation?.readiness }])
      setError('')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo crear el modelo.')
    } finally { setCreating(false) }
  }

  return <div className="flex h-full flex-col overflow-hidden">
    <header className="flex shrink-0 items-center justify-between border-b border-border px-6 py-4">
      <div><h1 className="text-base font-semibold">Modelos de negocio</h1><p className="mt-0.5 text-xs text-muted-foreground">Una definición versionada para procesos, recursos, demanda y finanzas.</p></div>
      <Button size="sm" className="gap-1.5" asChild><Link to="/onboarding"><Sparkles className="h-3.5 w-3.5" /> Crear desde plantilla</Link></Button>
    </header>
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {error && <div role="alert" className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-300">{error}</div>}
      <Card className="border-primary/30 bg-primary/5"><CardContent className="flex flex-wrap items-end gap-3 p-4"><div className="min-w-[220px] flex-1"><label htmlFor="model-business" className="mb-1 block text-[11px] text-muted-foreground">Empresa</label><select id="model-business" value={selectedBusiness} onChange={(event) => setSelectedBusiness(event.target.value)} className="w-full rounded-md border border-input bg-background px-2 py-2 text-xs"><option value="">Selecciona una empresa</option>{businesses.map((business) => <option key={business.id} value={business.id}>{business.name}</option>)}</select></div><div className="min-w-[240px] flex-1"><label htmlFor="model-template" className="mb-1 block text-[11px] text-muted-foreground">Punto de partida</label><select id="model-template" value={selectedTemplate} onChange={(event) => setSelectedTemplate(event.target.value)} className="w-full rounded-md border border-input bg-background px-2 py-2 text-xs"><option value="">Selecciona una plantilla</option>{templates.map((template) => <option key={template.slug} value={template.slug}>{template.name}</option>)}</select></div><Button size="sm" className="gap-1.5" onClick={createFromTemplate} disabled={creating || !selectedBusiness || !selectedTemplate}>{creating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />} Crear modelo editable</Button></CardContent></Card>
      {loading ? <div role="status" className="flex justify-center py-20"><Loader2 className="h-7 w-7 animate-spin text-muted-foreground" /></div> : <>
        <section aria-labelledby="models-title">
          <div className="mb-3 flex items-center gap-2"><Network className="h-4 w-4 text-primary" /><h2 id="models-title" className="text-sm font-medium">Tus modelos</h2></div>
          {models.length === 0 ? <Card><CardContent className="flex flex-col items-center gap-3 py-12 text-center"><Boxes className="h-10 w-10 text-muted-foreground/40" /><p className="text-sm font-medium">Todavía no hay modelos versionados.</p><p className="max-w-md text-xs text-muted-foreground">Empieza desde una plantilla y ajusta la estructura a tu negocio; los datos sintéticos están etiquetados.</p><Button size="sm" asChild><Link to="/onboarding">Elegir plantilla</Link></Button></CardContent></Card> : <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{models.map((model) => <Card key={model.id} className="transition-colors hover:border-primary/50"><CardHeader className="pb-2"><div className="flex items-start justify-between gap-2"><CardTitle className="text-sm">{model.name}</CardTitle><Badge variant={model.status === 'validated' ? 'success' : 'secondary'}>{model.status}</Badge></div><p className="text-xs text-muted-foreground">{model.business_name} · {model.sector}</p></CardHeader><CardContent><div className="mb-3 flex items-center justify-between text-xs"><span className="text-muted-foreground">Completitud del modelo</span><span className="font-medium text-foreground">{model.readiness?.score ?? 0}%</span></div><div className="h-1.5 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-primary" style={{ width: `${model.readiness?.score ?? 0}%` }} /></div><Button variant="ghost" size="sm" className="mt-3 w-full justify-between text-xs" asChild><Link to={`/models/${model.id}`}>Abrir constructor <ChevronRight className="h-3.5 w-3.5" /></Link></Button></CardContent></Card>)}</div>}
        </section>
        <section aria-labelledby="templates-title"><div className="mb-3 flex items-center gap-2"><Sparkles className="h-4 w-4 text-primary" /><h2 id="templates-title" className="text-sm font-medium">Plantillas disponibles</h2><span className="text-xs text-muted-foreground">{templates.length} sectores iniciales</span></div><div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">{templates.map((template) => <div key={template.slug} className="rounded-lg border border-border bg-card/40 p-3"><p className="text-xs font-medium">{template.name}</p><p className="mt-1 text-[11px] text-muted-foreground">{template.description}</p><Badge variant="outline" className="mt-2 text-[10px]">{String(template.provenance?.kind ?? 'USER_ENTERED')}</Badge></div>)}</div></section>
      </>}
    </div>
  </div>
}
