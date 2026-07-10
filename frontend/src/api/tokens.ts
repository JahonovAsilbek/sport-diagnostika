// Single source of truth for the JWT pair. Both the axios interceptor and the auth store read
// tokens here (not from each other) so there's no import cycle. "Remember me" picks the store:
// localStorage (persists across browser restarts) vs sessionStorage (cleared on close). Reads
// check both; the refresh token being blacklistable on logout bounds the localStorage tradeoff.
const ACCESS_KEY = 'sd.access'
const REFRESH_KEY = 'sd.refresh'

function read(key: string): string | null {
  return localStorage.getItem(key) ?? sessionStorage.getItem(key)
}

// Where the current session lives — sessionStorage if it holds the refresh, else localStorage.
function currentStore(): Storage {
  return sessionStorage.getItem(REFRESH_KEY) !== null ? sessionStorage : localStorage
}

export function getAccess(): string | null {
  return read(ACCESS_KEY)
}

export function getRefresh(): string | null {
  return read(REFRESH_KEY)
}

/** Start a fresh session (login). `remember` decides persistence. */
export function startSession(access: string, refresh: string, remember: boolean): void {
  clearTokens()
  const store = remember ? localStorage : sessionStorage
  store.setItem(ACCESS_KEY, access)
  store.setItem(REFRESH_KEY, refresh)
}

/** Update tokens in place after a refresh — stays in whichever store the session already uses. */
export function saveTokens(access: string, refresh?: string): void {
  const store = currentStore()
  store.setItem(ACCESS_KEY, access)
  if (refresh) store.setItem(REFRESH_KEY, refresh)
}

export function clearTokens(): void {
  for (const store of [localStorage, sessionStorage]) {
    store.removeItem(ACCESS_KEY)
    store.removeItem(REFRESH_KEY)
  }
}
