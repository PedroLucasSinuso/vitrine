import { useState, useEffect } from 'react'
import { listarContatosEmail, criarContatoEmail, atualizarContatoEmail, removerContatoEmail } from '../api/email'
import type { EmailContato } from '../api/email'
import { useToast } from '../hooks/useToast'

export default function ListaContatosEmail() {
  const { toast } = useToast()
  const [contatos, setContatos] = useState<EmailContato[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listarContatosEmail()
      .then(setContatos)
      .catch(() => toast({ type: 'error', message: 'Erro ao carregar contatos de email' }))
      .finally(() => setLoading(false))
  }, [])

  async function handleAdicionar() {
    try {
      const novo = await criarContatoEmail({ email: '', nome: '' })
      setContatos((prev) => [...prev, novo])
    } catch {
      toast({ type: 'error', message: 'Erro ao adicionar contato' })
    }
  }

  async function handleRemover(id: number) {
    try {
      await removerContatoEmail(id)
      setContatos((prev) => prev.filter((c) => c.id !== id))
    } catch {
      toast({ type: 'error', message: 'Erro ao remover contato' })
    }
  }

  async function handleUpdate(id: number, field: 'nome' | 'email', value: string) {
    const contato = contatos.find((c) => c.id === id)
    if (!contato) return
    const updated = { ...contato, [field]: value }
    try {
      const result = await atualizarContatoEmail(id, { nome: updated.nome, email: updated.email })
      setContatos((prev) => prev.map((c) => (c.id === id ? result : c)))
    } catch {
      toast({ type: 'error', message: 'Erro ao salvar contato' })
    }
  }

  if (loading) {
    return <p className="text-sm text-gray-400 dark:text-gray-500">Carregando contatos...</p>
  }

  return (
    <div className="flex flex-col gap-2">
      {contatos.map((contato) => (
        <div key={contato.id} className="flex items-center gap-2">
          <input
            className="flex-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            value={contato.nome}
            onChange={(e) => handleUpdate(contato.id, 'nome', e.target.value)}
            placeholder="Nome"
          />
          <input
            className="flex-[2] border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            value={contato.email}
            onChange={(e) => handleUpdate(contato.id, 'email', e.target.value)}
            placeholder="email@exemplo.com"
          />
          <button
            onClick={() => handleRemover(contato.id)}
            className="text-red-500 hover:text-red-700 dark:hover:text-red-400 text-lg leading-none px-2"
            title="Remover contato"
          >
            ✕
          </button>
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
