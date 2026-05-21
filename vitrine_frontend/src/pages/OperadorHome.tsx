import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Search, ClipboardList, LogOut } from 'lucide-react'

export default function OperadorHome() {
  const navigate = useNavigate()
  const { logout, getNomeExibicao, getRole } = useAuth()
  const role = getRole()
  const nome = getNomeExibicao()

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center px-4 py-8">
      <div className="w-full max-w-md flex flex-col gap-6">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-slate-800 dark:text-slate-100">
              Olá, {nome || 'Operador'}!
            </h1>
            <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">
              O que você precisa fazer?
            </p>
          </div>
          <button
            onClick={() => { logout(); navigate('/login') }}
            className="text-slate-400 hover:text-red-500 dark:hover:text-red-400 transition p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
            aria-label="Sair"
            title="Sair"
          >
            <LogOut size={18} />
          </button>
        </div>

        {/* Quick cards */}
        <div className="flex flex-col gap-4">

          {/* Card: Busca */}
          <button
            onClick={() => navigate('/busca')}
            className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-6 text-left hover:shadow-md hover:border-primary/30 dark:hover:border-primary/30 transition active:scale-[0.98]"
          >
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center shrink-0">
                <Search size={28} className="text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-base font-bold text-slate-800 dark:text-slate-100">Buscar Produto</p>
                <p className="text-sm text-slate-400 dark:text-slate-500 mt-0.5">
                  Consultar preço, estoque e informações
                </p>
              </div>
            </div>
          </button>

          {/* Card: Inventário */}
          <button
            onClick={() => navigate('/inventario')}
            className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-6 text-left hover:shadow-md hover:border-primary/30 dark:hover:border-primary/30 transition active:scale-[0.98]"
          >
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center shrink-0">
                <ClipboardList size={28} className="text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <p className="text-base font-bold text-slate-800 dark:text-slate-100">Inventário</p>
                <p className="text-sm text-slate-400 dark:text-slate-500 mt-0.5">
                  Bipar e contar estoque
                </p>
              </div>
            </div>
          </button>
        </div>

        {/* Role badge */}
        <div className="text-center">
          <span className="inline-block text-[10px] font-semibold px-2 py-1 rounded-full uppercase tracking-wider bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
            {role === 'operador' ? 'Operador' : role}
          </span>
        </div>
      </div>
    </div>
  )
}
