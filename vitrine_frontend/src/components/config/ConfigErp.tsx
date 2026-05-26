import { useState } from 'react'
import { Database, Globe, Hash, Lock, Clock, RefreshCw, Eye, EyeOff } from 'lucide-react'
import SectionHeader from '../ui/SectionHeader'
import TestConnectionButton from '../TestConnectionButton'
import PasswordConfigInput from '../PasswordConfigInput'
import { ETL_INTERVALS } from './types'
import type { TabProps } from './types'
import { testarConexaoErp } from '../../api/admin'

function CompactInput({
  label, icon: Icon, className, ...inputProps
}: { label: string; icon?: React.ElementType } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="flex flex-col gap-1">
      <label className="form-label flex items-center gap-1">
        {Icon && <Icon size={11} className="text-text-muted" />}
        {label}
      </label>
      <input className={`form-input-base${className ? ` ${className}` : ''}`} {...inputProps} />
    </div>
  )
}

function CompactSelect({
  label, icon: Icon, children, ...selectProps
}: { label: string; icon?: React.ElementType; children: React.ReactNode } & React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div className="flex flex-col gap-1">
      <label className="form-label flex items-center gap-1">
        {Icon && <Icon size={11} className="text-text-muted" />}
        {label}
      </label>
      <select className="form-input-base" {...selectProps}>{children}</select>
    </div>
  )
}

export default function ConfigErp({ form, updateField }: TabProps) {
  const [erpRevealed, setErpRevealed] = useState(false)

  return (
    <div className="p-5 flex flex-col gap-8 max-w-lg mx-auto">
      {/* Connection */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <SectionHeader icon={Database} title="Conexão ERP" description="Credenciais do banco de dados PostgreSQL" />
          <button
            onClick={() => setErpRevealed((p) => !p)}
            className="inline-flex items-center gap-1.5 text-[11px] font-medium text-text-muted hover:text-primary transition px-2 py-1 rounded-md hover:bg-bg-hover/50 shrink-0"
          >
            {erpRevealed ? <EyeOff size={12} /> : <Eye size={12} />}
            {erpRevealed ? 'Ocultar' : 'Mostrar'}
          </button>
        </div>

        {erpRevealed ? (
          <div className="flex flex-col gap-3 animate-fade-in-up">
            <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-3">
              <CompactInput label="Host" icon={Globe} value={form.erp_host ?? ''} onChange={(e) => updateField('erp_host', e.target.value)} placeholder="192.168.1.100" />
              <CompactInput label="Porta" icon={Hash} type="number" min="1" max="65535" value={form.erp_port ?? '5432'} onChange={(e) => updateField('erp_port', e.target.value)} className="max-w-[90px]" />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-[1fr_1fr] gap-3">
              <CompactInput label="Database" value={form.erp_database ?? ''} onChange={(e) => updateField('erp_database', e.target.value)} placeholder="erp_producao" />
              <CompactInput label="Usuário" value={form.erp_user ?? ''} onChange={(e) => updateField('erp_user', e.target.value)} placeholder="postgres" />
            </div>
            <PasswordConfigInput label="Senha" value={form.erp_password ?? ''} onChange={(v) => updateField('erp_password', v)} placeholder="••••••••" />
            <TestConnectionButton label="Testar conexão ERP" onTest={testarConexaoErp} warningText="Testa a configuração salva no servidor, não as alterações pendentes" />
          </div>
        ) : (
          <div className="text-[11px] text-text-muted bg-bg-hover/30 rounded-lg px-3 py-2 flex items-center gap-1.5">
            <Lock size={11} /> Dados de conexão ocultos — clique em "Mostrar" para editar
          </div>
        )}
      </div>

      {/* Sync settings */}
      <div className="border-t border-border/50 pt-4">
        <div className="mb-3">
          <SectionHeader icon={Clock} title="Agendamento" description="Intervalos de sincronização e cache" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <CompactSelect label="Intervalo ETL" value={form.etl_interval_minutes ?? '60'} onChange={(e) => updateField('etl_interval_minutes', e.target.value)}>
            {ETL_INTERVALS.map((opt) => (<option key={opt.value} value={opt.value}>{opt.label}</option>))}
          </CompactSelect>
          <CompactInput label="Cache Refresh (min)" icon={RefreshCw} type="number" min="1" value={form.cache_refresh_interval ?? '5'} onChange={(e) => updateField('cache_refresh_interval', e.target.value)} />
        </div>
      </div>
    </div>
  )
}
