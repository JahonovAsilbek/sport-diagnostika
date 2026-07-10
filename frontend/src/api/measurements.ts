import type { Gender, Paginated, TestBattery } from '@/types/catalog'
import type { Evaluation, TestSession } from '@/types/measurement'

import { api } from './client'

export const listSessions = (params?: { athlete?: number; status?: string; page?: number }) =>
  api.get<Paginated<TestSession>>('/sessions/', { params }).then((r) => r.data)

export const getSession = (id: number) =>
  api.get<TestSession>(`/sessions/${id}/`).then((r) => r.data)

export const createSession = (payload: {
  athlete: number
  date?: string
  height_cm?: string | null
  weight_kg?: string | null
}) => api.post<TestSession>('/sessions/', payload).then((r) => r.data)

export const updateSession = (
  id: number,
  payload: { date?: string; height_cm?: string | null; weight_kg?: string | null },
) => api.patch<TestSession>(`/sessions/${id}/`, payload).then((r) => r.data)

/** The 5 age×gender-specific exercises that drive the entry form (BCKND-40). */
export const getBattery = (id: number) =>
  api.get<TestBattery>(`/sessions/${id}/battery/`).then((r) => r.data)

export const saveMeasurements = (id: number, measurements: { exercise: number; raw_value: string }[]) =>
  api.post<TestSession>(`/sessions/${id}/measurements/`, { measurements }).then((r) => r.data)

/** Validate the complete battery, flip draft→finalized, and score it — returns the Evaluation. */
export const finalizeSession = (id: number) =>
  api.post<Evaluation & { status: string }>(`/sessions/${id}/finalize/`).then((r) => r.data)

export type { Gender }
