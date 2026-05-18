interface Props {
  className?: string
  variant?: 'text' | 'card' | 'circle' | 'table-row' | 'chart' | 'kpi'
}

const variants: Record<string, string> = {
  text: 'h-4 w-full rounded-md',
  card: 'h-32 w-full rounded-xl',
  circle: 'h-10 w-10 rounded-full',
  'table-row': 'h-12 w-full rounded-lg',
  chart: 'h-64 w-full rounded-xl',
  kpi: 'h-24 w-full rounded-xl',
}

export default function Skeleton({ className = '', variant = 'text' }: Props) {
  return (
    <div
      className={`animate-pulse bg-slate-200 dark:bg-slate-700/50 ${variants[variant]} ${className}`}
    />
  )
}
