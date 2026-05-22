import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Search, ClipboardList, LogOut } from 'lucide-react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'

export default function OperadorHome() {
  const navigate = useNavigate()
  const { logout, getNomeExibicao, getRole } = useAuth()
  const role = getRole()
  const nome = getNomeExibicao()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="flex flex-col items-center px-4 py-8">
      <div className="w-full max-w-md flex flex-col gap-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-bold text-text-primary">
            Olá, {nome || 'Operador'}!
          </h1>
          <button
            onClick={handleLogout}
            className="text-text-muted hover:text-danger transition p-2 rounded-lg hover:bg-danger-light"
            aria-label="Sair"
          >
            <LogOut size={18} />
          </button>
        </div>

        {role === 'operador' && (
          <p className="text-xs text-text-muted -mt-3">
            Use o menu abaixo para navegar
          </p>
        )}

        {/* Busca Card */}
        <Card
          variant="interactive"
          onClick={() => navigate('/busca')}
          className="flex items-center gap-4"
        >
          <div className="w-12 h-12 rounded-xl bg-primary-light flex items-center justify-center shrink-0">
            <Search size={24} className="text-primary" />
          </div>
          <div>
            <p className="text-base font-bold text-text-primary">Buscar Produto</p>
            <p className="text-xs text-text-muted mt-0.5">Consultar preço e estoque por código</p>
          </div>
        </Card>

        {/* Inventário Card */}
        <Card
          variant="interactive"
          onClick={() => navigate('/inventario')}
          className="flex items-center gap-4"
        >
          <div className="w-12 h-12 rounded-xl bg-primary-light flex items-center justify-center shrink-0">
            <ClipboardList size={24} className="text-primary" />
          </div>
          <div>
            <p className="text-base font-bold text-text-primary">Inventário</p>
            <p className="text-xs text-text-muted mt-0.5">Contagem e bipagem de produtos</p>
          </div>
        </Card>

        <Button variant="ghost" onClick={handleLogout} className="mt-2 w-full">
          <LogOut size={14} /> Sair
        </Button>
      </div>
    </div>
  )
}
