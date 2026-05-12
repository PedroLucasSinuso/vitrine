export type Role = 'operador' | 'supervisor' | 'admin'

export interface AuthToken {
  access_token: string
  token_type: string
}

export interface JwtPayload {
  sub: string
  role: Role
  nome_exibicao?: string
}
