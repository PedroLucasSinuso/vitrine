import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-bg-hover flex items-center justify-center px-4">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-text-primary mb-4">404</h1>
        <p className="text-text-secondary mb-6">Página não encontrada</p>
        <Link
          to="/"
          className="bg-primary hover:bg-primary-hover text-white font-semibold px-6 py-2 rounded-lg transition"
        >
          Voltar ao início
        </Link>
      </div>
    </div>
  )
}
