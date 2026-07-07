import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'
const v = cva('inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors', {
  variants: {
    variant: {
      default: 'border-transparent bg-primary text-primary-foreground',
      secondary: 'border-transparent bg-secondary text-secondary-foreground',
      outline: 'text-foreground',
      success: 'border-emerald-500/30 bg-emerald-500/20 text-emerald-400',
      warning: 'border-amber-500/30 bg-amber-500/20 text-amber-400',
      danger: 'border-red-500/30 bg-red-500/20 text-red-400',
      info: 'border-blue-500/30 bg-blue-500/20 text-blue-400',
    },
  },
  defaultVariants: { variant: 'default' },
})
export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof v> {}
export function Badge({ className, variant, ...p }: BadgeProps) { return <div className={cn(v({ variant }), className)} {...p} /> }
