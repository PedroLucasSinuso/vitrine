/**
 * Validações client-side que espelham as validações do backend.
 * Previne chamadas de API que seriam rejeitadas com 400/422.
 */

const MAX_RANGE_DIAS_NORMAL = 366
const MAX_RANGE_DIAS_COMPARATIVO = 731
const TOP_MIN = 1
const TOP_MAX = 100

export function validarCodigo(codigo: string): string | null {
  if (!codigo || codigo.trim().length === 0) {
    return 'Código do produto é obrigatório'
  }
  // Backend Codigo value object aceita qualquer string não vazia após strip
  return null
}

export function validarTop(top: number): string | null {
  if (!Number.isInteger(top) || top < TOP_MIN || top > TOP_MAX) {
    return `Top deve ser um número inteiro entre ${TOP_MIN} e ${TOP_MAX}`
  }
  return null
}

export function validarPeriodoBi(
  dataInicio: string,
  dataFim: string,
  comparar: boolean = false,
): string | null {
  const inicio = new Date(dataInicio)
  const fim = new Date(dataFim)

  if (isNaN(inicio.getTime()) || isNaN(fim.getTime())) {
    return 'Datas inválidas. Use o formato YYYY-MM-DD'
  }

  if (fim < inicio) {
    return 'data_fim não pode ser anterior a data_inicio'
  }

  const diffDays = Math.round((fim.getTime() - inicio.getTime()) / (1000 * 60 * 60 * 24))
  const maxDias = comparar ? MAX_RANGE_DIAS_COMPARATIVO : MAX_RANGE_DIAS_NORMAL

  if (diffDays > maxDias) {
    return `Intervalo máximo permitido é de ${maxDias} dias`
  }

  return null
}

export function validarSenha(senha: string): string | null {
  if (!senha || senha.trim().length === 0) {
    return 'Senha não pode ser vazia'
  }
  return null
}
