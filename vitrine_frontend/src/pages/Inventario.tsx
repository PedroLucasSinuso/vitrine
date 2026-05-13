import { useState, useRef, useEffect } from 'react'
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
  const [consolidado, setConsolidado] = useState(false)

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

  const { getUsername } = useAuth()
  const { toast } = useToast()

  useEffect(() => {
    getSessoesInventario()
      .then(setSessoes)
      .catch(() => setErro('Erro ao carregar sessões'))
      .finally(() => setLoadingSessoes(false))
  }, [])

  useEffect(() => {
    if (!sessaoAtiva) return
    const isCriador = sessaoAtiva.criado_por === getUsername()
    setConsolidado(isCriador)
    getItensInventario(sessaoAtiva.id, isCriador)
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
    try { navigator.vibrate?.(20) } catch {}
  }

  function handleVoltar() {
    scrollPosRef.current = window.scrollY
    setSessaoAtiva(null)
    setItens([])
    setConsolidado(false)
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
      }
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
    }
  }

  async function handleLimpar() {
    if (!sessaoAtiva) return
    try {
      await limparItensInventario(sessaoAtiva.id)
      setItens([])
      setConfirmarLimpar(false)
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

  async function handleToggleConsolidado() {
    if (!sessaoAtiva) return
    const novo = !consolidado
    setConsolidado(novo)
    if (novo) {
      try {
        const items = await getItensInventario(sessaoAtiva.id, true)
        setItens(items)
      } catch {
        setErro('Erro ao carregar consolidado')
      }
    } else {
      const items = await getItensInventario(sessaoAtiva.id)
      setItens(items)
    }
  }

  const totalItens = itens.reduce((acc, i) => acc + i.quantidade, 0)

  /* ─── Estado A: Seleção de sessão ─── */
  if (!sessaoAtiva) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-950 flex flex-col items-center px-4 py-6">
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
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-5">
                  <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200 mb-4">Sessões ativas</h2>
                  <div className="flex flex-col gap-2">
                    {sessoes.map(s => (
                      <button
                        key={s.id}
                        onClick={() => setSessaoAtiva(s)}
                        className="flex items-center justify-between border dark:border-gray-700 rounded-xl px-4 py-3 text-left hover:bg-primary-lighter dark:hover:bg-gray-700 transition"
                      >
                        <div>
                          <p className="font-semibold text-sm text-gray-800 dark:text-gray-100">{s.nome}</p>
                          <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
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
                    className="flex-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary uppercase"
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
              className="w-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </Modal>

        </div>
      </div>
    )
  }

  /* ─── Estado B/C: Bipagem / Consolidado ─── */
  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-950 flex flex-col items-center px-4 py-6">
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
            <button onClick={handleVoltar} className="text-sm text-gray-500 hover:text-primary transition shrink-0">
              ← Voltar
            </button>
            <div className="min-w-0">
              <h2 className="text-sm font-bold text-gray-800 dark:text-gray-100 truncate">{sessaoAtiva.nome}</h2>
              <p className="text-xs text-gray-400 dark:text-gray-500 font-mono">Código: {sessaoAtiva.codigo_convite}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {isSupervisor && (
              <button
                onClick={handleToggleConsolidado}
                className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${consolidado ? 'bg-primary text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300'}`}
              >
                {consolidado ? 'Consolidado' : 'Meus itens'}
              </button>
            )}
            {isSupervisor && (
              <button onClick={() => setConfirmarEncerrar(true)} className="text-xs text-red-500 hover:text-red-700 transition flex items-center gap-1">
                <LogOut size={12} /> Encerrar
              </button>
            )}
          </div>
        </div>

        {/* Input de bipagem (oculto no consolidado) */}
        {!consolidado && (
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-5">
            <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200 mb-4">Bipar produtos</h2>
            <div className="flex gap-2">
              <input
                ref={inputRef}
                aria-label="Código do produto"
                className="flex-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Digite ou bipe o código"
                onKeyDown={handleKeyDown}
                autoFocus
              />
              <button
                onClick={() => setCamera(true)}
                className="md:hidden bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 px-3 py-2 rounded-lg transition"
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
        )}

        {/* Lista de itens */}
        {itens.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-5">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200">
                {consolidado ? 'Consolidado' : 'Contagem'}
                <span className="text-gray-400 dark:text-gray-500 font-normal text-sm ml-2">
                  ({itens.length} produtos · {totalItens} unidades)
                </span>
              </h2>
              <div className="flex gap-2">
                {!consolidado && (
                  <button onClick={() => setConfirmarLimpar(true)} className="text-sm text-gray-400 hover:text-red-500 transition flex items-center gap-1">
                    <Trash2 size={14} /> Limpar
                  </button>
                )}
                <button onClick={handleExportarTxt} className="text-sm text-gray-500 hover:text-primary transition flex items-center gap-1">
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
                  onClick={() => !consolidado && setEditSheetItem(item)}
                  className="flex justify-between items-center border dark:border-gray-700 rounded-lg px-4 py-2 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-750 transition"
                >
                  <div className="min-w-0 flex-1">
                    <span className="text-sm font-semibold text-gray-700 dark:text-gray-200">{item.codigo}</span>
                    <span className="text-xs text-gray-400 dark:text-gray-500 ml-2 truncate block sm:inline">
                      {item.nome} {item.grupo && item.familia ? `• ${item.grupo} / ${item.familia}` : ''}
                    </span>
                  </div>
                  {consolidado ? (
                    <span className="text-sm font-semibold text-gray-700 dark:text-gray-200 w-14 text-center">{item.quantidade}</span>
                  ) : (
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={(e) => { e.stopPropagation(); ajustarQuantidade(item.codigo, -1) }}
                        className="w-7 h-7 rounded-full bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 font-bold transition flex items-center justify-center"
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
                        className="w-14 text-center text-sm font-semibold text-gray-700 dark:text-gray-200 bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg px-1 py-1 focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                      <button
                        onClick={(e) => { e.stopPropagation(); ajustarQuantidade(item.codigo, 1) }}
                        className="w-7 h-7 rounded-full bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 font-bold transition flex items-center justify-center"
                      >
                        <Plus size={14} />
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {!consolidado && itens.length === 0 && (
          <p className="text-sm text-gray-400 dark:text-gray-500 text-center">Nenhum item bipado ainda</p>
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
              <p className="font-semibold text-gray-800 dark:text-gray-100">{editSheetItem.codigo}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{editSheetItem.nome}</p>
              <div className="flex items-center gap-6 mt-5 justify-center">
                <button
                  onClick={() => ajustarQuantidade(editSheetItem.codigo, -1)}
                  className="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 font-bold transition flex items-center justify-center"
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
                  className="w-20 text-center text-xl font-bold text-gray-800 dark:text-gray-100 bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                  autoFocus
                />
                <button
                  onClick={() => ajustarQuantidade(editSheetItem.codigo, 1)}
                  className="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 font-bold transition flex items-center justify-center"
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
