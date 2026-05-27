/** Token store in-memory — evita circular dependency entre client.ts e useAuth.ts */
let _accessToken: string | null = null

export function setAccessToken(token: string | null) {
  _accessToken = token
}

export function getAccessToken(): string | null {
  return _accessToken
}
