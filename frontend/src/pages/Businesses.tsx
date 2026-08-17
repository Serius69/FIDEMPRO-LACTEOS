import { FormEvent, useEffect, useState } from 'react'
import { Building2, Loader2, Plus } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { createBusiness, getOwnedBusinesses } from '@/lib/api'

const SECTORS = [
  ['retail', 'Retail / comercio'], ['grocery', 'Tienda de barrio'], ['restaurant', 'Restaurante'],
  ['bakery', 'Panadería'], ['dairy', 'Lácteos'], ['manufacturing', 'Manufactura'],
  ['textiles', 'Textiles'], ['repair', 'Reparación / taller'], ['professional-services', 'Servicios profesionales'],
  ['technology-services', 'Servicios tecnológicos'], ['transport', 'Transporte'], ['construction', 'Construcción'],
  ['agriculture', 'Agricultura'], ['health', 'Salud'], ['education', 'Educación'], ['generic', 'Otro sector'],
] as const

type OwnedBusiness = { id: number; name: string; sector: string }

export default function Businesses() {
  const [businesses, setBusinesses] = useState<OwnedBusiness[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [name, setName] = useState('')
  const [location, setLocation] = useState('Cochabamba')
  const [sector, setSector] = useState('retail')

  function reload() {
    setLoading(true)
    getOwnedBusinesses().then((response) => setBusinesses(response.businesses)).catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false))
  }

  useEffect(() => { reload() }, [])

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!name.trim() || !location.trim()) return
    setSaving(true)
    setError('')
    try {
      const response = await createBusiness({ name: name.trim(), location: location.trim(), sector })
      setBusinesses((current) => [...current, response.business])
      setName('')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo crear la empresa.') } finally { setSaving(false) }
  }

  return <div className="flex h-full flex-col overflow-hidden">
    <header className="flex shrink-0 items-center justify-between border-b border-border px-6 py-4">
      <div><h1 className="text-base font-semibold">Empresas</h1><p className="mt-0.5 text-xs text-muted-foreground">Cada empresa tiene su propio modelo, datos y simulaciones.</p></div>
      <Badge variant="outline">{businesses.length} activa(s)</Badge>
    </header>
    <div className="flex-1 overflow-y-auto space-y-5 p-6">
      {error && <div role="alert" className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-300">{error}</div>}
      <Card className="border-primary/30 bg-primary/5"><CardHeader className="pb-2"><CardTitle className="flex items-center gap-2 text-sm"><Plus className="h-4 w-4 text-primary" /> Crear empresa</CardTitle></CardHeader><CardContent><form onSubmit={submit} className="grid gap-3 md:grid-cols-[1.4fr_1fr_1fr_auto] md:items-end"><label className="text-xs"><span className="mb-1 block text-muted-foreground">Nombre</span><input required minLength={3} value={name} onChange={(event) => setName(event.target.value)} placeholder="Ej. Panadería Central" className="w-full rounded-md border border-input bg-background px-2 py-2" /></label><label className="text-xs"><span className="mb-1 block text-muted-foreground">Ubicación</span><input required value={location} onChange={(event) => setLocation(event.target.value)} className="w-full rounded-md border border-input bg-background px-2 py-2" /></label><label className="text-xs"><span className="mb-1 block text-muted-foreground">Sector inicial</span><select value={sector} onChange={(event) => setSector(event.target.value)} className="w-full rounded-md border border-input bg-background px-2 py-2">{SECTORS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><Button type="submit" disabled={saving || !name.trim()}>{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Crear'}</Button></form><p className="mt-3 text-[11px] text-muted-foreground">El sector solo clasifica la empresa y sugiere plantillas; la definición completa se configura después.</p></CardContent></Card>
      {loading ? <div role="status" className="flex justify-center py-20"><Loader2 className="h-7 w-7 animate-spin text-muted-foreground" /></div> : businesses.length ? <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{businesses.map((business) => <Card key={business.id}><CardHeader className="pb-2"><div className="flex items-center gap-2"><div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/15 text-primary"><Building2 className="h-4 w-4" /></div><CardTitle className="text-sm">{business.name}</CardTitle></div></CardHeader><CardContent><p className="text-xs text-muted-foreground">Sector: <span className="text-foreground">{SECTORS.find(([value]) => value === business.sector)?.[1] ?? business.sector}</span></p><a className="mt-3 inline-block text-xs text-primary hover:underline" href={`/models?business_id=${business.id}`}>Configurar modelo →</a></CardContent></Card>)}</div> : <Card><CardContent className="py-14 text-center"><Building2 className="mx-auto h-10 w-10 text-muted-foreground/30" /><p className="mt-3 text-sm font-medium">Crea tu primera empresa para comenzar.</p></CardContent></Card>}
    </div>
  </div>
}
