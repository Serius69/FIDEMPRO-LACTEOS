import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Building2, PlayCircle, FileText,
  Brain, BarChart3, ExternalLink, Sparkles,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { backendUrl } from '@/lib/config'

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/businesses', icon: Building2, label: 'Negocios' },
  { to: '/onboarding', icon: Sparkles, label: 'Diagnóstico' },
  { to: '/simulate', icon: PlayCircle, label: 'Simulación MC' },
  { to: '/forecast', icon: BarChart3, label: 'Pronóstico' },
  { to: '/reports', icon: FileText, label: 'Reportes' },
]

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[100] focus:bg-primary focus:text-white focus:px-4 focus:py-2 focus:rounded-lg focus:shadow-lg focus:text-sm focus:font-medium">
        Saltar al contenido
      </a>
      <nav className="flex w-56 shrink-0 flex-col border-r border-border bg-card/30">
        <div className="flex items-center gap-2.5 px-4 py-4 border-b border-border">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/20 text-primary">
            <Brain className="h-4 w-4" />
          </div>
          <div>
            <p className="text-xs font-semibold">Findempro AI</p>
            <p className="text-[10px] text-muted-foreground">Simulación Monte Carlo</p>
          </div>
        </div>
        <div className="flex-1 py-3 space-y-0.5 px-2">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => cn(
              'flex items-center gap-2.5 rounded-lg px-3 py-2 text-xs transition-colors',
              isActive ? 'bg-primary/15 text-foreground font-medium' : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
            )}>
              <Icon className="h-4 w-4 shrink-0" /> {label}
            </NavLink>
          ))}
        </div>
        <div className="p-3 space-y-1 border-t border-border">
          <a href={backendUrl('/swagger/')} target="_blank" rel="noreferrer"
            className="flex items-center gap-2 text-[11px] text-muted-foreground hover:text-foreground transition-colors">
            <ExternalLink className="h-3.5 w-3.5" /> API Docs →
          </a>
          <a href={backendUrl('/admin/')} target="_blank" rel="noreferrer"
            className="flex items-center gap-2 text-[11px] text-muted-foreground hover:text-foreground transition-colors">
            <ExternalLink className="h-3.5 w-3.5" /> Django Admin →
          </a>
        </div>
      </nav>
      <main id="main-content" className="flex flex-1 flex-col overflow-hidden">{children}</main>
    </div>
  )
}
