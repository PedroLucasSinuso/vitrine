import { useState, useRef } from 'react'
import { buscarProduto } from '../api/produtos'
import AdminHeader from '../components/AdminHeader'
import LeitorCodigo from '../components/LeitorCodigo'
import { gerarCSV, baixarCSV, type CsvRow } from '../utils/csv'
import { Camera, Tag, Trash2, Download, Plus } from 'lucide-react'
import { useLocalStorage } from '../hooks/useLocalStorage'

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
      setItens(prev => [...prev, { codigo: produto.codigo_chamada, nome: produto.nome }])
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
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center px-4 py-6 overflow-x-hidden">
      {camera && (
        <LeitorCodigo
          onLeitura={(codigo) => { setCamera(false); setTimeout(() => handleCodigo(codigo), 50) }}
          onFechar={() => setCamera(false)}
        />
      )}

      <AdminHeader titulo="Etiquetas" paginaAtual="etiquetas" />

      <div className="w-full max-w-2xl flex flex-col gap-5">

        {/* Input card */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-primary/10 dark:bg-primary/20 flex items-center justify-center">
              <Tag size={20} className="text-primary" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-800 dark:text-slate-100">Bipar produtos</h2>
              <p className="text-xs text-slate-400 dark:text-slate-500">Adicione produtos à lista de etiquetas</p>
            </div>
          </div>
          <div className="flex gap-2">
            <input
              ref={inputRef}
              aria-label="Código do produto"
              className="flex-1 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Digite ou bipe o código"
              onKeyDown={handleKeyDown}
              autoFocus
            />
            <button
              onClick={() => setCamera(true)}
              className="md:hidden bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 px-3 py-2 rounded-xl transition"
              aria-label="Ler código de barras"
            >
              <Camera size={18} />
            </button>
          </div>
          {erro && <p className="text-red-500 text-sm mt-2" role="alert">{erro}</p>}
        </div>

        {/* Lista card */}
        {itens.length > 0 && (
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-6">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2">
                <Plus size={16} className="text-slate-400" />
                <h2 className="text-base font-semibold text-slate-800 dark:text-slate-100">
                  Lista <span className="text-slate-400 dark:text-slate-500 font-normal text-sm">({itens.length} produtos)</span>
                </h2>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setItens([])}
                  className="text-sm text-slate-400 hover:text-red-500 transition inline-flex items-center gap-1"
                >
                  <Trash2 size={13} /> Limpar
                </button>
                <button
                  onClick={handleExportar}
                  className="bg-primary hover:bg-primary-hover text-white text-sm font-semibold px-4 py-1.5 rounded-xl transition inline-flex items-center gap-1.5"
                >
                  <Download size={13} /> Exportar
                </button>
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              {itens.map(item => (
                <div key={item.codigo} className="flex justify-between items-center border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition group">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 flex items-center justify-center shrink-0">
                      <Tag size={14} className="text-slate-400 dark:text-slate-500" />
                    </div>
                    <div className="min-w-0">
                      <span className="text-sm font-semibold text-slate-700 dark:text-slate-200 font-mono">{item.codigo}</span>
                      <span className="text-sm text-slate-400 dark:text-slate-500 ml-2 truncate">{item.nome}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => remover(item.codigo)}
                    className="text-slate-300 hover:text-red-500 transition opacity-0 group-hover:opacity-100 p-1"
                    aria-label={`Remover ${item.nome}`}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
