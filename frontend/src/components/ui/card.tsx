import * as React from 'react'
import { cn } from '@/lib/utils'
export const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...p }, ref) => <div ref={ref} className={cn('rounded-xl border bg-card text-card-foreground shadow', className)} {...p} />)
Card.displayName = 'Card'
export const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...p }, ref) => <div ref={ref} className={cn('flex flex-col space-y-1.5 p-5', className)} {...p} />)
CardHeader.displayName = 'CardHeader'
export const CardTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(({ className, ...p }, ref) => <h3 ref={ref} className={cn('font-semibold leading-none tracking-tight', className)} {...p} />)
CardTitle.displayName = 'CardTitle'
export const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...p }, ref) => <div ref={ref} className={cn('p-5 pt-0', className)} {...p} />)
CardContent.displayName = 'CardContent'
