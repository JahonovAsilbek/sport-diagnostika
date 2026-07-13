import { isAxiosError } from 'axios'
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
   *  interceptor refreshes an expired access token transparently). Only a genuine auth failure
   *  (401 — the refresh token is dead too) ends the session; a network/server hiccup (API briefly
   *  down) must NOT nuke valid tokens and force a re-login, or a transient blip logs the user out
   *  for good. */
  async function restore() {
    if (!getRefresh()) return
    // Retry once on a network/server error — the API may just be (re)starting; a single blip
    // shouldn't drop the user to the login page.
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        user.value = await authApi.fetchMe()
        return
      } catch (e) {
        user.value = null
        if (isAxiosError(e) && e.response?.status === 401) {
          clearTokens()
          return
        }
        if (attempt === 0) await new Promise((resolve) => setTimeout(resolve, 600))
      }
    }
  }

  return { user, isAuthenticated, role, login, logout, restore }
})
