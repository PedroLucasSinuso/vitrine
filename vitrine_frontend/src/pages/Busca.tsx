import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Camera, Loader2, Search as SearchIcon, BarChart3 } from 'lucide-react'
import { formatCurrency } from '../utils/formatters'
import { buscarProduto, buscarProdutosPorNome, registrarNaoEncontrado } from '../api/produtos'
import type { ProdutoBasico, ProdutoCompleto } from '../types'
import { useAuth } from '../hooks/useAuth'
import LeitorCodigo from '../components/LeitorCodigo'
import PageContainer from '../components/layout/PageContainer'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import Modal from '../components/ui/Modal'
import EmptyState from '../components/ui/EmptyState'

function isCompleto(p: ProdutoBasico | ProdutoCompleto): p is ProdutoCompleto {
  return 'preco_custo' in p
}

export default function Busca() {
  const { getRole } = useAuth()

  const [codigo, setCodigo] = useState('')
  const [produto, setProduto] = useState<ProdutoBasico | ProdutoCompleto | null>(null)
  const [erro, setErro] = useState('')
  const [loading, setLoading] = useState(false)
  const [cameras, setCameras] = useState(false)
  const [codigoNaoEncontrado, setCodigoNaoEncontrado] = useState<string | null>(null)
  const [observacao, setObservacao] = useState('')
  const [enviandoObs, setEnviandoObs] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<ProdutoBasico[]>([])
  const [searching, setSearching] = useState(false)
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    return () => { mountedRef.current = false }
  }, [])

  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current)
    const q = searchQuery.trim()
    searchTimer.current = setTimeout(async () => {
      if (!mountedRef.current) return
      if (q.length < 2) { setSearchResults([]); setSearching(false); return }
      setSearching(true)
      try {
        const results = await buscarProdutosPorNome(q)
        if (mountedRef.current) setSearchResults(results)
      } catch {
        if (mountedRef.current) setSearchResults([])
      } finally {
        if (mountedRef.current) setSearching(false)
      }
    }, 300)
    return () => { if (searchTimer.current) clearTimeout(searchTimer.current) }
  }, [searchQuery])

  const role = getRole()

  async function handleBuscar(codigoParam?: string) {
    const valor = (codigoParam ?? codigo).trim()
    if (!valor) return
    setErro('')
    setProduto(null)
    setLoading(true)
    try {
      const produtoEncontrado = await buscarProduto(valor)
      if (!mountedRef.current) return
      setProduto(produtoEncontrado)
    } catch (e: unknown) {
      const error = e as { response?: { status?: number } }
      if (error.response?.status === 404) setCodigoNaoEncontrado(valor)
      else if (error.response?.status === 400) setErro('Código inválido.')
      else setErro('Erro ao consultar. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  function handleLeitura(codigoLido: string) {
    setCameras(false)
    setCodigo(codigoLido)
    handleBuscar(codigoLido)
  }

  async function handleEnviarObservacao() {
    if (!codigoNaoEncontrado) return
    setEnviandoObs(true)
    try { await registrarNaoEncontrado(codigoNaoEncontrado, observacao.trim()) }
    finally { setCodigoNaoEncontrado(null); setObservacao(''); setEnviandoObs(false) }
  }

  return (
    <PageContainer maxWidth="full">
      <div className="flex flex-col items-center px-4 py-4">
      {cameras && (
        <LeitorCodigo onLeitura={handleLeitura} onFechar={() => setCameras(false)} />
      )}

      {/* Modal Produto não encontrado */}
      <Modal
        open={!!codigoNaoEncontrado}
        onClose={() => { setCodigoNaoEncontrado(null); setObservacao('') }}
        title="Produto não encontrado"
        actions={
          <>
            <Button variant="ghost" onClick={() => { setCodigoNaoEncontrado(null); setObservacao('') }}>
              Ignorar
            </Button>
            <Button onClick={handleEnviarObservacao} loading={enviandoObs} disabled={!observacao.trim()}>
              Registrar
            </Button>
          </>
        }
      >
        <p className="text-xs text-text-muted mb-3">Código: {codigoNaoEncontrado}</p>
        <textarea
          className="w-full border border-border-input bg-bg-input text-text-primary rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-border-focus resize-none"
          placeholder="Observação (ex: Coca Cola lata 250ml)"
          rows={3}
          value={observacao}
          onChange={(e) => setObservacao(e.target.value)}
          autoFocus
        />
      </Modal>

      {/* Input de busca EAN/PLU */}
      <div className="w-full max-w-md flex gap-2 mb-6">
        <input
          aria-label="Código EAN ou PLU"
          className="flex-1 border border-border-input bg-bg-input text-text-primary rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-border-focus placeholder:text-text-muted"
          placeholder="Digite o código EAN ou PLU"
          value={codigo}
          onChange={(e) => setCodigo(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleBuscar()}
          autoFocus
        />
        <button
          onClick={() => setCameras(true)}
          className="md:hidden bg-bg-input border border-border-input hover:bg-bg-hover text-text-secondary px-3 py-2 rounded-xl transition"
          aria-label="Ler código de barras"
        >
          <Camera size={18} />
        </button>
        <Button onClick={() => handleBuscar()} loading={loading}>
          <SearchIcon size={14} /> Buscar
        </Button>
      </div>

      {/* Busca por nome */}
      <div className="w-full max-w-md mb-6 relative">
        <div className="relative">
          <input
            aria-label="Buscar produto por nome"
            className="w-full border border-border-input bg-bg-input text-text-primary rounded-xl px-4 py-2.5 pr-10 focus:outline-none focus:ring-2 focus:ring-border-focus placeholder:text-text-muted"
            placeholder="Buscar produto por nome..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searching && (
            <span className="absolute right-3 top-1/2 -translate-y-1/2">
              <Loader2 size={14} className="animate-spin text-text-muted" />
            </span>
          )}
        </div>
        {searchResults.length > 0 && (
          <div className="mt-2 bg-bg-card rounded-xl shadow-modal border border-border divide-y divide-border overflow-y-auto max-h-60 absolute left-0 right-0 z-20">
            {searchResults.map((p) => (
              <button
                key={p.codigo_chamada}
                onClick={() => {
                  setCodigo(p.codigo_chamada)
                  handleBuscar(p.codigo_chamada)
                  setSearchQuery('')
                  setSearchResults([])
                }}
                className="w-full text-left px-4 py-3 hover:bg-primary-lighter transition flex justify-between items-center"
              >
                <span className="text-sm font-medium text-text-primary">{p.nome}</span>
                <span className="text-xs text-text-muted">{p.codigo_chamada}</span>
              </button>
            ))}
          </div>
        )}
        {searchQuery.trim().length >= 2 && !searching && searchResults.length === 0 && (
          <EmptyState title="Nenhum produto encontrado" description={`Nenhum resultado para "${searchQuery}"`} />
        )}
      </div>

      {erro && <p className="text-danger text-sm mb-4" role="alert">{erro}</p>}

      {produto && (
        <>
        <Card variant="elevated" className="w-full max-w-md">
          <div>
            <p className="text-xs text-text-muted uppercase tracking-wider font-medium">Produto</p>
            <p className="text-base md:text-lg font-bold text-text-primary break-words">{produto.nome}</p>
          </div>

          <div className="flex gap-3 mt-3 flex-wrap">
            <Badge variant="info">{produto.grupo}</Badge>
            <Badge variant="default">{produto.familia}</Badge>
          </div>

          <div className="border-t border-border pt-3 mt-3">
            <p className="text-xs text-text-muted uppercase tracking-wider font-medium">Preço de Venda</p>
            <p className="text-xl md:text-3xl font-bold text-primary break-words animate-pulse-glow">
              {formatCurrency(produto.preco_venda)}
            </p>
          </div>

          <div className="border-t border-border pt-3 mt-3">
            <p className="text-xs text-text-muted uppercase tracking-wider font-medium">Estoque</p>
            <p className="text-sm font-semibold text-text-primary">{produto.estoque} un.</p>
          </div>

          {isCompleto(produto) && (
            <>
              <div className="flex gap-4 border-t border-border pt-3 mt-3">
                <div>
                  <p className="text-xs text-text-muted uppercase tracking-wider font-medium">Preço de Custo</p>
                  <p className="text-sm font-semibold text-text-primary">
                    {formatCurrency(produto.preco_custo)}
                  </p>
                </div>
              </div>
              <div className="flex gap-4 mt-2">
                <div>
                  <p className="text-xs text-text-muted uppercase tracking-wider font-medium">Markup</p>
                  <p className="text-sm font-semibold text-text-primary">
                    {(produto.markup * 100).toFixed(2)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-text-muted uppercase tracking-wider font-medium">Margem</p>
                  <p className="text-sm font-semibold text-text-primary">
                    {(produto.margem * 100).toFixed(2)}%
                  </p>
                </div>
              </div>
            </>
          )}
        </Card>

        {(role === 'supervisor' || role === 'admin') && (
          <Link
            to={`/bi/sku?codigo=${produto.codigo_chamada ?? ''}`}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-primary text-white text-sm font-medium rounded-lg hover:bg-primary-hover transition-colors mt-4 w-full max-w-md"
          >
            <BarChart3 size={16} />
            Análise de Vendas
          </Link>
        )}
      </>
      )}

      {!loading && !produto && !searchQuery.trim() && !erro && (
        <EmptyState
          title="Busque um produto"
          description="Digite o código EAN/PLU, use a câmera ou busque por nome"
        />
      )}
      </div>
    </PageContainer>
  )
}
