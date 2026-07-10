import axios, {
  AxiosError,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'

import { clearTokens, getAccess, getRefresh, setTokens } from './tokens'

// Same-origin base — Vite proxies /api to the backend in dev, nginx does in prod.
export const api = axios.create({ baseURL: '/api/v1' })

// A bare client for the refresh call itself — using `api` would recurse through the 401 handler.
const bare = axios.create({ baseURL: '/api/v1' })

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

// Requests that must never trigger a refresh-retry (they ARE the auth flow).
const AUTH_PATHS = ['/auth/login/', '/auth/refresh/']

api.interceptors.request.use((config) => {
  const token = getAccess()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Single-flight refresh: concurrent 401s share one refresh call instead of stampeding.
let refreshPromise: Promise<string> | null = null

async function refreshAccess(): Promise<string> {
  const refresh = getRefresh()
  if (!refresh) throw new Error('no refresh token')
  const { data } = await bare.post<{ access: string; refresh?: string }>('/auth/refresh/', {
    refresh,
  })
  setTokens(data.access, data.refresh)
  return data.access
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetriableConfig | undefined
    const status = error.response?.status
    const isAuthCall = config ? AUTH_PATHS.some((p) => config.url?.includes(p)) : true

    if (status === 401 && config && !config._retry && !isAuthCall && getRefresh()) {
      config._retry = true
      try {
        refreshPromise ??= refreshAccess().finally(() => {
          refreshPromise = null
        })
        const access = await refreshPromise
        config.headers.Authorization = `Bearer ${access}`
        return api(config)
      } catch (refreshError) {
        // Refresh failed → the session is dead. Clear it and bounce to login.
        clearTokens()
        if (window.location.pathname !== '/login') window.location.assign('/login')
        return Promise.reject(refreshError)
      }
    }
    return Promise.reject(error)
  },
)

/** Map any request failure to a user-facing Uzbek message (API.md §1 error shape). */
export function toMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) return "Kutilmagan xatolik yuz berdi."
  const err = error as AxiosError<{ detail?: string } & Record<string, unknown>>
  if (!err.response) return "Server bilan bogʻlanib boʻlmadi. Internetni tekshiring."
  const data = err.response.data
  if (typeof data?.detail === 'string') return data.detail
  // DRF field errors: {field: ["msg", ...]} — surface the first one.
  if (data && typeof data === 'object') {
    for (const value of Object.values(data)) {
      if (Array.isArray(value) && typeof value[0] === 'string') return value[0]
    }
  }
  const byStatus: Record<number, string> = {
    400: "Notoʻgʻri soʻrov.",
    401: "Avtorizatsiya talab qilinadi.",
    403: "Bu amal uchun ruxsatingiz yoʻq.",
    404: "Maʼlumot topilmadi.",
    500: "Server xatosi. Keyinroq urinib koʻring.",
  }
  return byStatus[err.response.status] ?? "Xatolik yuz berdi."
}

export type { AxiosResponse }
