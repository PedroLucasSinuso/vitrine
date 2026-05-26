import { Component, type ReactNode, type ErrorInfo } from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary]', error, info.componentStack)
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined })
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 px-4">
          <div className="w-12 h-12 rounded-2xl bg-danger-light flex items-center justify-center">
            <AlertCircle size={24} className="text-danger" />
          </div>
          <div className="text-center">
            <p className="text-lg font-semibold text-text-primary">Erro ao carregar página</p>
            <p className="text-sm text-text-muted mt-1 max-w-sm">
              {this.state.error?.message || 'Ocorreu um erro inesperado.'}
            </p>
          </div>
          <button
            onClick={this.handleRetry}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-white text-sm font-semibold hover:bg-primary-hover transition active:scale-[0.97]"
          >
            <RefreshCw size={14} />
            Tentar novamente
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
