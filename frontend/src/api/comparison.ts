import type { DarajaLevel } from '@/constants/labels'

import { api } from './client'

// One exercise's result. `exercise` is the NAME (not id) — batteries differ by age×gender,
// so the name is what matches rows across athletes (backend ComparisonIndicatorSerializer).
export interface ComparisonIndicator {
  exercise: string
  raw_value: string
  points: number
}

// One athlete's side. Scalars are null for an athlete with no Evaluation yet.
export interface ComparisonAthlete {
  id: number
  full_name: string
  physical_total: number | null
  ranking_score: number | null
  daraja: DarajaLevel | 'none' | null
  color: 'green' | 'yellow' | 'red' | null
  indicators: ComparisonIndicator[]
}

export interface ComparisonResult {
  athletes: ComparisonAthlete[]
  // id of the highest physical_total (request order breaks ties), or null if none evaluated.
  leader: number | null
}

// Every id must be in the caller's scope server-side (out-of-scope → 403). 2–3 ids only.
export const compareAthletes = (ids: number[]) =>
  api
    .get<ComparisonResult>('/comparison/', { params: { athletes: ids.join(',') } })
    .then((r) => r.data)
