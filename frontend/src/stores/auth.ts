import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as authApi from '@/api/auth'
import { clearTokens, getRefresh, startSession } from '@/api/tokens'
import type { Role, User } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)

  const isAuthenticated = computed(() => user.value !== null)
  const role = computed<Role | null>(() => user.value?.role ?? null)

  async function login(username: string, password: string, remember = true) {
    const data = await authApi.login(username, password)
    startSession(data.access, data.refresh, remember)
    user.value = data.user
  }

  async function logout() {
    const refresh = getRefresh()
    if (refresh) {
      // Best-effort blacklist — clear locally regardless of the server's answer.
      await authApi.logout(refresh).catch(() => undefined)
    }
    clearTokens()
    user.value = null
  }

  /** Called once on app load: if a refresh token survives, validate it via /me (the axios
   *  interceptor refreshes an expired access token transparently). On failure, stay logged out. */
  async function restore() {
    if (!getRefresh()) return
    try {
      user.value = await authApi.fetchMe()
    } catch {
      clearTokens()
      user.value = null
    }
  }

  return { user, isAuthenticated, role, login, logout, restore }
})
