import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { PlayCircle, Loader2, AlertTriangle, TrendingUp, DollarSign, BarChart2 } from 'lucide-react'
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  BarChart, Bar, Cell,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { runSimulation } from '@/lib/api'
import { DISTRIBUTIONS, fmtNum, fmtPct } from '@/lib/utils'
import type { SimulationRequest, SimulationResult } from '@/types'

const DEFAULTS: SimulationRequest = {
  demand_mean: 1000, demand_std: 150, unit_price: 25, unit_cost: 12,
  fixed_costs: 5000, distribution_type: 'normal', n_iterations: 10000,
  time_periods: 30, confidence_level: 0.95, random_seed: 42,
}

export default function Simulate() {
  const { register, handleSubmit, setValue, watch } = useForm<SimulationRequest>({ defaultValues: DEFAULTS })
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const distType = watch('distribution_type')

  async function onSubmit(data: SimulationRequest) {
    setLoading(true); setError(''); setResult(null)
    try { setResult(await runSimulation(data)) }
    catch (e) { setError(e instanceof Error ? e.message : 'Error') }
    finally { setLoading(false) }
  }

  // `time_series` es una lista de puntos por período (no columnas paralelas).
  const timeSeriesData = result?.time_series.map((p) => ({
    period: `P${p.period}`,
    demand: p.demand_mean,
    revenue: p.revenue_mean,
    profit: p.profit_mean,
  })) ?? []

  // `scenarios` es una lista de cinco escenarios nombrados, ordenados por
  // demanda creciente. El servidor no publica una probabilidad por escenario
  // —son percentiles de la distribución, no una masa de probabilidad— así que
  // se muestra el percentil, que es lo que realmente son.
  const scenarioData = result?.scenarios.map((s) => ({
    name: s.name,
    percentile: s.demand_percentile,
    demand: s.demand_value,
    revenue: s.revenue,
    profit: s.gross_profit,
    margin: s.profit_margin_pct,
  })) ?? []

  const SCENARIO_COLORS = ['#f87171', '#fbbf24', '#60a5fa', '#4ade80', '#34d399']

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <header className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <PlayCircle className="h-5 w-5 text-primary" />
        <div>
          <h1 className="text-base font-semibold">Simulación Monte Carlo</h1>
          <p className="text-xs text-muted-foreground mt-0.5">Análisis probabilístico de riesgo financiero · {(DEFAULTS.n_iterations).toLocaleString()} escenarios</p>
        </div>
      </header>

      <div className="flex flex-1 flex-col overflow-hidden md:flex-row">
        {/* Config panel */}
        <aside className="w-full shrink-0 border-b border-border overflow-y-auto md:w-72 md:border-b-0 md:border-r">
          <form onSubmit={handleSubmit(onSubmit)} className="p-4 space-y-4">
            <Section label="Demanda">
              <Field label="Media de demanda (unidades)"><Input type="number" step="1" {...register('demand_mean', { valueAsNumber: true })} /></Field>
              <Field label="Desviación estándar"><Input type="number" step="1" {...register('demand_std', { valueAsNumber: true })} /></Field>
              <Field label="Distribución">
                <Select value={distType} onValueChange={(v) => setValue('distribution_type', v as SimulationRequest['distribution_type'])}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {DISTRIBUTIONS.map((d) => <SelectItem key={d.value} value={d.value}>{d.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </Field>
            </Section>

            <Section label="Financiero">
              <Field label="Precio unitario (BOB)"><Input type="number" step="0.01" {...register('unit_price', { valueAsNumber: true })} /></Field>
              <Field label="Costo unitario (BOB)"><Input type="number" step="0.01" {...register('unit_cost', { valueAsNumber: true })} /></Field>
              <Field label="Costos fijos (BOB)"><Input type="number" step="100" {...register('fixed_costs', { valueAsNumber: true })} /></Field>
            </Section>

            <Section label="Parámetros">
              <Field label="Iteraciones Monte Carlo">
                <Select value={String(watch('n_iterations'))} onValueChange={(v) => setValue('n_iterations', Number(v))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {[1000, 5000, 10000, 50000, 100000].map((n) => <SelectItem key={n} value={String(n)}>{n.toLocaleString()}</SelectItem>)}
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Períodos de tiempo"><Input type="number" min={5} max={365} {...register('time_periods', { valueAsNumber: true })} /></Field>
              <Field label="Nivel de confianza">
                <Select value={String(watch('confidence_level'))} onValueChange={(v) => setValue('confidence_level', Number(v))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {[0.80, 0.90, 0.95, 0.99].map((c) => <SelectItem key={c} value={String(c)}>{(c * 100).toFixed(0)}%</SelectItem>)}
                  </SelectContent>
                </Select>
              </Field>
            </Section>

            <Button type="submit" className="w-full gap-2" disabled={loading}>
              {loading ? <><Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> Simulando...</> : <><PlayCircle className="h-4 w-4" aria-hidden="true" /> Ejecutar Simulación</>}
            </Button>
          </form>
        </aside>

        {/* Results */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {error && <div role="alert" className="rounded-lg bg-destructive/10 border border-destructive/20 p-4 text-sm text-red-400">{error}</div>}

          {!result && !loading && (
            <div className="flex flex-col items-center gap-4 py-20 text-center">
              <div className="h-16 w-16 rounded-2xl bg-primary/10 flex items-center justify-center text-3xl">🎲</div>
              <div>
                <h2 className="text-lg font-semibold">Configura y ejecuta una simulación</h2>
                <p className="text-sm text-muted-foreground mt-1 max-w-sm">Ajusta los parámetros en el panel izquierdo y haz clic en "Ejecutar Simulación" para obtener el análisis probabilístico.</p>
              </div>
              <div className="grid grid-cols-3 gap-3 text-xs max-w-sm">
                {[['VaR', 'Value at Risk al 5%'], ['CVaR', 'Expected Shortfall'], ['Sharpe', 'Ratio riesgo/retorno']].map(([k, v]) => (
                  <div key={k} className="rounded-lg border border-border bg-card/50 p-3">
                    <p className="font-bold text-primary">{k}</p>
                    <p className="text-muted-foreground mt-0.5">{v}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result && (
            <>
              {/* Risk KPIs */}
              <div className="grid grid-cols-4 gap-4 animate-fade-in">
                <Card><CardContent className="p-4">
                  <div className="flex items-start justify-between"><p className="text-xs text-muted-foreground">Demanda media</p><BarChart2 className="h-4 w-4 text-primary" /></div>
                  <p className="text-2xl font-bold text-primary mt-2">{fmtNum(result.demand.mean, 0)}</p>
                  <p className="text-[11px] text-muted-foreground">± {fmtNum(result.demand.std, 0)}</p>
                </CardContent></Card>

                <Card><CardContent className="p-4">
                  <div className="flex items-start justify-between"><p className="text-xs text-muted-foreground">Beneficio típico (mediana)</p><DollarSign className="h-4 w-4 text-emerald-400" /></div>
                  <p className="text-2xl font-bold text-emerald-400 mt-2">Bs. {fmtNum(result.profit.median, 0)}</p>
                  <p className="text-[11px] text-muted-foreground">Media: Bs. {fmtNum(result.profit.mean, 0)} · ± {fmtNum(result.profit.std, 0)}</p>
                </CardContent></Card>

                <Card><CardContent className="p-4">
                  <div className="flex items-start justify-between"><p className="text-xs text-muted-foreground">VaR {fmtPct(result.risk.var_confidence_level)}</p><AlertTriangle className="h-4 w-4 text-amber-400" /></div>
                  <p className="text-2xl font-bold text-amber-400 mt-2">Bs. {fmtNum(result.profit.var_95, 0)}</p>
                  <p className="text-[11px] text-muted-foreground">Beneficio en el peor {fmtPct(1 - result.risk.var_confidence_level)} de escenarios</p>
                </CardContent></Card>

                <Card><CardContent className="p-4">
                  <div className="flex items-start justify-between"><p className="text-xs text-muted-foreground">Probabilidad de pérdida</p><TrendingUp className="h-4 w-4 text-muted-foreground" /></div>
                  {/* Sin semáforo: el servidor no publica una categoría de
                      riesgo y clasificar aquí sería inventar los umbrales. */}
                  <p className="text-2xl font-bold mt-2 text-foreground">{fmtPct(result.risk.probability_of_loss)}</p>
                  <p className="text-[11px] text-muted-foreground">Alcanza el punto de equilibrio: {fmtPct(result.risk.probability_breakeven)}</p>
                </CardContent></Card>
              </div>

              {/* Additional metrics */}
              <div className="grid grid-cols-3 gap-4">
                <Card><CardContent className="p-4">
                  <p className="text-xs text-muted-foreground">Ingresos esperados</p>
                  <p className="text-xl font-bold mt-1">Bs. {fmtNum(result.revenue.mean, 0)}</p>
                  <p className="text-[11px] text-muted-foreground mt-0.5">P5: Bs. {fmtNum(result.revenue.p5, 0)} · P95: Bs. {fmtNum(result.revenue.p95, 0)}</p>
                </CardContent></Card>
                <Card><CardContent className="p-4">
                  <p className="text-xs text-muted-foreground">Sharpe Ratio</p>
                  {/* El servidor manda `sharpe_ratio: null` y dice por qué en
                      `ratio_basis`. Presentarlo como N/A es el dato correcto. */}
                  <p className="text-xl font-bold mt-1">{fmtNum(result.profit.sharpe_ratio)}</p>
                  <p className="text-[11px] text-muted-foreground mt-0.5">
                    {result.profit.sharpe_ratio === null
                      ? 'No aplica: el beneficio monetario no es una serie de retornos periodizados'
                      : 'Retorno ajustado por riesgo'}
                  </p>
                </CardContent></Card>
                <Card><CardContent className="p-4">
                  <p className="text-xs text-muted-foreground">CVaR {fmtPct(result.risk.cvar_confidence_level)}</p>
                  <p className="text-xl font-bold mt-1">Bs. {fmtNum(result.profit.cvar_95, 0)}</p>
                  <p className="text-[11px] text-muted-foreground mt-0.5">Beneficio medio dentro de esa peor cola</p>
                </CardContent></Card>
              </div>

              {/* Time series chart */}
              {timeSeriesData.length > 0 && (
                <Card>
                  <CardHeader className="pb-2"><CardTitle className="text-sm">Series de tiempo — Demanda, Ingresos y Beneficio</CardTitle></CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={220}>
                      <AreaChart data={timeSeriesData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                        <defs>
                          <linearGradient id="gProfit" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#34d399" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#34d399" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(216 34% 17%)" />
                        <XAxis dataKey="period" tick={{ fill: 'hsl(215.4 16.3% 56.9%)', fontSize: 10 }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                        <YAxis tick={{ fill: 'hsl(215.4 16.3% 56.9%)', fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={(v) => `${(v / 1000).toFixed(1)}K`} />
                        <Tooltip contentStyle={{ background: 'hsl(224 71% 6%)', border: '1px solid hsl(216 34% 17%)', borderRadius: '8px', fontSize: 11 }} formatter={(v: number, name: string) => [`Bs. ${fmtNum(v, 0)}`, name]} />
                        <Area type="monotone" dataKey="profit" name="Beneficio" stroke="#34d399" strokeWidth={2} fill="url(#gProfit)" dot={false} />
                        <Area type="monotone" dataKey="revenue" name="Ingresos" stroke="hsl(224 76% 48%)" strokeWidth={1.5} fill="none" dot={false} strokeDasharray="4 4" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              )}

              {/* Scenarios */}
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm">Análisis de escenarios (por percentil de demanda)</CardTitle></CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-6">
                    <ResponsiveContainer width="100%" height={180}>
                      <BarChart data={scenarioData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(216 34% 17%)" />
                        <XAxis dataKey="name" tick={{ fill: 'hsl(215.4 16.3% 56.9%)', fontSize: 11 }} tickLine={false} axisLine={false} />
                        <YAxis tick={{ fill: 'hsl(215.4 16.3% 56.9%)', fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={(v) => `${(v / 1000).toFixed(1)}K`} />
                        <Tooltip contentStyle={{ background: 'hsl(224 71% 6%)', border: '1px solid hsl(216 34% 17%)', borderRadius: '8px', fontSize: 11 }} formatter={(v: number) => [`Bs. ${fmtNum(v, 0)}`, 'Beneficio']} />
                        <Bar dataKey="profit" radius={[4, 4, 0, 0]}>
                          {scenarioData.map((_, i) => <Cell key={i} fill={SCENARIO_COLORS[i]} />)}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                    <div className="space-y-3">
                      {scenarioData.map(({ name, percentile, demand, revenue, profit, margin }, i) => (
                        <div key={name} className="flex items-start gap-3 rounded-lg border border-border p-3">
                          <div className={`mt-1 h-2.5 w-2.5 rounded-full shrink-0`} style={{ background: SCENARIO_COLORS[i % SCENARIO_COLORS.length] }} />
                          <div className="flex-1 min-w-0 text-xs">
                            <p className="font-medium">{name} <span className="text-muted-foreground">(percentil {fmtNum(percentile, 0)} de demanda)</span></p>
                            <p className="text-muted-foreground mt-0.5">Dem: {fmtNum(demand, 0)} · Ing: Bs. {fmtNum(revenue, 0)} · Ben: Bs. {fmtNum(profit, 0)} · Margen: {fmtNum(margin, 1)}%</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              <p className="text-[11px] text-muted-foreground text-center">
                {result.metadata.n_iterations.toLocaleString()} iteraciones · distribución {result.metadata.distribution_used} · {result.metadata.confidence_level * 100}% confianza
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">{label}</p>
      <div className="space-y-2">{children}</div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-1"><Label className="text-[11px]">{label}</Label>{children}</div>
}
