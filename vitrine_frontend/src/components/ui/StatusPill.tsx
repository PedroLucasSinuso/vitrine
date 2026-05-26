interface Props {
  status: 'online' | 'offline' | 'idle'
  label?: string
  className?: string
}

const statusConfig: Record<string, { bg: string; text: string; dot: string; pulse: boolean }> = {
  online: {
    bg: 'bg-online-light',
    text: 'text-online',
    dot: 'bg-online',
    pulse: true,
  },
  offline: {
    bg: 'bg-offline-light',
    text: 'text-offline',
    dot: 'bg-offline',
    pulse: false,
  },
  idle: {
    bg: 'bg-idle-light',
    text: 'text-idle',
    dot: 'bg-idle',
    pulse: false,
  },
}

const defaultLabels: Record<string, string> = {
  online: 'Online',
  offline: 'Offline',
  idle: 'Atenção',
}

export default function StatusPill({ status, label, className = '' }: Props) {
  const cfg = statusConfig[status] ?? statusConfig.online
  const safeLabel = label ?? defaultLabels[status] ?? status
  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold font-mono border border-current/20 ${cfg.bg} ${cfg.text} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} ${cfg.pulse ? 'animate-pulse' : ''}`} />
      <span>{safeLabel}</span>
    </div>
  )
}
