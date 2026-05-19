import { useState, useEffect } from 'react'
import { Trash2, UserPlus, Edit2, Users } from 'lucide-react'
import AdminHeader from '../components/AdminHeader'
import {
  listarUsuarios,
  criarUsuario,
  atualizarUsuario,
  excluirUsuario,
  type Usuario,
} from '../api/usuarios'
import { useAuth } from '../hooks/useAuth'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import type { Role } from '../types'

const ROLES: Role[] = ['operador', 'supervisor', 'admin']

const roleBadgeClass: Record<Role, string> = {
  operador: 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300',
  supervisor: 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  admin: 'bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
}

const roleLabels: Record<Role, string> = {
  operador: 'Operador',
  supervisor: 'Supervisor',
  admin: 'Admin',
}

interface ModalEdicao {
  usuario: Usuario
  password: string
  role: Role
  loading: boolean
  erro: string
}

function UserAvatar({ name, size = 'md' }: { name: string; size?: 'sm' | 'md' | 'lg' }) {
  const initials = name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()
  const sizeClass = size === 'sm' ? 'w-8 h-8 text-xs' : size === 'lg' ? 'w-12 h-12 text-base' : 'w-10 h-10 text-sm'
  const colors = [
    'bg-primary/10 text-primary dark:bg-primary/20',
    'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  ]
  const colorIdx = name.charCodeAt(0) % colors.length
  return (
    <div className={`${sizeClass} rounded-xl ${colors[colorIdx]} flex items-center justify-center font-bold shrink-0`}>
      {initials}
    </div>
  )
}

export default function Usuarios() {
  const { getUsername } = useAuth()

  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erroGeral, setErroGeral] = useState('')

  const [modal, setModal] = useState<ModalEdicao | null>(null)

  const [novoUsername, setNovoUsername] = useState('')
  const [novoNome, setNovoNome] = useState('')
  const [novoPassword, setNovoPassword] = useState('')
  const [novoRole, setNovoRole] = useState<Role>('operador')
  const [criando, setCriando] = useState(false)
  const [erroCriacao, setErroCriacao] = useState('')

  const [excluirUsuarioObj, setExcluirUsuarioObj] = useState<Usuario | null>(null)

  const meuUsername = getUsername()

  async function carregar() {
    try {
      const data = await listarUsuarios()
      setUsuarios(data)
      setCarregando(false)
    } catch {
      setErroGeral('Erro ao carregar usuários.')
      setCarregando(false)
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    carregar()
  }, [])

  async function handleCriar() {
    setErroCriacao('')
    if (!novoUsername.trim() || !novoNome.trim() || !novoPassword.trim()) {
      setErroCriacao('Preencha todos os campos.')
      return
    }
    setCriando(true)
    try {
      await criarUsuario({ username: novoUsername.trim(), nome_exibicao: novoNome.trim(), password: novoPassword, role: novoRole })
      setNovoUsername(''); setNovoNome(''); setNovoPassword(''); setNovoRole('operador')
      await carregar()
    } catch {
      setErroCriacao('Erro ao criar usuário.')
    } finally {
      setCriando(false)
    }
  }

  async function handleAtualizar() {
    if (!modal) return
    setModal(m => m ? { ...m, loading: true, erro: '' } : null)
    try {
      await atualizarUsuario(modal.usuario.id, { role: modal.role, ...(modal.password ? { password: modal.password } : {}) })
      setModal(null)
      await carregar()
    } catch {
      setModal(m => m ? { ...m, loading: false, erro: 'Erro ao atualizar.' } : null)
    }
  }

  async function handleConfirmarExcluir() {
    if (!excluirUsuarioObj) return
    try {
      await excluirUsuario(excluirUsuarioObj.id)
      setExcluirUsuarioObj(null)
      setCarregando(true)
      await carregar()
    } catch {
      setErroGeral('Erro ao excluir usuário.')
      setExcluirUsuarioObj(null)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center px-4 py-6 overflow-x-auto">

      {/* Modal de edição */}
      {modal && (
        <Modal
          open={!!modal}
          onClose={() => setModal(null)}
          title={`Editar: ${modal.usuario.nome_exibicao}`}
          actions={
            <>
              <Button variant="ghost" onClick={() => setModal(null)} fullWidth>Cancelar</Button>
              <Button onClick={handleAtualizar} loading={modal.loading} fullWidth>Salvar</Button>
            </>
          }
        >
          <div className="flex flex-col gap-4">
            <p className="text-xs text-slate-400 dark:text-slate-500">{modal.usuario.username}</p>
            <div>
              <label className="text-xs text-slate-500 dark:text-slate-400 mb-1.5 block">Nova senha (opcional)</label>
              <input
                type="password"
                className="w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Deixe em branco para não alterar"
                value={modal.password}
                onChange={(e) => setModal(m => m ? { ...m, password: e.target.value } : null)}
              />
            </div>
            <div>
              <label className="text-xs text-slate-500 dark:text-slate-400 mb-1.5 block">Permissão</label>
              <select
                className="w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                value={modal.role}
                onChange={(e) => setModal(m => m ? { ...m, role: e.target.value as Role } : null)}
              >
                {ROLES.map(r => <option key={r} value={r}>{roleLabels[r]}</option>)}
              </select>
            </div>
            {modal.erro && <p className="text-red-500 text-sm">{modal.erro}</p>}
          </div>
        </Modal>
      )}

      <AdminHeader titulo="Usuários" paginaAtual="usuarios" />

      <div className="w-full max-w-2xl flex flex-col gap-5">

        {/* Formulário de criação */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-primary/10 dark:bg-primary/20 flex items-center justify-center">
              <UserPlus size={20} className="text-primary" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-800 dark:text-slate-100">Novo usuário</h2>
              <p className="text-xs text-slate-400 dark:text-slate-500">Adicione um novo membro à equipe</p>
            </div>
          </div>
          <div className="flex flex-col gap-4">
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                className="w-full sm:flex-1 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Username"
                value={novoUsername}
                onChange={(e) => setNovoUsername(e.target.value)}
              />
              <input
                className="w-full sm:flex-1 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Nome de exibição"
                value={novoNome}
                onChange={(e) => setNovoNome(e.target.value)}
              />
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="password"
                className="w-full sm:flex-1 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Senha"
                value={novoPassword}
                onChange={(e) => setNovoPassword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCriar()}
              />
              <select
                className="w-full sm:w-auto border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                value={novoRole}
                onChange={(e) => setNovoRole(e.target.value as Role)}
              >
                {ROLES.map(r => <option key={r} value={r}>{roleLabels[r]}</option>)}
              </select>
              <Button onClick={handleCriar} loading={criando}>
                Criar
              </Button>
            </div>
            {erroCriacao && <p className="text-red-500 text-sm">{erroCriacao}</p>}
          </div>
        </div>

        {/* Lista de usuários */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-slate-100 dark:bg-slate-700 flex items-center justify-center">
              <Users size={20} className="text-slate-500 dark:text-slate-400" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-800 dark:text-slate-100">
                Equipe
              </h2>
              {!carregando && (
                <p className="text-xs text-slate-400 dark:text-slate-500">{usuarios.length} membro(s)</p>
              )}
            </div>
          </div>

          {erroGeral && <p className="text-red-500 text-sm mb-3">{erroGeral}</p>}
          {carregando && <p className="text-sm text-slate-400 dark:text-slate-500">Carregando...</p>}

          {!carregando && (
            <div className="flex flex-col gap-2">
              {usuarios.map(usuario => (
                <div key={usuario.id} className="flex justify-between items-center border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition group">
                  <div className="flex items-center gap-3 min-w-0">
                    <UserAvatar name={usuario.nome_exibicao} />
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 truncate">{usuario.nome_exibicao}</p>
                      <p className="text-xs text-slate-400 dark:text-slate-500 font-mono">{usuario.username}</p>
                    </div>
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full shrink-0 ${roleBadgeClass[usuario.role]}`}>
                      {roleLabels[usuario.role]}
                    </span>
                  </div>
                  <div className="flex gap-1 shrink-0 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition">
                    <button
                      onClick={() => setModal({
                        usuario,
                        password: '',
                        role: usuario.role,
                        loading: false,
                        erro: '',
                      })}
                      className="text-slate-400 hover:text-primary transition p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700"
                      aria-label={`Editar ${usuario.nome_exibicao}`}
                    >
                      <Edit2 size={14} />
                    </button>
                    <button
                      onClick={() => setExcluirUsuarioObj(usuario)}
                      disabled={usuario.username === meuUsername}
                      className="text-slate-400 hover:text-red-500 transition disabled:opacity-30 disabled:cursor-not-allowed p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
                      aria-label={`Excluir ${usuario.nome_exibicao}`}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modal Confirmar Exclusão */}
      <Modal
        open={!!excluirUsuarioObj}
        onClose={() => setExcluirUsuarioObj(null)}
        title={`Excluir "${excluirUsuarioObj?.nome_exibicao}"?`}
        variant="danger"
        actions={
          <>
            <Button variant="ghost" onClick={() => setExcluirUsuarioObj(null)}>Cancelar</Button>
            <Button variant="danger" onClick={handleConfirmarExcluir}>
              <Trash2 size={14} /> Excluir
            </Button>
          </>
        }
      >
        <p>Esta ação não pode ser desfeita. O usuário perderá acesso ao sistema.</p>
      </Modal>

    </div>
  )
}
