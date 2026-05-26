interface Props {
  variant?: 'text' | 'card' | 'circle' | 'table-row' | 'chart' | 'kpi'
  className?: string
}

const variants: Record<string, string> = {
  text:      'h-4 w-full rounded',
  card:      'h-32 w-full rounded-xl',
  circle:    'h-10 w-10 rounded-full',
  'table-row': 'h-12 w-full rounded-lg',
  chart:     'h-[180px] w-full rounded-xl',
  kpi:       'h-24 w-full rounded-xl',
}

export default function Skeleton({ variant = 'text', className = '' }: Props) {
  return (
    <div
      className={`animate-pulse bg-bg-hover ${variants[variant]} ${className}`}
      aria-hidden="true"
    />
  )
}
