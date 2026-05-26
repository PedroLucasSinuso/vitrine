import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  title?: string
  subtitle?: string
  actions?: ReactNode
  className?: string
  variant?: 'card' | 'plain'
  padding?: boolean
}

/**
 * PageSection — seção consistente para páginas
 * 
 * Uso:
 * ```tsx
 * <PageSection title="Título" subtitle="Descrição" actions={<Button>...</Button>}>
 *   <div>conteúdo</div>
 * </PageSection>
 * ```
 */
export default function PageSection({
  children, title, subtitle, actions, className = '',
  variant = 'plain', padding = true,
}: Props) {
  const wrapperClass = variant === 'card'
    ? `card-bordered ${padding ? 'p-5' : ''}`
    : padding ? 'flex flex-col gap-4' : ''

  return (
    <section className={`page-section ${wrapperClass} ${className}`}>
      {(title || actions) && (
        <div className="page-section-header">
          <div className="min-w-0">
            {title && <h2 className="page-section-title">{title}</h2>}
            {subtitle && <p className="page-section-subtitle">{subtitle}</p>}
          </div>
          {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
        </div>
      )}

      {children}
    </section>
  )
}
