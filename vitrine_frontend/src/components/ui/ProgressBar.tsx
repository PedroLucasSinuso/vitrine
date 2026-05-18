interface Props {
  value: number
  max: number
  className?: string
}

export default function ProgressBar({ value, max, className = '' }: Props) {
  const pct = Math.min((value / Math.max(max, 1)) * 100, 100)
  return (
    <div className={`h-1.5 bg-slate-50 dark:bg-slate-700 rounded-full overflow-hidden ${className}`}>
      <div
        className="h-full bg-gradient-to-r from-primary to-primary-light rounded-full transition-all duration-500"
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}
