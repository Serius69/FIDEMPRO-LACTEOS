import { useEffect, useState } from 'react'
import { ArrowUpRight, ShieldCheck } from 'lucide-react'
import { getSubscriptionContext, type SubscriptionContext } from '@/lib/api'

export function SubscriptionStatus() {
  const [context, setContext] = useState<SubscriptionContext | null>(null)

  useEffect(() => {
    getSubscriptionContext().then(setContext).catch(() => setContext(null))
  }, [])

  if (!context) return null
  const trial = context.subscription.trial_ends_at
    ? `Trial hasta ${new Date(context.subscription.trial_ends_at).toLocaleDateString()}`
    : null

  return (
    <div className="border-t border-border p-3 text-[10px] text-muted-foreground">
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-1 text-foreground">
          <ShieldCheck className="h-3.5 w-3.5 text-primary" />
          {context.organization.name}
        </span>
        <span className="rounded bg-primary/10 px-1.5 py-0.5 font-medium text-primary">
          {context.subscription.effective_plan}
        </span>
      </div>
      {trial && <p className="mt-1">{trial}</p>}
      {context.subscription.effective_plan !== 'BUSINESS' && (
        <a
          href={context.upgrade_url || '/api/subscription/context/'}
          className="mt-2 flex items-center gap-1 text-primary hover:underline"
        >
          Ver opciones de mejora <ArrowUpRight className="h-3 w-3" />
        </a>
      )}
    </div>
  )
}
