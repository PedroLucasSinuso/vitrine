import { memo } from 'react'
import { useNavigate } from 'react-router-dom'
import { DollarSign, ArrowRight } from 'lucide-react'
import Card from '../ui/Card'
import Badge from '../ui/Badge'
import DataTable from '../ui/DataTable'
import Skeleton from '../ui/Skeleton'
import { formatCurrency } from '../../utils/formatters'
import type { ItemCurvaAbcDTO } from '../../types'
import type { Column } from '../ui/DataTable'

const LIMITE_ABC = 8

interface CurvaAbcPreviewProps {
  data: ItemCurvaAbcDTO[]
  loading: boolean
}

const columns: Column<ItemCurvaAbcDTO>[] = [
  {
    key: 'produto',
    label: 'Produto',
    render: (r) => r.produto ?? r.grupo ?? '—',
  },
  {
    key: 'receita',
    label: 'Receita',
    align: 'right',
    render: (r) => <span className="font-semibold tabular-nums">{formatCurrency(r.receita)}</span>,
  },
  {
    key: 'participacao',
    label: 'Participação',
    align: 'right',
    render: (r) => <span className="tabular-nums">{r.participacao_pct.toFixed(1)}%</span>,
  },
  {
    key: 'curva',
    label: 'Curva',
    render: (r) => (
      <Badge
        variant={r.curva === 'A' ? 'success' : r.curva === 'B' ? 'warning' : 'danger'}
        dot
        pulse={r.curva === 'A'}
      >
        {r.curva}
      </Badge>
    ),
  },
]

export default memo(function CurvaAbcPreview({ data, loading }: CurvaAbcPreviewProps) {
  const navigate = useNavigate()

  return (
    <Card variant="default" className="p-5">
      <h2 className="text-sm font-semibold text-text-primary font-display flex items-center gap-2 mb-4">
        <DollarSign size={16} className="text-primary" />
        Curva ABC
      </h2>

      {data.length > 0 ? (
        <>
          <DataTable
            columns={columns}
            data={data.slice(0, LIMITE_ABC)}
            rowKey={(r) => r.produto ?? r.grupo ?? ''}
          />
          <button
            onClick={() => navigate('/bi/curva-abc')}
            className="mt-3 text-xs font-semibold text-primary hover:text-primary/80 transition mx-auto flex items-center gap-1"
          >
            Ver análise completa <ArrowRight size={12} />
          </button>
        </>
      ) : (
        <div className="h-[120px]">
          {loading ? (
            <div className="flex flex-col gap-3 p-2">
              {[1,2,3,4].map(i => (
                <div key={i} className="flex items-center gap-4">
                  <Skeleton className="h-4 flex-1" />
                  <Skeleton className="w-20 h-4 rounded-md" />
                  <Skeleton className="w-12 h-4 rounded-md" />
                  <Skeleton className="w-10 h-6 rounded-full" />
                </div>
              ))}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-sm text-text-muted">
              Nenhum dado disponível
            </div>
          )}
        </div>
      )}
    </Card>
  )
})
