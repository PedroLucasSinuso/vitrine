import { useState, useRef, useEffect } from 'react'
import { Bell, BellOff, Check, Download } from 'lucide-react'
import { useNotificacoes } from '../hooks/useNotificacoes'
import api from '../api/client'
import { formatDataBrasil } from '../utils/formatters'

export default function NotificationCenter() {
  const [open, setOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const { notificacoes, naoLidas, ler, lerTodas } = useNotificacoes()

  useEffect(() => {
    if (!open) return
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('mousedown', handleClick)
      document.removeEventListener('keydown', handleKey)
    }
  }, [open])

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setOpen((prev) => !prev)}
        className="relative text-text-muted hover:text-text-primary transition p-1.5 rounded-lg hover:bg-bg-hover"
        aria-label="Notificações"
        aria-expanded={open}
        aria-haspopup="true"
        title="Notificações"
      >
        <Bell size={15} aria-hidden="true" />
        {naoLidas > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-red-500 text-white text-[8px] font-bold rounded-full flex items-center justify-center">
            {naoLidas > 9 ? '9+' : naoLidas}
          </span>
        )}
      </button>

      {open && (
        <div
          role="menu"
          aria-label="Notificações"
          className="absolute right-0 top-full mt-2 w-80 sm:w-96 bg-surface-modal rounded-xl shadow-lg border border-border animate-fade-in-up z-[60]"
        >
          <div className="px-4 py-3 border-b border-border flex items-center justify-between">
            <h3 className="text-sm font-semibold text-text-primary">Notificações</h3>
            {naoLidas > 0 && (
              <button
                onClick={lerTodas}
                className="text-xs text-primary hover:underline"
                aria-label="Marcar todas como lidas"
              >
                Marcar todas como lidas
              </button>
            )}
          </div>

          {notificacoes.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-text-muted">
              <BellOff size={24} className="mx-auto mb-2 opacity-40" aria-hidden="true" />
              Nenhuma notificação
            </div>
          ) : (
            <div className="max-h-80 overflow-y-auto divide-y divide-border">
              {notificacoes.map((n) => (
                <div
                  key={n.id}
                  className={`px-4 py-3 text-sm transition ${
                    n.resolvida ? 'opacity-40' : n.lida ? '' : 'bg-accent/5'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className={`text-xs font-semibold mb-0.5 ${
                        n.tipo === 'margem_negativa' ? 'text-danger' :
                        n.tipo === 'sync_erro' ? 'text-warning' :
                        'text-text-primary'
                      }`}>
                        {n.titulo}
                      </p>
                      {n.mensagem && (
                        <p className="text-xs text-text-muted mt-1 whitespace-pre-line leading-relaxed">
                          {n.mensagem}
                        </p>
                      )}
                      <div className="flex items-center gap-2 mt-1.5">
                        <p className="text-[10px] text-text-muted/60">
                          {formatDataBrasil(n.criada_em)}
                        </p>
                        {(() => {
                          if (!n.dados_json) return null
                          try {
                            const parsed = JSON.parse(n.dados_json)
                            if (!Array.isArray(parsed.itens) || parsed.itens.length === 0) return null
                            return (
                              <button
                                onClick={async (e) => {
                                  e.stopPropagation()
                                  try {
                                    const r = await api.get(`/bi/exportar/margem-negativa/${n.id}`, {
                                      responseType: 'blob',
                                    })
                                    const url = URL.createObjectURL(r.data)
                                    const link = document.createElement('a')
                                    link.href = url
                                    link.download = `margem_negativa_${n.id}.xlsx`
                                    link.click()
                                    URL.revokeObjectURL(url)
                                  } catch {
                                    // fallback silencioso
                                  }
                                }}
                                className="text-[10px] text-primary hover:underline inline-flex items-center gap-0.5"
                                title="Baixar relatório Excel"
                              >
                                <Download size={10} />
                                Baixar relatório
                              </button>
                            )
                          } catch { return null }
                        })()}
                      </div>
                    </div>
                    {!n.lida && (
                      <button
                        onClick={() => ler(n.id)}
                        className="shrink-0 p-1 text-text-muted hover:text-text-primary hover:bg-bg-hover rounded transition"
                        aria-label="Marcar como lida"
                        title="Marcar como lida"
                      >
                        <Check size={12} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
