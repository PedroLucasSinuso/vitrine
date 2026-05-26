import { useState, useEffect } from 'react'
import { Trash2, UserPlus, Edit2 } from 'lucide-react'
import {
  listarUsuarios,
  criarUsuario,
  atualizarUsuario,
  excluirUsuario,
  type Usuario,
} from '../api/usuarios'
import { useAuth } from '../hooks/useAuth'
import PageContainer from '../components/layout/PageContainer'
import PageSection from '../components/layout/PageSection'
import Card from '../components/ui/Card'
import UserAvatar from '../components/ui/UserAvatar'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import Badge from '../components/ui/Badge'
import EmptyState from '../components/ui/EmptyState'
import type { Role } from '../types'

const ROLES: Role[] = ['operador', 'supervisor', 'admin']

const roleBadgeVariant: Record<Role, 'default' | 'info' | 'warning' | 'success'> = {
  operador: 'default',
  supervisor: 'info',
  admin: 'warning',
}

const roleLabels: Record<Role, string> = {
  operador: 'Operador',
  supervisor: 'Supervisor',
  admin: 'Admin',
}

const ROLES_CONFIG: { value: Role; label: string; desc: string }[] = [
  { value: 'operador', label: 'Operador', desc: 'Acesso a busca e inventário' },
  { value: 'supervisor', label: 'Supervisor', desc: 'Acesso a relatórios e etiquetas' },
  { value: 'admin', label: 'Admin', desc: 'Acesso total ao sistema' },
]

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

  // Novo usuário form
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

  useEffect(() => { carregar() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  async function handleCriar() {
    setErroCriacao('')
    if (!novoUsername.trim() || !novoNome.trim() || !novoPassword.trim()) {
      setErroCriacao('Preencha todos os campos.')
      return
    }
    setCriando(true)
    try {
      await criarUsuario({
        username: novoUsername.trim(),
        nome_exibicao: novoNome.trim(),
        password: novoPassword,
        role: novoRole,
      })
      setNovoUsername('')
      setNovoNome('')
      setNovoPassword('')
      setNovoRole('operador')
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
      await atualizarUsuario(modal.usuario.id, {
        role: modal.role,
        ...(modal.password ? { password: modal.password } : {}),
      })
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
    <PageContainer maxWidth="md">
      {/* Modal de edição */}
      {modal && (
        <Modal
          open={!!modal}
          onClose={() => setModal(null)}
          title={`Editar: ${modal.usuario.nome_exibicao}`}
          actions={
            <>
              <Button variant="ghost" onClick={() => setModal(null)}>Cancelar</Button>
              <Button onClick={handleAtualizar} loading={modal.loading}>Salvar</Button>
            </>
          }
        >
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-3 mb-2">
              <UserAvatar name={modal.usuario.nome_exibicao} size="sm" />
              <div>
                <p className="text-sm font-semibold text-text-primary">{modal.usuario.nome_exibicao}</p>
                <p className="text-xs text-text-muted font-mono">{modal.usuario.username}</p>
              </div>
            </div>
            <Input
              label="Nova senha (opcional)"
              type="password"
              placeholder="Deixe em branco para não alterar"
              value={modal.password}
              onChange={(e) => setModal(m => m ? { ...m, password: e.target.value } : null)}
            />
            <div className="flex flex-col gap-1.5">
              <label className="form-label">Permissão</label>
              <div className="grid grid-cols-1 gap-1.5">
                {ROLES_CONFIG.map(r => (
                  <button
                    key={r.value}
                    onClick={() => setModal(m => m ? { ...m, role: r.value } : null)}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg border text-sm text-left transition ${
                      modal.role === r.value
                        ? 'border-primary bg-primary-light text-primary'
                        : 'border-border text-text-secondary hover:border-border-input hover:bg-bg-hover'
                    }`}
                  >
                    <span className={`w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 ${
                      modal.role === r.value ? 'border-primary' : 'border-text-muted'
                    }`}>
                      {modal.role === r.value && (
                        <span className="w-2 h-2 rounded-full bg-primary" />
                      )}
                    </span>
                    <div>
                      <p className="font-medium">{r.label}</p>
                      <p className="text-xs text-text-muted">{r.desc}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
            {modal.erro && <p className="text-danger text-sm">{modal.erro}</p>}
          </div>
        </Modal>
      )}

      {/* Modal confirmar exclusão */}
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
        <p className="text-sm text-text-secondary">
          Esta ação não pode ser desfeita. O usuário perderá acesso ao sistema.
        </p>
      </Modal>

      {/* Novo usuário */}
      <PageSection
        title="Novo usuário"
        subtitle="Adicione um novo membro à equipe"
      >
        <Card variant="bordered" padding="md">
          <div className="flex flex-col gap-4">
            {erroGeral && (
              <p className="text-sm text-danger">{erroGeral}</p>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Input
                placeholder="Username"
                value={novoUsername}
                onChange={(e) => setNovoUsername(e.target.value)}
              />
              <Input
                placeholder="Nome de exibição"
                value={novoNome}
                onChange={(e) => setNovoNome(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Input
                type="password"
                placeholder="Senha"
                value={novoPassword}
                onChange={(e) => setNovoPassword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCriar()}
              />
              <select
                value={novoRole}
                onChange={(e) => setNovoRole(e.target.value as Role)}
                className="form-input-base"
              >
                {ROLES.map(r => <option key={r} value={r}>{roleLabels[r]}</option>)}
              </select>
              <Button
                onClick={handleCriar}
                loading={criando}
                fullWidth
              >
                <UserPlus size={14} /> Criar
              </Button>
            </div>

            {erroCriacao && (
              <p className="text-sm text-danger">{erroCriacao}</p>
            )}
          </div>
        </Card>
      </PageSection>

      {/* Lista de usuários */}
      <PageSection
        title="Equipe"
        subtitle={`${carregando ? '...' : usuarios.length} membro(s)`}
      >
        <Card variant="bordered" padding="none">
          {carregando ? (
            <div className="flex flex-col gap-2 p-5">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-12 bg-bg-hover rounded-lg animate-pulse" />
              ))}
            </div>
          ) : usuarios.length === 0 ? (
            <EmptyState title="Nenhum usuário" description="Crie o primeiro usuário da equipe." />
          ) : (
            <div className="divide-y divide-border-light">
              {usuarios.map(usuario => (
                <div
                  key={usuario.id}
                  className="flex items-center justify-between px-5 py-3 hover:bg-bg-hover transition group"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <UserAvatar name={usuario.nome_exibicao} size="sm" />
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-text-primary truncate">
                        {usuario.nome_exibicao}
                      </p>
                      <p className="text-xs text-text-muted font-mono">{usuario.username}</p>
                    </div>
                    <Badge variant={roleBadgeVariant[usuario.role]}>
                      {roleLabels[usuario.role]}
                    </Badge>
                  </div>

                  <div className="flex gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition">
                    <button
                      onClick={() => setModal({
                        usuario,
                        password: '',
                        role: usuario.role,
                        loading: false,
                        erro: '',
                      })}
                      className="p-1.5 rounded-lg text-text-muted hover:text-primary hover:bg-bg-hover transition"
                      aria-label={`Editar ${usuario.nome_exibicao}`}
                    >
                      <Edit2 size={14} />
                    </button>
                    <button
                      onClick={() => setExcluirUsuarioObj(usuario)}
                      disabled={usuario.username === meuUsername}
                      className="p-1.5 rounded-lg text-text-muted hover:text-danger hover:bg-danger-light transition disabled:opacity-30 disabled:cursor-not-allowed"
                      aria-label={`Excluir ${usuario.nome_exibicao}`}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </PageSection>
    </PageContainer>
  )
}
