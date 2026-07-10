import type { Athlete, AthleteWrite } from '@/types/athlete'
import type { Gender, Paginated } from '@/types/catalog'

import { api } from './client'

export interface AthleteFilters {
  search?: string
  region?: number | null
  district?: number | null
  organization?: number | null
  sport_type?: number | null
  gender?: Gender | null
  coach?: number | null
  age_category?: number | null
  is_active?: boolean | null
  ordering?: string
  page?: number
}

// Scope is enforced server-side (BCKND-37) — the client only passes filters as query params.
function clean(filters: AthleteFilters): Record<string, unknown> {
  const params: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(filters)) {
    if (value !== null && value !== undefined && value !== '') params[key] = value
  }
  return params
}

export const listAthletes = (filters: AthleteFilters = {}) =>
  api.get<Paginated<Athlete>>('/athletes/', { params: clean(filters) }).then((r) => r.data)

export const getAthlete = (id: number) =>
  api.get<Athlete>(`/athletes/${id}/`).then((r) => r.data)

export const createAthlete = (payload: AthleteWrite) =>
  api.post<Athlete>('/athletes/', payload).then((r) => r.data)

export const updateAthlete = (id: number, payload: AthleteWrite) =>
  api.patch<Athlete>(`/athletes/${id}/`, payload).then((r) => r.data)

export const deleteAthlete = (id: number) => api.delete(`/athletes/${id}/`)
