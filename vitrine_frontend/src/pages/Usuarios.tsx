import { useState, useEffect } from 'react'
import { Trash2 } from 'lucide-react'
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
  operador: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300',
  supervisor: 'bg-primary-lighter text-primary dark:bg-primary dark:text-primary-lighter',
  admin: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
}

interface ModalEdicao {
  usuario: Usuario
  password: string
  role: Role
  loading: boolean
  erro: string
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
    <div className="min-h-screen bg-gray-100 dark:bg-gray-950 flex flex-col items-center px-4 py-6">

      {/* Modal de edição */}
      {modal && (
        <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 px-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-5 w-full max-w-sm flex flex-col gap-4">
            <div>
              <p className="text-sm font-semibold text-gray-700 dark:text-gray-200">Editar usuário</p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{modal.usuario.nome_exibicao} ({modal.usuario.username})</p>
            </div>

            <div className="flex flex-col gap-3">
              <div>
                <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Nova senha (opcional)</label>
                <input
                  type="password"
                  className="w-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Deixe em branco para não alterar"
                  value={modal.password}
                  onChange={(e) => setModal(m => m ? { ...m, password: e.target.value } : null)}
                />
              </div>
              <div>
                <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Role</label>
                <select
                  className="w-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  value={modal.role}
                  onChange={(e) => setModal(m => m ? { ...m, role: e.target.value as Role } : null)}
                >
                  {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                </select>
              </div>
            </div>

            {modal.erro && <p className="text-red-500 text-sm">{modal.erro}</p>}

            <div className="flex gap-2">
              <Button variant="ghost" onClick={() => setModal(null)} fullWidth>Cancelar</Button>
              <Button onClick={handleAtualizar} loading={modal.loading} fullWidth>Salvar</Button>
            </div>
          </div>
        </div>
      )}

      <AdminHeader titulo="Usuários" paginaAtual="usuarios" />

      <div className="w-full max-w-2xl flex flex-col gap-5">

        {/* Formulário de criação */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-5">
          <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200 mb-4">Novo usuário</h2>
          <div className="flex flex-col gap-3">
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                className="w-full sm:flex-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Username"
                value={novoUsername}
                onChange={(e) => setNovoUsername(e.target.value)}
              />
              <input
                className="w-full sm:flex-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Nome de exibição"
                value={novoNome}
                onChange={(e) => setNovoNome(e.target.value)}
              />
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="password"
                className="w-full sm:flex-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Senha"
                value={novoPassword}
                onChange={(e) => setNovoPassword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCriar()}
              />
              <select
                className="w-full sm:w-auto border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                value={novoRole}
                onChange={(e) => setNovoRole(e.target.value as Role)}
              >
                {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
              <Button onClick={handleCriar} loading={criando}>
                Criar
              </Button>
            </div>
            {erroCriacao && <p className="text-red-500 text-sm">{erroCriacao}</p>}
          </div>
        </div>

        {/* Lista de usuários */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-5">
          <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200 mb-4">
            Usuários
            {!carregando && (
              <span className="text-gray-400 dark:text-gray-500 font-normal text-sm ml-2">({usuarios.length})</span>
            )}
          </h2>

          {erroGeral && <p className="text-red-500 text-sm mb-3">{erroGeral}</p>}
          {carregando && <p className="text-sm text-gray-400 dark:text-gray-500">Carregando...</p>}

          {!carregando && (
            <div className="flex flex-col gap-2">
              {usuarios.map(usuario => (
                <div key={usuario.id} className="flex justify-between items-center border dark:border-gray-700 rounded-lg px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div>
                      <p className="text-sm font-semibold text-gray-700 dark:text-gray-200">{usuario.nome_exibicao}</p>
                      <p className="text-xs text-gray-400 dark:text-gray-500">{usuario.username}</p>
                    </div>
                    <span className={`text-xs font-semibold px-2 py-1 rounded-full ${roleBadgeClass[usuario.role]}`}>
                      {usuario.role}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setModal({
                        usuario,
                        password: '',
                        role: usuario.role,
                        loading: false,
                        erro: '',
                      })}
                      className="text-sm text-gray-500 hover:text-primary transition"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => setExcluirUsuarioObj(usuario)}
                      disabled={usuario.username === meuUsername}
                      className="text-sm text-gray-300 hover:text-red-500 transition disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      Excluir
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
