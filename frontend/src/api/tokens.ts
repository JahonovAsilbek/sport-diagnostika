// Single source of truth for the JWT pair. Both the axios interceptor and the auth store read
// tokens here (not from each other) so there's no import cycle. localStorage is a deliberate
// tradeoff (survives reloads; accepted per FRNTND-3) — the refresh token is blacklistable on logout.
const ACCESS_KEY = 'sd.access'
const REFRESH_KEY = 'sd.refresh'

export function getAccess(): string | null {
  return localStorage.getItem(ACCESS_KEY)
}

export function getRefresh(): string | null {
  return localStorage.getItem(REFRESH_KEY)
}

export function setTokens(access: string, refresh?: string): void {
  localStorage.setItem(ACCESS_KEY, access)
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}
