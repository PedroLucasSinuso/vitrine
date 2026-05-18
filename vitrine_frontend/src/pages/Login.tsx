import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { TrendingUp, Shield, BarChart3 } from 'lucide-react'

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
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute -top-40 -right-40 w-[600px] h-[600px] bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-[500px] h-[500px] bg-accent/5 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/[0.02] rounded-full blur-3xl" />
      </div>

      {/* Left panel — brand / value prop (hidden on mobile) */}
      <div className="hidden lg:flex flex-col justify-between px-16 py-12 flex-1 relative">
        <div className="animate-fade-in-up">
          <img src="/vitrine_logo.svg" alt="Vitrine" className="h-8 w-auto mb-12 dark:invert" />
          <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-50 mb-6 leading-tight tracking-tight">
            Gestão inteligente<br />
            <span className="text-primary">para o seu supermercado</span>
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-base leading-relaxed mb-10 max-w-md">
            Relatórios de BI, controle de inventário, etiquetas e muito mais
            em um só lugar. Dados em tempo real para decisões mais assertivas.
          </p>
        </div>
        <div className="flex flex-col gap-5 animate-fade-in-up" style={{ animationDelay: '200ms' }}>
          <div className="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-300">
            <div className="w-10 h-10 rounded-xl bg-primary/10 dark:bg-primary/20 flex items-center justify-center shrink-0">
              <TrendingUp size={18} className="text-primary" />
            </div>
            <div>
              <p className="font-medium">Dashboards completos</p>
              <p className="text-slate-400 dark:text-slate-500 text-xs mt-0.5">KPIs, ranking e análise temporal</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-300">
            <div className="w-10 h-10 rounded-xl bg-primary/10 dark:bg-primary/20 flex items-center justify-center shrink-0">
              <Shield size={18} className="text-primary" />
            </div>
            <div>
              <p className="font-medium">Controle de acesso</p>
              <p className="text-slate-400 dark:text-slate-500 text-xs mt-0.5">Perfis: admin, supervisor, operador</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-300">
            <div className="w-10 h-10 rounded-xl bg-primary/10 dark:bg-primary/20 flex items-center justify-center shrink-0">
              <BarChart3 size={18} className="text-primary" />
            </div>
            <div>
              <p className="font-medium">Análise de vendas</p>
              <p className="text-slate-400 dark:text-slate-500 text-xs mt-0.5">Curva ABC, receita e perdas</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="flex-1 flex items-center justify-center px-6 relative">
        <div className="w-full max-w-sm animate-scale-in">
          {/* Logo on mobile */}
          <div className="lg:hidden text-center mb-10">
            <img src="/vitrine_logo.svg" alt="Vitrine" className="h-8 mx-auto mb-4 dark:invert" />
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-8">
            <div className="mb-8">
              <h2 className="text-xl font-bold text-slate-900 dark:text-slate-50">Acessar sistema</h2>
              <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">Informe suas credenciais para continuar</p>
            </div>

            <div className="flex flex-col gap-4">
              <div>
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1.5 block">Usuário</label>
                <input
                  aria-label="Usuário"
                  autoComplete="username"
                  className="w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition"
                  placeholder="Seu usuário"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                  autoFocus
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1.5 block">Senha</label>
                <input
                  type="password"
                  aria-label="Senha"
                  autoComplete="current-password"
                  className="w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition"
                  placeholder="Sua senha"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                />
              </div>

              {error && (
                <div className="bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-900 rounded-xl px-4 py-3 text-xs text-red-600 dark:text-red-400 flex items-center gap-2" role="alert">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500 shrink-0" />
                  {error}
                </div>
              )}

              <button
                onClick={handleSubmit}
                disabled={loading}
                className="bg-primary hover:bg-primary-hover text-white font-semibold py-3 rounded-xl transition disabled:opacity-50 text-sm mt-2"
              >
                {loading ? 'Entrando…' : 'Entrar'}
              </button>
            </div>
          </div>

          <p className="text-[10px] text-slate-400 dark:text-slate-500 text-center mt-8">
            Vitrine — Sistema de Gestão para Supermercados
          </p>
        </div>
      </div>
    </div>
  )
}
