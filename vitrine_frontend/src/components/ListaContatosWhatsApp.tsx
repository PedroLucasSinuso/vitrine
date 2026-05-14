import { useState, useEffect, useRef } from 'react'
import { listarContatos, criarContato, atualizarContato, removerContato } from '../api/whatsapp'
import type { WhatsAppContato } from '../api/whatsapp'
import { useToast } from '../hooks/useToast'

export default function ListaContatosWhatsApp() {
  const { toast } = useToast()
  const [contatos, setContatos] = useState<WhatsAppContato[]>([])
  const [loading, setLoading] = useState(true)
  const contatosRef = useRef(contatos)
  contatosRef.current = contatos
  const debounceTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({})

  useEffect(() => {
    listarContatos()
      .then(setContatos)
      .catch(() => toast({ type: 'error', message: 'Erro ao carregar contatos' }))
      .finally(() => setLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    return () => { Object.values(debounceTimers.current).forEach(clearTimeout) }
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
      }
    }, 600)
  }

  if (loading) {
    return <p className="text-sm text-gray-400 dark:text-gray-500">Carregando contatos...</p>
  }

  return (
    <div className="flex flex-col gap-2">
      {contatos.map((contato) => (
        <div key={contato.id} className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
          <input
            className="w-full sm:flex-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            value={contato.nome}
            onChange={(e) => handleUpdate(contato.id, 'nome', e.target.value)}
            placeholder="Nome"
          />
          <div className="flex items-center gap-2 w-full sm:flex-[2]">
            <input
              className="flex-1 min-w-0 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              value={contato.numero}
              onChange={(e) => handleUpdate(contato.id, 'numero', e.target.value)}
              placeholder="5522999999999"
            />
            <button
              onClick={() => handleRemover(contato.id)}
              className="text-red-500 hover:text-red-700 dark:hover:text-red-400 text-lg leading-none px-2 shrink-0"
              title="Remover contato"
            >
              ✕
            </button>
          </div>
        </div>
      ))}
      <button
        onClick={handleAdicionar}
        className="self-start text-xs bg-primary hover:bg-primary-hover text-white font-semibold px-4 py-2 rounded-lg transition"
      >
        + Adicionar
      </button>
    </div>
  )
}
