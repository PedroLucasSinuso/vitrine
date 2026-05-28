/** Tipos para indicadores macroeconômicos. */

export interface MacroIndicator {
  chave: string
  rotulo: string
  valor: number | null
  disponivel: boolean
  unidade: string
  periodo_ref: string | null
  consultado_em: string
  mensagem: string | null
}
