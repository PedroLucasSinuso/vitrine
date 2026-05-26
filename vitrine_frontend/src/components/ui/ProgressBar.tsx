interface Props {
  value: number
  max: number
  variant?: 'success' | 'warning' | 'danger' | 'primary'
  size?: 'sm' | 'md'
  showLabel?: boolean
  className?: string
}

const fillColors: Record<string, string> = {
  success: 'bg-success',
  warning: 'bg-warning',
  danger:  'bg-danger',
  primary: 'bg-primary',
}

export default function ProgressBar({
  value, max, variant = 'primary', size = 'sm', showLabel = false, className = '',
}: Props) {
  const pct = Math.min((value / Math.max(max, 1)) * 100, 100)

  return (
    <div className={`${className}`}>
      {showLabel && (
        <div className="flex justify-between text-[10px] font-mono font-bold text-text-muted mb-1">
          <span>{Math.round(pct)}%</span>
          <span>{value}/{max}</span>
        </div>
      )}
      <div className={`${size === 'sm' ? 'h-1.5' : 'h-2.5'} bg-bg-input rounded-full overflow-hidden border border-border/30`}>
        <div
          className={`h-full rounded-full transition-all duration-slow ${fillColors[variant]}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
