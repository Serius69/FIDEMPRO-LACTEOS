import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { BarChart3, Loader2 } from 'lucide-react'
import { ResponsiveContainer, ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { runForecast } from '@/lib/api'
import { fmtNum } from '@/lib/utils'
import type { ForecastRequest, ForecastResult } from '@/types'

const SAMPLE_DATA = [850, 920, 1050, 980, 1100, 1030, 1200, 1150, 1080, 1300, 1250, 1180]

export default function ForecastPage() {
  const { register, handleSubmit, setValue, watch } = useForm<ForecastRequest>({
    defaultValues: { historical_data: SAMPLE_DATA, periods: 12, method: 'auto', confidence_level: 0.95, include_analysis: true },
  })
  const [result, setResult] = useState<ForecastResult | null>(null)
  const [submittedHistory, setSubmittedHistory] = useState<number[]>(SAMPLE_DATA)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [rawData, setRawData] = useState(SAMPLE_DATA.join(', '))
  const method = watch('method')

  async function onSubmit(data: ForecastRequest) {
    const parsed = rawData.split(',').map((v) => parseFloat(v.trim())).filter((v) => !isNaN(v))
    if (parsed.length < 5) { setError('Ingresa al menos 5 puntos históricos.'); return }
    setLoading(true); setError(''); setResult(null)
    try {
      const nextResult = await runForecast({ ...data, historical_data: parsed })
      setSubmittedHistory(parsed)
      setResult(nextResult)
    }
    catch (e) { setError(e instanceof Error ? e.message : 'Error') }
    finally { setLoading(false) }
  }

  // `forecast` es un objeto con series paralelas, no un array de valores.
  const chartData = result ? [
    ...submittedHistory.map((v, i) => ({ label: `H${i + 1}`, historical: v, forecast: null, lower: null, upper: null })),
    ...result.forecast.values.map((v, i) => ({
      label: `F${i + 1}`, historical: null, forecast: v,
      lower: result.forecast.ci_lower[i],
      upper: result.forecast.ci_upper[i],
    })),
  ] : []

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <header className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <BarChart3 className="h-5 w-5 text-primary" />
        <div>
          <h1 className="text-base font-semibold">Pronóstico de Demanda</h1>
          <p className="text-xs text-muted-foreground mt-0.5">Modelos: lineal, media móvil, suavizado exponencial, auto</p>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <aside className="w-72 shrink-0 border-r border-border overflow-y-auto p-4 space-y-4">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <Label className="text-[11px]">Datos históricos (separados por comas)</Label>
              <textarea
                className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-xs min-h-[100px] resize-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                value={rawData}
                onChange={(e) => setRawData(e.target.value)}
                placeholder="100, 120, 115, 130, ..."
              />
              <p className="text-[10px] text-muted-foreground">{rawData.split(',').filter((v) => !isNaN(parseFloat(v.trim()))).length} puntos detectados</p>
              <p className="text-[10px] text-amber-500">Los valores iniciales son un EJEMPLO SINTÉTICO; reemplázalos con observaciones de tu negocio.</p>
            </div>

            <div className="space-y-1.5">
              <Label className="text-[11px]">Períodos a pronosticar</Label>
              <Input type="number" min={1} max={60} {...register('periods', { valueAsNumber: true })} />
            </div>

            <div className="space-y-1.5">
              <Label className="text-[11px]">Método de pronóstico</Label>
              <Select value={method} onValueChange={(v) => setValue('method', v as ForecastRequest['method'])}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {[['auto', 'Automático (mejor ajuste)'], ['linear', 'Regresión lineal'], ['moving_average', 'Media móvil'], ['exponential_smoothing', 'Suavizado exponencial']].map(([v, l]) => (
                    <SelectItem key={v} value={v}>{l}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="text-[11px]">Nivel de confianza</Label>
              <Select value={String(watch('confidence_level'))} onValueChange={(v) => setValue('confidence_level', Number(v))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {[0.80, 0.90, 0.95, 0.99].map((c) => <SelectItem key={c} value={String(c)}>{(c * 100).toFixed(0)}%</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? <><Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> Calculando...</> : 'Generar Pronóstico'}
            </Button>
          </form>
        </aside>

        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {error && <div role="alert" className="rounded-lg bg-destructive/10 border border-destructive/20 p-4 text-sm text-red-400">{error}</div>}

          {!result && !loading && (
            <div className="flex flex-col items-center gap-4 py-20 text-center">
              <div className="h-16 w-16 rounded-2xl bg-primary/10 flex items-center justify-center text-3xl">📈</div>
              <div>
                <h2 className="text-lg font-semibold">Pronóstico de series de tiempo</h2>
                <p className="text-sm text-muted-foreground mt-1 max-w-sm">Ingresa tus datos históricos de demanda y obtén proyecciones con intervalos de confianza.</p>
              </div>
            </div>
          )}

          {result && (
            <>
              <div className="grid grid-cols-4 gap-4 animate-fade-in">
                {[
                  { label: 'Método usado', value: result.forecast.method_used },
                  { label: 'Confianza', value: `${(result.forecast.confidence_level * 100).toFixed(0)}%` },
                  // MAPE llega `null` cuando el holdout tiene observaciones en
                  // cero: `fmtNum` lo pinta como «—» en vez de fabricar un 0.
                  { label: 'RMSE (unidades)', value: fmtNum(result.forecast.rmse) },
                  { label: 'MAPE', value: result.forecast.mape == null ? '—' : `${fmtNum(result.forecast.mape)}%` },
                ].map(({ label, value }) => (
                  <Card key={label}><CardContent className="p-4">
                    <p className="text-xs text-muted-foreground">{label}</p>
                    <p className="text-base font-bold text-primary mt-1">{value}</p>
                  </CardContent></Card>
                ))}
              </div>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Histórico + Pronóstico con intervalos de confianza</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={260}>
                    <ComposedChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="ci" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="hsl(224 76% 48%)" stopOpacity={0.2} />
                          <stop offset="95%" stopColor="hsl(224 76% 48%)" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(216 34% 17%)" />
                      <XAxis dataKey="label" tick={{ fill: 'hsl(215.4 16.3% 56.9%)', fontSize: 10 }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                      <YAxis tick={{ fill: 'hsl(215.4 16.3% 56.9%)', fontSize: 10 }} tickLine={false} axisLine={false} domain={['auto', 'auto']} />
                      <Tooltip contentStyle={{ background: 'hsl(224 71% 6%)', border: '1px solid hsl(216 34% 17%)', borderRadius: '8px', fontSize: 11 }} />
                      <Area type="monotone" dataKey="upper" stroke="none" fill="url(#ci)" name="IC superior" />
                      <Area type="monotone" dataKey="lower" stroke="none" fill="hsl(var(--background))" name="IC inferior" />
                      <Line type="monotone" dataKey="historical" name="Histórico" stroke="hsl(215.4 16.3% 56.9%)" strokeWidth={2} dot={false} connectNulls={false} />
                      <Line type="monotone" dataKey="forecast" name="Pronóstico" stroke="hsl(224 76% 48%)" strokeWidth={2} strokeDasharray="6 3" dot={{ r: 3 }} connectNulls={false} />
                    </ComposedChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm">Valores pronosticados</CardTitle></CardHeader>
                <CardContent className="p-0">
                  <table className="w-full text-xs">
                    <thead><tr className="border-b border-border">
                      {['Período', 'Pronóstico', 'IC inferior', 'IC superior'].map((h) => (
                        <th key={h} scope="col" className="px-4 py-2 text-left font-medium text-muted-foreground">{h}</th>
                      ))}
                    </tr></thead>
                    <tbody>
                      {result.forecast.values.map((v, i) => (
                        <tr key={i} className="border-b border-border/50 hover:bg-muted/20">
                          <td className="px-4 py-2 text-muted-foreground">+{i + 1}</td>
                          <td className="px-4 py-2 font-medium text-primary">{fmtNum(v, 0)}</td>
                          <td className="px-4 py-2">{fmtNum(result.forecast.ci_lower[i], 0)}</td>
                          <td className="px-4 py-2">{fmtNum(result.forecast.ci_upper[i], 0)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
