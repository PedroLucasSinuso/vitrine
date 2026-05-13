import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sun, Moon, Camera, Loader2, Search as SearchIcon } from 'lucide-react'
import { formatCurrency } from '../utils/formatters'
import { buscarProduto, buscarProdutosPorNome, registrarNaoEncontrado } from '../api/produtos'
import type { ProdutoBasico, ProdutoCompleto } from '../types'
import { useAuth } from '../hooks/useAuth'
import LeitorCodigo from '../components/LeitorCodigo'
import AdminHeader from '../components/AdminHeader'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import EmptyState from '../components/ui/EmptyState'

function isCompleto(p: ProdutoBasico | ProdutoCompleto): p is ProdutoCompleto {
  return 'preco_custo' in p
}

export default function Busca() {
  const navigate = useNavigate()
  const { logout, getRole, getNomeExibicao } = useAuth()
  const [dark, setDark] = useState(() => localStorage.getItem('darkMode') === 'true')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('darkMode', String(dark))
  }, [dark])

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

  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current)
    const q = searchQuery.trim()
    searchTimer.current = setTimeout(async () => {
      if (q.length < 2) { setSearchResults([]); setSearching(false); return }
      setSearching(true)
      try { setSearchResults(await buscarProdutosPorNome(q)) }
      catch { setSearchResults([]) }
      finally { setSearching(false) }
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
      setProduto(await buscarProduto(valor))
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
    <div className="min-h-screen bg-gray-100 dark:bg-gray-950 flex flex-col items-center px-4 py-6">

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
        <p className="text-xs text-gray-400 dark:text-gray-500 mb-3">Código: {codigoNaoEncontrado}</p>
        <textarea
          className="w-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
          placeholder="Observação (ex: Coca Cola lata 250ml)"
          rows={3}
          value={observacao}
          onChange={(e) => setObservacao(e.target.value)}
          autoFocus
        />
      </Modal>

      {/* Header */}
      {role !== 'operador' ? (
        <AdminHeader titulo="Busca" paginaAtual="busca" />
      ) : (
        <div className="w-full max-w-md flex justify-between items-center mb-6">
          <div className="flex items-center gap-4">
            <div>
              <h1 className="text-xl font-bold text-gray-800 dark:text-gray-100">Vitrine</h1>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{getNomeExibicao()}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setDark((prev) => !prev)}
              className="text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
              aria-label="Alternar tema"
            >
              {dark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <button
              onClick={() => { logout(); navigate('/login') }}
              className="text-sm text-gray-500 hover:text-red-500 dark:hover:text-red-400 transition"
            >
              Sair
            </button>
          </div>
        </div>
      )}

      {/* Input de busca */}
      <div className="w-full max-w-md flex gap-2 mb-6">
        <input
          aria-label="Código EAN ou PLU"
          className="flex-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
          placeholder="Digite o código EAN ou PLU"
          value={codigo}
          onChange={(e) => setCodigo(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleBuscar()}
          autoFocus
        />
        <button
          onClick={() => setCameras(true)}
          className="md:hidden bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 px-3 py-2 rounded-lg transition"
          aria-label="Ler código de barras"
        >
          <Camera size={18} />
        </button>
        <Button onClick={() => handleBuscar()} loading={loading}>
          <SearchIcon size={14} /> Buscar
        </Button>
      </div>

      {/* Busca por nome */}
      <div className="w-full max-w-md mb-6">
        <div className="relative">
          <input
            aria-label="Buscar produto por nome"
            className="w-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 rounded-lg px-4 py-2 pr-10 focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="Buscar produto por nome..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searching && (
            <span className="absolute right-3 top-1/2 -translate-y-1/2">
              <Loader2 size={14} className="animate-spin text-gray-400" />
            </span>
          )}
        </div>
        {searchResults.length > 0 && (
          <div className="mt-2 bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 divide-y divide-gray-100 dark:divide-gray-700 max-h-60 overflow-y-auto">
            {searchResults.map((p) => (
              <button
                key={p.codigo_chamada}
                onClick={() => {
                  setCodigo(p.codigo_chamada)
                  handleBuscar(p.codigo_chamada)
                  setSearchQuery('')
                  setSearchResults([])
                }}
                className="w-full text-left px-4 py-3 hover:bg-primary-lighter dark:hover:bg-gray-700 transition flex justify-between items-center"
              >
                <span className="text-sm font-medium text-gray-800 dark:text-gray-100">{p.nome}</span>
                <span className="text-xs text-gray-400 dark:text-gray-500">{p.codigo_chamada}</span>
              </button>
            ))}
          </div>
        )}
        {searchQuery.trim().length >= 2 && !searching && searchResults.length === 0 && (
          <EmptyState title="Nenhum produto encontrado" description={`Nenhum resultado para "${searchQuery}"`} />
        )}
      </div>

      {erro && <p className="text-red-500 text-sm mb-4" role="alert">{erro}</p>}

      {produto && (
        <Card variant="elevated" className="w-full max-w-md">
          <div>
            <p className="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide">Produto</p>
            <p className="text-base md:text-lg font-bold text-gray-800 dark:text-gray-100 break-words">{produto.nome}</p>
          </div>

          <div className="flex gap-4 mt-3">
            <div>
              <p className="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide">Grupo</p>
              <p className="text-sm text-gray-700 dark:text-gray-300">{produto.grupo}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide">Família</p>
              <p className="text-sm text-gray-700 dark:text-gray-300">{produto.familia}</p>
            </div>
          </div>

          <div className="border-t dark:border-gray-700 pt-3 mt-3">
            <p className="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide">Preço de Venda</p>
            <p className="text-xl md:text-3xl font-bold text-primary dark:text-primary-light break-words animate-pulse-glow">
              {formatCurrency(produto.preco_venda)}
            </p>
          </div>

          <div className="border-t dark:border-gray-700 pt-3 mt-3">
            <p className="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide">Estoque</p>
            <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">{produto.estoque} un.</p>
          </div>

          {isCompleto(produto) && (
            <>
              <div className="flex gap-4 border-t dark:border-gray-700 pt-3 mt-3">
                <div>
                  <p className="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide">Preço de Custo</p>
                  <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                    {formatCurrency(produto.preco_custo)}
                  </p>
                </div>
              </div>
              <div className="flex gap-4 mt-2">
                <div>
                  <p className="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide">Markup</p>
                  <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                    {(produto.markup * 100).toFixed(2)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide">Margem</p>
                  <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                    {(produto.margem * 100).toFixed(2)}%
                  </p>
                </div>
              </div>
            </>
          )}
        </Card>
      )}

      {!loading && !produto && !searchQuery.trim() && !erro && (
        <EmptyState
          title="Busque um produto"
          description="Digite o código EAN/PLU, use a câmera ou busque por nome"
        />
      )}
    </div>
  )
}
