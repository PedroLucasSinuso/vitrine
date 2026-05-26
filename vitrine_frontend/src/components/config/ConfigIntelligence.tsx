import { Key, Clock } from 'lucide-react'
import SectionHeader from '../ui/SectionHeader'
import TestConnectionButton from '../TestConnectionButton'
import PasswordConfigInput from '../PasswordConfigInput'
import type { TabProps } from './types'
import { testarAnthropic } from '../../api/admin'

function CompactInput({
  label, className, ...inputProps
}: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="flex flex-col gap-1">
      <label className="form-label">{label}</label>
      <input className={`form-input-base${className ? ` ${className}` : ''}`} {...inputProps} />
    </div>
  )
}

export default function ConfigIntelligence({ form, updateField }: TabProps) {
  return (
    <div className="p-5 flex flex-col gap-5">
      <div>
        <div className="mb-3">
          <SectionHeader icon={Key} title="API Keys" description="Chaves dos provedores de IA para relatórios inteligentes" />
        </div>
        <div className="ml-9 flex flex-col gap-3">
          <PasswordConfigInput label="Anthropic API Key" value={form.anthropic_api_key ?? ''} onChange={(v) => updateField('anthropic_api_key', v)} placeholder="sk-ant-xxxxxxxxxxxxxxxx" />
          <PasswordConfigInput label="OpenAI API Key" value={form.openai_api_key ?? ''} onChange={(v) => updateField('openai_api_key', v)} placeholder="sk-xxxxxxxxxxxxxxxx" />
        </div>
      </div>

      <div className="border-t border-border/50 pt-4">
        <div className="mb-3">
          <SectionHeader icon={Clock} title="Relatório" description="Período de análise dos dados" />
        </div>
        <div className="ml-9">
          <CompactInput label="Dias retroativos" type="number" min="1" value={form.relatorio_dias_retroativos ?? '30'} onChange={(e) => updateField('relatorio_dias_retroativos', e.target.value)} placeholder="30" className="max-w-[120px]" />
          <p className="text-[11px] text-text-muted mt-1">Quantos dias de dados o relatório de inteligência analisa</p>
        </div>
      </div>

      <TestConnectionButton label="Testar Anthropic" onTest={testarAnthropic} warningText="Testa a configuração salva no servidor, não as alterações pendentes" />
    </div>
  )
}
