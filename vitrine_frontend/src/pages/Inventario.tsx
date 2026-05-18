import { useState, useRef, useEffect, useCallback } from 'react'
import * as XLSX from 'xlsx'
import { Camera, Plus, Minus, Download, Trash2, LogOut, Check } from 'lucide-react'
import { buscarProduto } from '../api/produtos'
import AdminHeader from '../components/AdminHeader'
import LeitorCodigo from '../components/LeitorCodigo'
import { useAuth } from '../hooks/useAuth'
import { useToast } from '../hooks/useToast'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import Skeleton from '../components/ui/Skeleton'
import {
  getSessoesInventario,
  criarSessaoInventario,
  entrarSessaoInventario,
  encerrarSessaoInventario,
  getItensInventario,
  adicionarItemInventario,
  atualizarItemInventario,
  limparItensInventario,
  getConsolidadoGeral,
} from '../api/admin'
import type { SessaoInventario, ItemInventario } from '../types/inventario'

export default function Inventario() {
  const { getRole } = useAuth()
  const role = getRole()
  const isSupervisor = role === 'supervisor' || role === 'admin'

  const [sessoes, setSessoes] = useState<SessaoInventario[]>([])
  const [sessaoAtiva, setSessaoAtiva] = useState<SessaoInventario | null>(null)
  const [itens, setItens] = useState<ItemInventario[]>([])

  const [erro, setErro] = useState('')
  const [camera, setCamera] = useState(false)
  const [loadingSessoes, setLoadingSessoes] = useState(true)
  const [editando, setEditando] = useState<Record<string, string>>({})
  const [novaSessaoModal, setNovaSessaoModal] = useState(false)
  const [novaSessaoNome, setNovaSessaoNome] = useState('')
  const [criandoSessao, setCriandoSessao] = useState(false)
  const [confirmarEncerrar, setConfirmarEncerrar] = useState(false)
  const [confirmarLimpar, setConfirmarLimpar] = useState(false)
  const [editSheetItem, setEditSheetItem] = useState<ItemInventario | null>(null)
  const [scanFeedback, setScanFeedback] = useState<string | null>(null)
  const processando = useRef<Set<string>>(new Set())
  const inputRef = useRef<HTMLInputElement>(null)
  const conviteRef = useRef<HTMLInputElement>(null)
  const scrollPosRef = useRef(0)
  const feedbackTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const { toast } = useToast()

  // Consolidated data from all sessions (auto-refreshed)
  const [consolidadoItems, setConsolidadoItems] = useState<ItemInventario[]>([])
  const [consolidadoLoading, setConsolidadoLoading] = useState(false)

  const fetchConsolidado = useCallback(async () => {
    if (!isSupervisor) return
    setConsolidadoLoading(true)
    try {
      const items = await getConsolidadoGeral()
      setConsolidadoItems(items)
    } catch { /* ignore */ }
    finally { setConsolidadoLoading(false) }
  }, [isSupervisor])

  useEffect(() => {
    if (sessaoAtiva && isSupervisor) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- Mount/dependency-triggered fetch
      fetchConsolidado()
    }
  }, [sessaoAtiva, isSupervisor, fetchConsolidado])

  useEffect(() => {
    getSessoesInventario()
      .then(setSessoes)
      .catch(() => setErro('Erro ao carregar sessões'))
      .finally(() => setLoadingSessoes(false))
  }, [])

  useEffect(() => {
    if (!sessaoAtiva) return
    getItensInventario(sessaoAtiva.id, false)
      .then(setItens)
      .catch(() => setErro('Erro ao carregar itens'))
  }, [sessaoAtiva])

  useEffect(() => {
    if (!sessaoAtiva || scrollPosRef.current <= 0) return
    requestAnimationFrame(() => {
      window.scrollTo({ top: scrollPosRef.current, behavior: 'auto' })
      scrollPosRef.current = 0
    })
  }, [sessaoAtiva])

  function mostrarFeedback(nome: string) {
    setScanFeedback(null)
    if (feedbackTimer.current) clearTimeout(feedbackTimer.current)
    requestAnimationFrame(() => {
      setScanFeedback(nome)
      feedbackTimer.current = setTimeout(() => setScanFeedback(null), 700)
    })
  }

  function haptico() {
    try { navigator.vibrate?.(20) } catch { /* vibrate not supported */ }
  }

  function handleVoltar() {
    scrollPosRef.current = window.scrollY
    setSessaoAtiva(null)
    setItens([])
    setEditando({})
    setCamera(false)
    getSessoesInventario().then(setSessoes).catch(() => {})
  }

  async function handleConsolidadoTxt() {
    setErro('')
    try {
      const itens = await getConsolidadoGeral()
      if (itens.length === 0) { setErro('Nenhum item encontrado nas sessões.'); return }
      const linhas = itens.map(i => `${i.codigo};${i.quantidade}`).join('\n')
      const bom = "\uFEFF"
      const blob = new Blob([bom + linhas], { type: 'text/plain;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `consolidado_geral_${new Date().toISOString().slice(0, 10)}.txt`
      link.click()
      URL.revokeObjectURL(url)
      toast({ type: 'success', message: 'TXT consolidado baixado!' })
    } catch {
      setErro('Erro ao gerar relatório consolidado')
    }
  }

  async function handleConsolidadoExcel() {
    setErro('')
    try {
      const itens = await getConsolidadoGeral()
      if (itens.length === 0) { setErro('Nenhum item encontrado nas sessões.'); return }
      const data = itens.map(i => ({ código: i.codigo, produto: i.nome, grupo: i.grupo, família: i.familia, quantidade: i.quantidade }))
      const ws = XLSX.utils.json_to_sheet(data)
      const wb = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(wb, ws, 'Consolidado Geral')
      XLSX.writeFile(wb, `consolidado_geral_${new Date().toISOString().slice(0, 10)}.xlsx`)
      toast({ type: 'success', message: 'Excel consolidado baixado!' })
    } catch {
      setErro('Erro ao gerar relatório consolidado')
    }
  }

  async function handleCriarSessao() {
    if (!novaSessaoNome.trim()) return
    setCriandoSessao(true)
    try {
      const s = await criarSessaoInventario(novaSessaoNome.trim())
      setSessoes(prev => [s, ...prev])
      setSessaoAtiva(s)
      setNovaSessaoModal(false)
      setNovaSessaoNome('')
    } catch {
      setErro('Erro ao criar sessão')
    } finally {
      setCriandoSessao(false)
    }
  }

  async function handleEntrarSessao() {
    const codigo = conviteRef.current?.value?.trim().toUpperCase()
    if (!codigo) return
    try {
      const s = await entrarSessaoInventario(codigo)
      setSessaoAtiva(s)
    } catch {
      setErro('Sessão não encontrada')
    }
  }

  async function handleEncerrarSessao() {
    if (!sessaoAtiva) return
    try {
      await encerrarSessaoInventario(sessaoAtiva.id)
      setConfirmarEncerrar(false)
      handleVoltar()
    } catch {
      setErro('Erro ao encerrar sessão')
    }
  }

  async function handleCodigo(codigo: string) {
    if (!sessaoAtiva) return
    setErro('')
    const codigoLimpo = codigo.trim()
    if (!codigoLimpo) return

    if (processando.current.has(codigoLimpo)) return
    processando.current.add(codigoLimpo)

    try {
      const existente = itens.find(i => i.codigo === codigoLimpo)
      if (existente) {
        setItens(prev => prev.map(i =>
          i.codigo === codigoLimpo ? { ...i, quantidade: i.quantidade + 1 } : i
        ))
        await adicionarItemInventario(sessaoAtiva.id, { codigo: codigoLimpo, nome: existente.nome, grupo: existente.grupo, familia: existente.familia })
        if (inputRef.current) inputRef.current.value = ''
        haptico()
        mostrarFeedback(existente.nome)
        return
      }

      const produto = await buscarProduto(codigoLimpo)
      const internalCode = produto.codigo_chamada

      setItens(prev => {
        const jaExiste = prev.find(i => i.codigo === internalCode)
        if (jaExiste) {
          return prev.map(i => i.codigo === internalCode ? { ...i, quantidade: i.quantidade + 1 } : i)
        }
        return [...prev, { codigo: internalCode, nome: produto.nome, grupo: produto.grupo, familia: produto.familia, quantidade: 1 }]
      })

      await adicionarItemInventario(sessaoAtiva.id, { codigo: internalCode, nome: produto.nome, grupo: produto.grupo, familia: produto.familia })
      if (inputRef.current) inputRef.current.value = ''
      haptico()
      mostrarFeedback(produto.nome)
      fetchConsolidado()
    } catch (e: unknown) {
      const error = e as { response?: { status?: number } }
      let msg = 'Erro ao consultar.'
      if (error.response?.status === 404) msg = 'Produto não encontrado.'
      else if (error.response?.status === 400) msg = 'Código inválido.'
      toast({ type: 'error', message: msg })
    } finally {
      processando.current.delete(codigoLimpo)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') handleCodigo((e.target as HTMLInputElement).value)
  }

  function ajustarQuantidade(codigo: string, delta: number) {
    if (!sessaoAtiva) return
    setItens(prev => prev
      .map(i => i.codigo === codigo ? { ...i, quantidade: Math.max(0, i.quantidade + delta) } : i)
      .filter(i => i.quantidade > 0)
    )
    const item = itens.find(i => i.codigo === codigo)
    if (item) {
      const novaQtd = Math.max(0, item.quantidade + delta)
      if (novaQtd > 0) {
        atualizarItemInventario(sessaoAtiva.id, codigo, novaQtd).catch(() => {})
      } else {
        atualizarItemInventario(sessaoAtiva.id, codigo, 0).catch(() => {})
      }
      fetchConsolidado()
    }
  }

  function definirQuantidade(codigo: string, valor: string) {
    if (!sessaoAtiva) return
    setEditando(prev => { const n = { ...prev }; delete n[codigo]; return n })
    const n = parseInt(valor, 10)
    if (isNaN(n) || n < 0) return
    setItens(prev => prev
      .map(i => i.codigo === codigo ? { ...i, quantidade: n } : i)
      .filter(i => i.quantidade > 0)
    )
    if (n > 0) {
      atualizarItemInventario(sessaoAtiva.id, codigo, n).catch(() => {})
    } else {
      atualizarItemInventario(sessaoAtiva.id, codigo, 0).catch(() => {})
    }
    fetchConsolidado()
  }

  async function handleLimpar() {
    if (!sessaoAtiva) return
    try {
      await limparItensInventario(sessaoAtiva.id)
      setItens([])
      setConfirmarLimpar(false)
      fetchConsolidado()
    } catch {
      setErro('Erro ao limpar itens')
    }
  }

  function handleExportarTxt() {
    if (itens.length === 0) return
    const linhas = itens.map(i => `${i.codigo};${i.quantidade}`).join('\n')
    const bom = "\uFEFF"
    const blob = new Blob([bom + linhas], { type: 'text/plain;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `inventario_${new Date().toISOString().slice(0, 10)}.txt`
    link.click()
    URL.revokeObjectURL(url)
  }

  function handleExportarExcel() {
    if (itens.length === 0) return
    const data = itens.map(i => ({ código: i.codigo, grupo: i.grupo, família: i.familia, produto: i.nome }))
    const ws = XLSX.utils.json_to_sheet(data)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Inventário')
    XLSX.writeFile(wb, `inventario_${new Date().toISOString().slice(0, 10)}.xlsx`)
  }

  const totalItens = itens.reduce((acc, i) => acc + i.quantidade, 0)
  const totalConsolidado = consolidadoItems.reduce((acc, i) => acc + i.quantidade, 0)

  /* ─── Estado A: Seleção de sessão ─── */
  if (!sessaoAtiva) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center px-4 py-6 overflow-x-hidden">
        <AdminHeader titulo="Inventário" paginaAtual="inventario" />
        <div className="w-full max-w-2xl flex flex-col gap-5">

          {erro && <p className="text-red-500 text-sm" role="alert">{erro}</p>}

          {loadingSessoes ? (
            <div className="flex flex-col gap-3">
              <Skeleton variant="card" />
              <Skeleton variant="card" />
            </div>
          ) : (
            <>
              {sessoes.length > 0 && (
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-5">
                  <h2 className="text-base font-semibold text-slate-700 dark:text-slate-200 mb-4">Sessões ativas</h2>
                  <div className="flex flex-col gap-2">
                    {sessoes.map(s => (
                      <button
                        key={s.id}
                        onClick={() => setSessaoAtiva(s)}
                        className="flex items-center justify-between border dark:border-slate-700 rounded-xl px-4 py-3 text-left hover:bg-primary-lighter dark:hover:bg-slate-700 transition"
                      >
                        <div>
                          <p className="font-semibold text-sm text-slate-800 dark:text-slate-100">{s.nome}</p>
                          <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">
                            Código: <span className="font-mono font-bold text-primary">{s.codigo_convite}</span>
                            {' · '}{s.total_operadores} operador(es) · {s.total_itens} item(ns)
                          </p>
                        </div>
                        <span className="text-xs text-primary font-semibold">Entrar →</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex flex-col sm:flex-row gap-3">
                {isSupervisor && (
                  <Button onClick={() => setNovaSessaoModal(true)} fullWidth>
                    <Plus size={16} /> Nova Sessão
                  </Button>
                )}
                <div className="flex gap-2 flex-1">
                  <input
                    ref={conviteRef}
                    placeholder="Código da sessão"
                    className="flex-1 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary uppercase"
                    onKeyDown={(e) => e.key === 'Enter' && handleEntrarSessao()}
                  />
                  <Button onClick={handleEntrarSessao}>
                    Entrar
                  </Button>
                </div>
              </div>

              {isSupervisor && (
                <div className="flex gap-2">
                  <Button variant="outline" onClick={handleConsolidadoTxt} fullWidth>
                    <Download size={14} /> TXT Consolidado
                  </Button>
                  <Button onClick={handleConsolidadoExcel} fullWidth>
                    <Download size={14} /> Excel Consolidado
                  </Button>
                </div>
              )}
            </>
          )}

          {/* Modal Nova Sessão */}
          <Modal
            open={novaSessaoModal}
            onClose={() => { setNovaSessaoModal(false); setNovaSessaoNome('') }}
            title="Nova Sessão"
            actions={
              <>
                <Button variant="ghost" onClick={() => { setNovaSessaoModal(false); setNovaSessaoNome('') }}>
                  Cancelar
                </Button>
                <Button onClick={handleCriarSessao} loading={criandoSessao}>
                  Criar
                </Button>
              </>
            }
          >
            <input
              autoFocus
              value={novaSessaoNome}
              onChange={(e) => setNovaSessaoNome(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCriarSessao()}
              placeholder="Nome da sessão"
              className="w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </Modal>

        </div>
      </div>
    )
  }

  /* ─── Estado B/C: Bipagem / Consolidado ─── */
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center px-4 py-6 overflow-x-hidden">
      {camera && (
        <LeitorCodigo
          continuo
          onLeitura={(codigo) => { handleCodigo(codigo) }}
          onFechar={() => setCamera(false)}
        />
      )}

      <AdminHeader titulo="Inventário" paginaAtual="inventario" />

      <div className="w-full max-w-2xl flex flex-col gap-5">

        {/* Info da sessão */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-3 min-w-0">
            <button onClick={handleVoltar} className="text-sm text-slate-500 hover:text-primary transition shrink-0">
              ← Voltar
            </button>
            <div className="min-w-0">
              <h2 className="text-sm font-bold text-slate-800 dark:text-slate-100 truncate">{sessaoAtiva.nome}</h2>
              <p className="text-xs text-slate-400 dark:text-slate-500 font-mono">Código: {sessaoAtiva.codigo_convite}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {isSupervisor && (
              <button onClick={() => setConfirmarEncerrar(true)} className="text-xs text-red-500 hover:text-red-700 transition flex items-center gap-1">
                <LogOut size={12} /> Encerrar
              </button>
            )}
          </div>
        </div>

        {/* Input de bipagem */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-5">
            <h2 className="text-base font-semibold text-slate-700 dark:text-slate-200 mb-4">Bipar produtos</h2>
            <div className="flex gap-2">
              <input
                ref={inputRef}
                aria-label="Código do produto"
                className="flex-1 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Digite ou bipe o código"
                onKeyDown={handleKeyDown}
                autoFocus
              />
              <button
                onClick={() => setCamera(true)}
                className="md:hidden bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-gray-600 text-slate-700 dark:text-slate-300 px-3 py-2 rounded-lg transition"
                aria-label="Ler código de barras"
              >
                <Camera size={18} />
              </button>
            </div>
            {scanFeedback && (
              <div className="mt-2 flex items-center gap-2 text-green-600 dark:text-green-400 text-sm font-medium animate-fade-in-up">
                <Check size={16} /> {scanFeedback}
              </div>
            )}
            {erro && <p className="text-red-500 text-sm mt-2" role="alert">{erro}</p>}
          </div>

        {/* Lista de itens */}
        {itens.length > 0 && (
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-5">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-base font-semibold text-slate-700 dark:text-slate-200">
                Contagem
                <span className="text-slate-400 dark:text-slate-500 font-normal text-sm ml-2">
                  ({itens.length} produtos · {totalItens} unidades)
                </span>
              </h2>
              <div className="flex gap-2">
                <button onClick={() => setConfirmarLimpar(true)} className="text-sm text-slate-400 hover:text-red-500 transition flex items-center gap-1">
                  <Trash2 size={14} /> Limpar
                </button>
                <button onClick={handleExportarTxt} className="text-sm text-slate-500 hover:text-primary transition flex items-center gap-1">
                  <Download size={14} /> TXT
                </button>
                <Button size="sm" onClick={handleExportarExcel}>
                  <Download size={14} /> Excel
                </Button>
              </div>
            </div>

            <div className="flex flex-col gap-2">
              {itens.map(item => (
                <div
                  key={item.codigo}
                  onClick={() => setEditSheetItem(item)}
                  className="flex justify-between items-center border dark:border-slate-700 rounded-lg px-4 py-2 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50 transition"
                >
                  <div className="min-w-0 flex-1">
                    <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">{item.codigo}</span>
                    <span className="text-xs text-slate-400 dark:text-slate-500 ml-2 truncate block sm:inline">
                      {item.nome} {item.grupo && item.familia ? `• ${item.grupo} / ${item.familia}` : ''}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={(e) => { e.stopPropagation(); ajustarQuantidade(item.codigo, -1) }}
                      className="w-7 h-7 rounded-full bg-slate-50 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-600 dark:text-slate-300 font-bold transition flex items-center justify-center"
                    >
                      <Minus size={14} />
                    </button>
                    <input
                      type="number"
                      min="0"
                      value={editando[item.codigo] ?? item.quantidade}
                      onChange={(e) => setEditando(prev => ({ ...prev, [item.codigo]: e.target.value }))}
                      onBlur={(e) => definirQuantidade(item.codigo, e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') definirQuantidade(item.codigo, (e.target as HTMLInputElement).value)
                      }}
                      onClick={(e) => e.stopPropagation()}
                      className="w-14 text-center text-sm font-semibold text-slate-700 dark:text-slate-200 bg-transparent border border-slate-300 dark:border-slate-600 rounded-lg px-1 py-1 focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                    <button
                      onClick={(e) => { e.stopPropagation(); ajustarQuantidade(item.codigo, 1) }}
                      className="w-7 h-7 rounded-full bg-slate-50 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-600 dark:text-slate-300 font-bold transition flex items-center justify-center"
                    >
                      <Plus size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {itens.length === 0 && (
          <p className="text-sm text-slate-400 dark:text-slate-500 text-center">Nenhum item bipado ainda</p>
        )}

        {/* Consolidado Geral — auto-refreshed */}
        {isSupervisor && (
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-5">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-base font-semibold text-slate-700 dark:text-slate-200">
                Consolidado Geral
                <span className="text-slate-400 dark:text-slate-500 font-normal text-sm ml-2">
                  ({consolidadoItems.length} produtos · {totalConsolidado} unidades)
                </span>
              </h2>
              {consolidadoLoading && (
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Atualizando...
                </span>
              )}
            </div>

            {consolidadoItems.length === 0 && !consolidadoLoading && (
              <p className="text-sm text-slate-400 dark:text-slate-500 text-center py-4">Nenhum item em nenhuma sessão</p>
            )}

            {consolidadoItems.length > 0 && (
              <div className="flex flex-col gap-1.5 max-h-60 overflow-y-auto">
                {consolidadoItems.slice(0, 20).map(item => (
                  <div key={item.codigo} className="flex justify-between items-center px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-700/50">
                    <div className="min-w-0 flex-1">
                      <span className="text-xs font-mono text-slate-500 dark:text-slate-400">{item.codigo}</span>
                      <span className="text-xs text-slate-400 dark:text-slate-500 ml-2 truncate">{item.nome}</span>
                    </div>
                    <span className="text-sm font-bold text-slate-700 dark:text-slate-200 w-12 text-right">{item.quantidade}</span>
                  </div>
                ))}
                {consolidadoItems.length > 20 && (
                  <p className="text-xs text-slate-400 dark:text-slate-500 text-center py-2">
                    +{consolidadoItems.length - 20} produtos
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Modal Editar Item (bottom-sheet) */}
        <Modal
          open={!!editSheetItem}
          onClose={() => setEditSheetItem(null)}
          title="Editar quantidade"
          actions={
            <Button variant="ghost" onClick={() => setEditSheetItem(null)}>
              Fechar
            </Button>
          }
        >
          {editSheetItem && (
            <div>
              <p className="font-semibold text-slate-800 dark:text-slate-100">{editSheetItem.codigo}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{editSheetItem.nome}</p>
              <div className="flex items-center gap-6 mt-5 justify-center">
                <button
                  onClick={() => ajustarQuantidade(editSheetItem.codigo, -1)}
                  className="w-12 h-12 rounded-full bg-slate-50 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-gray-600 text-slate-600 dark:text-slate-300 font-bold transition flex items-center justify-center"
                >
                  <Minus size={22} />
                </button>
                <input
                  type="number"
                  min="0"
                  value={editando[editSheetItem.codigo] ?? editSheetItem.quantidade}
                  onChange={(e) => setEditando(prev => ({ ...prev, [editSheetItem.codigo]: e.target.value }))}
                  onBlur={(e) => {
                    definirQuantidade(editSheetItem.codigo, e.target.value)
                    setEditSheetItem(null)
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      definirQuantidade(editSheetItem.codigo, (e.target as HTMLInputElement).value)
                      setEditSheetItem(null)
                    }
                  }}
                  className="w-20 text-center text-xl font-bold text-slate-800 dark:text-slate-100 bg-transparent border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                  autoFocus
                />
                <button
                  onClick={() => ajustarQuantidade(editSheetItem.codigo, 1)}
                  className="w-12 h-12 rounded-full bg-slate-50 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-gray-600 text-slate-600 dark:text-slate-300 font-bold transition flex items-center justify-center"
                >
                  <Plus size={22} />
                </button>
              </div>
            </div>
          )}
        </Modal>

        {/* Modal Confirmar Encerrar */}
        <Modal
          open={confirmarEncerrar}
          onClose={() => setConfirmarEncerrar(false)}
          title={`Encerrar "${sessaoAtiva.nome}"?`}
          variant="danger"
          actions={
            <>
              <Button variant="ghost" onClick={() => setConfirmarEncerrar(false)}>Cancelar</Button>
              <Button variant="danger" onClick={handleEncerrarSessao}>
                <LogOut size={14} /> Encerrar
              </Button>
            </>
          }
        >
          <p>Tem certeza? Os operadores não poderão mais bipar itens nesta sessão.</p>
        </Modal>

        {/* Modal Confirmar Limpar */}
        <Modal
          open={confirmarLimpar}
          onClose={() => setConfirmarLimpar(false)}
          title="Limpar todos os itens?"
          variant="danger"
          actions={
            <>
              <Button variant="ghost" onClick={() => setConfirmarLimpar(false)}>Cancelar</Button>
              <Button variant="danger" onClick={handleLimpar}>
                <Trash2 size={14} /> Limpar
              </Button>
            </>
          }
        >
          <p>Todos os itens desta sessão serão removidos permanentemente.</p>
        </Modal>

      </div>
    </div>
  )
}
