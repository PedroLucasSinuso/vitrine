import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { TrendingUp, Shield, BarChart3, AlertCircle } from 'lucide-react'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import Logo from '../components/ui/Logo'

export default function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit() {
    setError('')
    setLoading(true)
    try {
      await login(username, password)
      navigate('/', { replace: true })
    } catch {
      setError('Usuário ou senha inválidos.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg-page flex relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute -top-40 -right-40 w-[600px] h-[600px] bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-[500px] h-[500px] bg-accent/5 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/[0.02] rounded-full blur-3xl" />
      </div>

      {/* Left panel — brand / value prop (hidden on mobile) */}
      <div className="hidden md:flex flex-col justify-between px-16 py-12 flex-1 relative">
        <div>
          <Logo height={32} className="text-text-primary mb-12" />
          <h1 className="text-4xl font-bold text-text-primary mb-6 leading-tight tracking-tight">
            Gestão inteligente<br />
            <span className="text-primary">para o seu supermercado</span>
          </h1>
          <p className="text-text-muted text-base leading-relaxed mb-10 max-w-md">
            Relatórios de BI, controle de inventário, etiquetas e muito mais
            em um só lugar. Dados em tempo real para decisões mais assertivas.
          </p>
        </div>
        <div className="flex flex-col gap-5">
          <div className="flex items-center gap-4 text-sm text-text-secondary">
            <div className="w-10 h-10 rounded-xl bg-primary-light flex items-center justify-center shrink-0">
              <TrendingUp size={18} className="text-primary" />
            </div>
            <div>
              <p className="font-medium text-text-primary">Dashboards completos</p>
              <p className="text-text-muted text-xs mt-0.5">KPIs, ranking e análise temporal</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm text-text-secondary">
            <div className="w-10 h-10 rounded-xl bg-primary-light flex items-center justify-center shrink-0">
              <Shield size={18} className="text-primary" />
            </div>
            <div>
              <p className="font-medium text-text-primary">Controle de acesso</p>
              <p className="text-text-muted text-xs mt-0.5">Perfis: admin, supervisor, operador</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm text-text-secondary">
            <div className="w-10 h-10 rounded-xl bg-primary-light flex items-center justify-center shrink-0">
              <BarChart3 size={18} className="text-primary" />
            </div>
            <div>
              <p className="font-medium text-text-primary">Análise de vendas</p>
              <p className="text-text-muted text-xs mt-0.5">Curva ABC, receita e perdas</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="flex-1 flex items-center justify-center px-6 relative">
        <div className="w-full max-w-sm">
          {/* Logo on mobile */}
          <div className="lg:hidden text-center mb-10">
            <Logo height={32} className="text-text-primary mx-auto" />
          </div>

          <Card variant="elevated" className="p-8">
            <div className="mb-8">
              <h2 className="text-xl font-bold text-text-primary">Acessar sistema</h2>
              <p className="text-sm text-text-muted mt-1">Informe suas credenciais para continuar</p>
            </div>

            <div className="flex flex-col gap-4">
              <Input
                label="Usuário"
                placeholder="Seu usuário"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                autoFocus
              />
              <Input
                label="Senha"
                type="password"
                placeholder="Sua senha"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
              />

              {error && (
                <div className="flex items-center gap-2 bg-danger-light border border-danger/20 rounded-xl px-4 py-3 text-xs text-danger" role="alert">
                  <AlertCircle size={14} className="shrink-0" />
                  <span className="w-1.5 h-1.5 rounded-full bg-danger shrink-0" />
                  {error}
                </div>
              )}

              <Button onClick={handleSubmit} loading={loading} className="mt-2 w-full">
                Entrar
              </Button>
            </div>
          </Card>

          <p className="text-[10px] text-text-muted text-center mt-8">
            Vitrine — Sistema de Gestão para Supermercados
          </p>
        </div>
      </div>
    </div>
  )
}
