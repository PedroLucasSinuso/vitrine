import type { ReactNode } from 'react'

interface Props {
  icon?: React.ElementType
  title?: string
  description?: string
  action?: ReactNode
  children?: ReactNode
  className?: string
}

/**
 * SectionHeader — cabeçalho de seção com ícone, título e descrição opcionais.
 * 
 * Uso 1 (com title):
 *   <SectionHeader icon={X} title="Título" description="Descrição" />
 * 
 * Uso 2 (com children como título):
 *   <SectionHeader icon={X}>Título aqui</SectionHeader>
 */
export default function SectionHeader({
  icon: Icon, title, description, action, children, className = '',
}: Props) {
  const heading = title ?? children
  return (
    <div className={`flex items-start gap-3 ${className}`}>
      {Icon && (
        <div className="mt-0.5 p-1.5 rounded-lg bg-primary-light text-primary shrink-0">
          <Icon size={14} />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-sm font-semibold text-text-primary">
            {heading}
          </h3>
          {action && <div className="shrink-0">{action}</div>}
        </div>
        {description && (
          <p className="text-xs text-text-muted mt-0.5">{description}</p>
        )}
      </div>
    </div>
  )
}
