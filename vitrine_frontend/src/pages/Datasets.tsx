import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Database, Trash2 } from 'lucide-react'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import DataTable, { type Column } from '../components/ui/DataTable'
import EmptyState from '../components/ui/EmptyState'
import Modal from '../components/ui/Modal'
import { excluirDataset, listarDatasets } from '../api/importacao'
import { useToast } from '../hooks/useToast'
import type { DatasetResumo } from '../types'
import { NOMES_TIPO_DATASET, formatarDataCurta } from '../utils/equipe'

export default function Datasets() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [datasets, setDatasets] = useState<DatasetResumo[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [excluindo, setExcluindo] = useState<DatasetResumo | null>(null)

  const carregar = useCallback(() => {
    setCarregando(true)
    listarDatasets()
      .then((d) => { setDatasets(d); setErro(null) })
      .catch(() => setErro('Não foi possível carregar os dados importados.'))
      .finally(() => setCarregando(false))
  }, [])

  useEffect(() => { const t = setTimeout(carregar); return () => clearTimeout(t) }, [carregar])

  async function confirmarExclusao() {
    if (!excluindo) return
    await excluirDataset(excluindo.id)
    toast({ type: 'success', message: 'Dados excluídos' })
    setExcluindo(null)
    carregar()
  }

  const colunas: Column<DatasetResumo>[] = [
    { key: 'nome_origem', label: 'Arquivo', align: 'left', headerAlign: 'left', render: (d) => <span className="text-text-primary">{d.nome_origem}</span> },
    { key: 'tipo', label: 'Conteúdo', align: 'left', headerAlign: 'left', hide: 'sm', render: (d) => NOMES_TIPO_DATASET[d.tipo] },
    { key: 'periodo', label: 'Período', render: (d) => `${formatarDataCurta(d.inicio)} a ${formatarDataCurta(d.fim)}` },
    { key: 'linhas', label: 'Linhas', align: 'right', hide: 'sm', render: (d) => d.linhas.toLocaleString('pt-BR') },
    { key: 'criado_em', label: 'Importado em', hide: 'md', render: (d) => formatarDataCurta(d.criado_em) },
    {
      key: 'acoes', label: '', align: 'right',
      render: (d) => (
        <button aria-label={`Excluir ${d.nome_origem}`} className="text-text-muted hover:text-danger p-1" onClick={(e) => { e.stopPropagation(); setExcluindo(d) }}>
          <Trash2 size={16} />
        </button>
      ),
    },
  ]

  return (
    <div className="flex flex-col gap-5 max-w-full">
      <div className="page-section-header mb-0">
        <div>
          <h1 className="page-section-title">Dados importados</h1>
          <p className="page-section-subtitle">Relatórios confirmados que alimentam as análises. Excluir apaga os dados em definitivo.</p>
        </div>
        <Button onClick={() => navigate('/importar')}>Importar relatório</Button>
      </div>
      <Card variant="bordered">
        <DataTable
          data={datasets}
          columns={colunas}
          loading={carregando}
          error={erro}
          onRetry={carregar}
          rowKey={(d) => d.id}
          empty={<EmptyState icon={<Database size={28} />} title="Nenhum dado importado" description="Importe um relatório de vendas para começar." />}
        />
      </Card>
      <Modal
        open={excluindo !== null}
        onClose={() => setExcluindo(null)}
        title="Excluir dados importados?"
        variant="danger"
        size="sm"
        actions={(
          <>
            <Button variant="ghost" onClick={() => setExcluindo(null)}>Cancelar</Button>
            <Button variant="danger" onClick={confirmarExclusao}>Excluir</Button>
          </>
        )}
      >
        <p className="text-sm text-text-secondary">
          Os dados de <strong>{excluindo?.nome_origem}</strong> serão apagados e deixarão de aparecer nas análises.
        </p>
      </Modal>
    </div>
  )
}
