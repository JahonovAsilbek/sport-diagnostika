import type { Role, User, UserWrite } from '@/types/auth'
import type { Paginated } from '@/types/catalog'

import { api } from './client'

export interface UserFilters {
  role?: Role
  is_active?: boolean
  search?: string
  page?: number
}

// The list is scoped server-side (a region_admin sees only their region; BCKND-15).
export const listUsers = (params: UserFilters = {}) =>
  api.get<Paginated<User>>('/users/', { params: { page_size: 100, ...params } }).then((r) => r.data)

export const createUser = (payload: UserWrite) =>
  api.post<User>('/users/', payload).then((r) => r.data)

export const updateUser = (id: number, payload: Partial<UserWrite>) =>
  api.patch<User>(`/users/${id}/`, payload).then((r) => r.data)

// Soft deactivate (is_active=false) — users are never hard-deleted (audit/FK integrity).
export const deactivateUser = (id: number) => api.delete(`/users/${id}/`)

export const resetPassword = (id: number, password: string) =>
  api.post(`/users/${id}/reset-password/`, { password })

// Coaches the actor may assign — the /users list is scoped server-side (a region_admin sees
// only their region's coaches, a coach sees themselves).
export const getCoaches = () =>
  api
    .get<Paginated<User>>('/users/', {
      params: { role: 'coach', is_active: true, page_size: 100 },
    })
    .then((r) => r.data.results)
