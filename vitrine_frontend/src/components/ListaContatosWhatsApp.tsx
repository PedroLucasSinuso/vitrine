import { useState, useEffect, useRef } from 'react'
import { listarContatos, criarContato, atualizarContato, removerContato } from '../api/whatsapp'
import type { WhatsAppContato } from '../api/whatsapp'
import { useToast } from '../hooks/useToast'
import { Plus, X, Loader2 } from 'lucide-react'

export default function ListaContatosWhatsApp() {
  const { toast } = useToast()
  const [contatos, setContatos] = useState<WhatsAppContato[]>([])
  const [loading, setLoading] = useState(true)
  const [savingIds, setSavingIds] = useState<Set<number>>(new Set())
  const contatosRef = useRef(contatos)

  useEffect(() => {
    contatosRef.current = contatos
  }, [contatos])
  const debounceTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({})

  useEffect(() => {
    listarContatos()
      .then(setContatos)
      .catch(() => toast({ type: 'error', message: 'Erro ao carregar contatos' }))
      .finally(() => setLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const timers = debounceTimers.current
    return () => { Object.values(timers).forEach(clearTimeout) }
  }, [])

  async function handleAdicionar() {
    try {
      const novo = await criarContato({ numero: '', nome: '' })
      setContatos((prev) => [...prev, novo])
    } catch {
      toast({ type: 'error', message: 'Erro ao adicionar contato' })
    }
  }

  async function handleRemover(id: number) {
    try {
      await removerContato(id)
      setContatos((prev) => prev.filter((c) => c.id !== id))
    } catch {
      toast({ type: 'error', message: 'Erro ao remover contato' })
    }
  }

  function handleUpdate(id: number, field: 'nome' | 'numero', value: string) {
    setContatos((prev) =>
      prev.map((c) => (c.id === id ? { ...c, [field]: value } : c))
    )
    setSavingIds((prev) => new Set(prev).add(id))
    const key = `${id}-${field}`
    clearTimeout(debounceTimers.current[key])
    debounceTimers.current[key] = setTimeout(async () => {
      delete debounceTimers.current[key]
      const contato = contatosRef.current.find((c) => c.id === id)
      if (!contato) return
      try {
        const result = await atualizarContato(id, { nome: contato.nome, numero: contato.numero })
        setContatos((prev) => prev.map((c) => (c.id === id ? result : c)))
      } catch {
        toast({ type: 'error', message: 'Erro ao salvar contato' })
      } finally {
        setSavingIds((prev) => {
          const next = new Set(prev)
          next.delete(id)
          return next
        })
      }
    }, 600)
  }

  if (loading) {
    return <p className="text-xs text-slate-400 dark:text-slate-500">Carregando contatos...</p>
  }

  return (
    <div className="flex flex-col gap-2">
      {/* Column headers */}
      <div className="hidden sm:grid sm:grid-cols-[1fr_1.5fr_auto] gap-2 px-1">
        <span className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Nome</span>
        <span className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Número</span>
        <span className="w-7" />
      </div>

      {contatos.map((contato) => (
        <div key={contato.id} className="flex flex-col sm:grid sm:grid-cols-[1fr_1.5fr_auto] gap-2 items-center">
          <input
            className="w-full border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-transparent transition"
            value={contato.nome}
            onChange={(e) => handleUpdate(contato.id, 'nome', e.target.value)}
            placeholder="Nome do contato"
          />
          <input
            className="w-full border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-transparent transition font-mono"
            value={contato.numero}
            onChange={(e) => handleUpdate(contato.id, 'numero', e.target.value)}
            placeholder="5522999999999"
          />
          {savingIds.has(contato.id) ? (
            <div className="w-7 flex items-center justify-center self-end sm:self-center">
              <Loader2 size={14} className="animate-spin text-primary" />
            </div>
          ) : (
            <button
              onClick={() => handleRemover(contato.id)}
              className="text-slate-300 hover:text-red-500 dark:hover:text-red-400 transition p-1 rounded-md hover:bg-red-50 dark:hover:bg-red-900/20 self-end sm:self-center"
              title="Remover contato"
            >
              <X size={14} />
            </button>
          )}
        </div>
      ))}

      <button
        onClick={handleAdicionar}
        className="inline-flex items-center gap-1.5 text-xs text-primary hover:text-primary-hover font-medium px-3 py-1.5 rounded-lg hover:bg-primary/5 transition self-start mt-1"
      >
        <Plus size={13} /> Adicionar contato
      </button>
    </div>
  )
}
