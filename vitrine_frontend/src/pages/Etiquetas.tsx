import { useState, useRef } from 'react'
import { buscarProduto } from '../api/produtos'
import LeitorCodigo from '../components/LeitorCodigo'
import { gerarCSV, baixarCSV, type CsvRow } from '../utils/csv'
import { Camera, Tag, Trash2, Download, Plus } from 'lucide-react'
import { useLocalStorage } from '../hooks/useLocalStorage'
import PageContainer from '../components/layout/PageContainer'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'

interface ItemEtiqueta {
  codigo: string
  nome: string
}

export default function Etiquetas() {
  const [itens, setItens] = useLocalStorage<ItemEtiqueta[]>('etiquetas_lista', [])
  const [erro, setErro] = useState('')
  const [camera, setCamera] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  async function handleCodigo(codigo: string) {
    setErro('')
    const codigoLimpo = codigo.trim()
    if (!codigoLimpo) return

    if (itens.some(i => i.codigo === codigoLimpo)) {
      setErro(`Produto ${codigoLimpo} já está na lista.`)
      if (inputRef.current) inputRef.current.value = ''
      return
    }

    try {
      const produto = await buscarProduto(codigoLimpo)
      setItens(prev => [{ codigo: produto.codigo_chamada, nome: produto.nome }, ...prev].slice(0, 100))
      if (inputRef.current) inputRef.current.value = ''
    } catch (e: unknown) {
      const error = e as { response?: { status?: number } }
      if (error.response?.status === 404) setErro('Produto não encontrado.')
      else if (error.response?.status === 400) setErro('Código inválido.')
      else setErro('Erro ao consultar.')
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      handleCodigo((e.target as HTMLInputElement).value)
    }
  }

  function remover(codigo: string) {
    setItens(prev => prev.filter(i => i.codigo !== codigo))
  }

  function handleExportar() {
    if (itens.length === 0) return
    const rows: CsvRow[] = itens.map(i => ({ codigo: i.codigo, tipo: 'chamada', quantidade: 1 }))
    baixarCSV(gerarCSV(rows), 'etiquetas')
  }

  return (
    <PageContainer maxWidth="md">
      {camera && (
        <LeitorCodigo
          onLeitura={(codigo) => { setCamera(false); setTimeout(() => handleCodigo(codigo), 50) }}
          onFechar={() => setCamera(false)}
        />
      )}

      <div className="w-full max-w-md flex flex-col gap-5">

        {/* Input card */}
        <Card variant="elevated" padding="lg">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-primary-light flex items-center justify-center">
              <Tag size={20} className="text-primary" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-text-primary">Bipar produtos</h2>
              <p className="text-xs text-text-muted">Adicione produtos à lista de etiquetas</p>
            </div>
          </div>
          <div className="flex gap-2">
            <input
              ref={inputRef}
              aria-label="Código do produto"
              className="form-input-base flex-1 rounded-xl"
              placeholder="Digite ou bipe o código"
              onKeyDown={handleKeyDown}
              autoFocus
            />
            <button
              onClick={() => setCamera(true)}
              className="md:hidden bg-bg-input border border-border-input hover:bg-bg-hover text-text-secondary px-3 py-2 rounded-xl transition"
              aria-label="Ler código de barras"
            >
              <Camera size={18} />
            </button>
          </div>
          {erro && <p className="text-danger text-sm mt-2" role="alert">{erro}</p>}
        </Card>

        {/* Lista card */}
        {itens.length > 0 && (
          <Card variant="elevated" padding="lg">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2">
                <Plus size={16} className="text-text-muted" />
                <h2 className="text-base font-semibold text-text-primary">
                  Lista <span className="text-text-muted font-normal text-sm">({itens.length} produtos)</span>
                </h2>
              </div>
              <div className="flex gap-2">
                <Button variant="ghost" onClick={() => setItens([])}>
                  <Trash2 size={13} /> Limpar
                </Button>
                <Button onClick={handleExportar}>
                  <Download size={13} /> Exportar
                </Button>
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              {itens.map(item => (
                <div key={item.codigo} className="flex justify-between items-center border border-border rounded-xl px-4 py-3 hover:bg-bg-hover transition group">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-bg-card flex items-center justify-center shrink-0">
                      <Tag size={14} className="text-text-muted" />
                    </div>
                    <div className="min-w-0">
                      <Badge variant="info">{item.codigo}</Badge>
                      <span className="text-sm text-text-secondary ml-2 truncate">{item.nome}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => remover(item.codigo)}
                    className="text-text-muted hover:text-danger transition opacity-100 sm:opacity-0 sm:group-hover:opacity-100 p-1"
                    aria-label={`Remover ${item.nome}`}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </PageContainer>
  )
}
