import { useState } from 'react'
import { AlertCircle, Loader2, CheckCircle2, XCircle } from 'lucide-react'

interface Props {
  label: string
  onTest: () => Promise<{ status: string; mensagem: string }>
  warningText?: string
}

export default function TestConnectionButton({ label, onTest, warningText }: Props) {
  const [testing, setTesting] = useState(false)
  const [result, setResult] = useState<{ ok: boolean; msg: string } | null>(null)

  async function handleTest() {
    setTesting(true)
    setResult(null)
    try {
      const res = await onTest()
      setResult({ ok: res.status === 'ok', msg: res.mensagem })
    } catch {
      setResult({ ok: false, msg: 'Erro ao testar conexão' })
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-2">
        <button
          onClick={handleTest}
          disabled={testing}
          className="inline-flex items-center gap-2 text-xs font-medium text-primary hover:text-primary-hover disabled:opacity-50 transition px-3 py-1.5 rounded-lg hover:bg-primary/5 w-fit"
        >
          {testing ? <Loader2 size={13} className="animate-spin" /> : null}
          {testing ? 'Testando...' : label}
        </button>
        {warningText && (
          <span className="text-[10px] text-amber-600 dark:text-amber-400 flex items-center gap-0.5" title={warningText}>
            <AlertCircle size={11} />
            Usa config. salva
          </span>
        )}
      </div>
      {result && (
        <p className={`text-[11px] flex items-center gap-1 ${result.ok ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-500'}`}>
          {result.ok ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
          {result.msg}
        </p>
      )}
    </div>
  )
}
