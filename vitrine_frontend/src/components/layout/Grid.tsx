import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  cols?: 1 | 2 | 3 | 4 | 5 | 6
  gap?: 'sm' | 'md' | 'lg'
  className?: string
}

const colClasses: Record<number, string> = {
  1: 'grid-cols-1',
  2: 'grid-cols-1 sm:grid-cols-2',
  3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
  4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
  5: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-5',
  6: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-6',
}

const gapClasses: Record<string, string> = {
  sm: 'gap-3',
  md: 'gap-4',
  lg: 'gap-5',
}

/**
 * Grid — layout responsivo de grid com gap consistente
 * 
 * Uso:
 * ```tsx
 * <Grid cols={3} gap="md">
 *   <KpiCard .../>
 *   <KpiCard .../>
 * </Grid>
 * ```
 */
export default function Grid({ children, cols = 2, gap = 'md', className = '' }: Props) {
  return (
    <div className={`grid ${colClasses[cols]} ${gapClasses[gap]} ${className}`}>
      {children}
    </div>
  )
}
