import type { LoginResponse, User } from '@/types/auth'

import { api } from './client'

export function login(username: string, password: string) {
  return api.post<LoginResponse>('/auth/login/', { username, password }).then((r) => r.data)
}

export function fetchMe() {
  return api.get<User>('/auth/me/').then((r) => r.data)
}

export function logout(refresh: string) {
  return api.post('/auth/logout/', { refresh })
}
