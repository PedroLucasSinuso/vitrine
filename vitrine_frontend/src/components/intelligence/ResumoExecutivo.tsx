/** Card de resumo executivo da análise Intelligence. */
import { Sparkles, Cpu } from 'lucide-react'
import Card from '../ui/Card'
import type { Fonte } from '../../types/intelligence'
import { formatDateWithWeekday } from '../../utils/formatters'

interface Props {
  texto: string
  fonte: Fonte
  geradoEm: string
}

const FONTE_LABEL: Record<Fonte, { label: string; icon: React.ReactNode; description: string }> = {
  claude: { label: 'Claude Sonnet', icon: <Sparkles size={14} />, description: 'Análise completa com IA' },
  gpt4o_mini: { label: 'GPT-4o Mini', icon: <Sparkles size={14} />, description: 'Análise com IA' },
  deterministico: { label: 'Síntese simplificada', icon: <Cpu size={14} />, description: 'Análise baseada em regras (sem IA)' },
}

export default function ResumoExecutivo({ texto, fonte, geradoEm }: Props) {
  const info = FONTE_LABEL[fonte] ?? FONTE_LABEL.deterministico

  return (
    <Card variant="elevated" padding="md">
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-primary-light text-primary shrink-0">
          <Sparkles size={20} />
        </div>
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold text-text-primary">Resumo Executivo</h2>
            <span className="inline-flex items-center gap-1 text-[10px] text-text-muted bg-bg-hover px-2 py-0.5 rounded-full font-medium">
              {info.icon}
              {info.label}
            </span>
          </div>
          <p className="text-sm text-text-secondary leading-relaxed">{texto}</p>
          <p className="text-[11px] text-text-muted">
            Gerado em {formatDateWithWeekday(geradoEm.split('T')[0])}
          </p>
        </div>
      </div>
    </Card>
  )
}
