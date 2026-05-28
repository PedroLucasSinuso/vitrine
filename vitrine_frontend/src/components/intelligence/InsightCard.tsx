/** Card de insight individual com cores por impacto, ícone por tipo, e botão de dismiss. */
import { useState } from 'react'
import { Lightbulb, X, ChevronDown, ChevronUp, TrendingUp, AlertTriangle, RefreshCw, ShoppingCart, Calendar, List } from 'lucide-react'
import Card from '../ui/Card'
import Badge from '../ui/Badge'
import Button from '../ui/Button'
import ProductListModal from './ProductListModal'
import type { Insight, InsightTipo } from '../../types/intelligence'
import { formatCurrency } from '../../utils/formatters'

const TIPO_ICON: Record<InsightTipo, React.ReactNode> = {
  encalhe: <AlertTriangle size={16} />,
  margem_erosao: <TrendingUp size={16} />,
  taxa_troca: <RefreshCw size={16} />,
  oportunidade_b: <Lightbulb size={16} />,
  sazonalidade: <Calendar size={16} />,
  outro: <ShoppingCart size={16} />,
}

const IMPACTO_COLORS: Record<string, { border: string; badge: 'danger' | 'warning' | 'info' }> = {
  alto: { border: 'border-l-red-400', badge: 'danger' },
  medio: { border: 'border-l-orange-400', badge: 'warning' },
  baixo: { border: 'border-l-blue-400', badge: 'info' },
}

interface Props {
  insight: Insight
  onDismiss: () => void
}

export default function InsightCard({ insight, onDismiss }: Props) {
  const [expanded, setExpanded] = useState(false)
  const [showProdutos, setShowProdutos] = useState(false)
  const cores = IMPACTO_COLORS[insight.impacto] ?? IMPACTO_COLORS.baixo
  const icone = TIPO_ICON[insight.tipo] ?? TIPO_ICON.outro

  return (
    <Card className={`border-l-4 ${cores.border}`} padding="md">
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1 space-y-2">
          {/* Header: ícone + badge + tipo */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-lg text-text-primary shrink-0">{icone}</span>
            <Badge variant={cores.badge}>
              {insight.impacto === 'alto' ? 'ALTO' : insight.impacto === 'medio' ? 'MÉDIO' : 'BAIXO'}
            </Badge>
            <span className="text-[11px] text-text-muted uppercase font-mono tracking-wide">
              {insight.tipo.replace(/_/g, ' ')}
            </span>
            {insight.confianca === 'hipotese' && (
              <span className="text-[10px] text-warning bg-warning-light px-1.5 py-0.5 rounded-full font-medium">
                💡 Hipótese
              </span>
            )}
          </div>

          {/* Título */}
          <h3 className="text-base font-semibold text-text-primary">{insight.titulo}</h3>

          {/* Descrição */}
          <p className="text-sm text-text-secondary">{insight.descricao}</p>

          {/* Métricas */}
          {insight.metricas && expanded && (
            <div className="flex flex-wrap gap-3 text-sm bg-bg-hover/50 rounded-lg p-3">
              {insight.metricas.total_encalhados != null && (
                <span>Total: <strong>{insight.metricas.total_encalhados}</strong> itens</span>
              )}
              {insight.metricas.valor_total_encalhado != null && (
                <span>Valor: <strong>{formatCurrency(insight.metricas.valor_total_encalhado)}</strong></span>
              )}
              {insight.metricas.margem_anterior != null && (
                <span>Margem anterior: <strong>{insight.metricas.margem_anterior}%</strong></span>
              )}
              {insight.metricas.margem_atual != null && (
                <span>Margem atual: <strong>{insight.metricas.margem_atual}%</strong></span>
              )}
              {insight.metricas.taxa != null && (
                <span>Taxa: <strong>{insight.metricas.taxa}%</strong></span>
              )}
              {insight.metricas.margem_b != null && (
                <span>Margem B: <strong>{insight.metricas.margem_b}%</strong></span>
              )}
              {insight.metricas.potencial_ganho_mensal != null && (
                <span className="text-success font-medium">
                  +{formatCurrency(insight.metricas.potencial_ganho_mensal)}/mês
                </span>
              )}
              {insight.metricas.preco_atual != null && (
                <span>Preço atual: <strong>{formatCurrency(insight.metricas.preco_atual)}</strong></span>
              )}
              {insight.metricas.preco_sugerido != null && (
                <span>Preço sugerido: <strong>{formatCurrency(insight.metricas.preco_sugerido)}</strong></span>
              )}
              {insight.metricas.economia_percentual != null && (
                <span className="text-success">Economia: <strong>{insight.metricas.economia_percentual}%</strong></span>
              )}
            </div>
          )}

          {/* Sugestão */}
          <p className="text-sm italic text-text-muted border-l-2 border-border pl-3">
            {insight.sugestao}
          </p>

          {/* Ver produtos */}
          {insight.produtos && insight.produtos.length > 0 && (
            <Button variant="outline" size="sm" onClick={() => setShowProdutos(true)}>
              <List size={14} className="mr-1.5" />
              Ver {insight.produtos.length} produtos
            </Button>
          )}
        </div>

        {/* Ações à direita */}
        <div className="flex flex-col gap-1 shrink-0">
          <Button variant="ghost" size="sm" onClick={() => setExpanded(!expanded)} aria-label={expanded ? 'Recolher' : 'Expandir'}>
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </Button>
          <Button variant="ghost" size="sm" onClick={onDismiss} aria-label="Ignorar">
            <X size={14} />
          </Button>
        </div>
      </div>

      {/* Modal de produtos */}
      {insight.produtos && (
        <ProductListModal
          open={showProdutos}
          onClose={() => setShowProdutos(false)}
          tipo={insight.tipo}
          produtos={insight.produtos}
        />
      )}
    </Card>
  )
}
