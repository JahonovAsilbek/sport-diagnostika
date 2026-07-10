import type { DarajaLevel } from '@/constants/labels'
import type { Gender, Paginated } from '@/types/catalog'

import { api } from './client'

// One ranked athlete. `daraja`/`color` are the snapshot's stable English enum values;
// the UI maps them (DarajaBadge). `none` = scored but below daraja III.
export interface RatingRow {
  rank: number
  athlete: { id: number; full_name: string }
  ranking_score: number
  daraja: DarajaLevel | 'none'
  color: 'green' | 'yellow' | 'red'
}

// One region row from `/rating/regions/`.
export interface RegionRatingRow {
  rank: number
  region: string
  daraja_i_count: number
  avg_score: number | null
}

export interface RatingQuery {
  region?: number | null
  sport_type?: number | null
  age_category?: number | null
  gender?: Gender | null
  limit?: number
  page?: number
}

// `/rating/top/` returns a small envelope (echoed filter names + the ranked rows).
export interface TopResponse {
  filters: Record<string, string>
  results: RatingRow[]
}

// Scope is enforced server-side (BCKND-49) — the client only passes the whitelisted filters.
function clean(query: RatingQuery): Record<string, unknown> {
  const params: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(query)) {
    if (value !== null && value !== undefined && value !== '') params[key] = value
  }
  return params
}

export const getTopAthletes = (query: RatingQuery = {}) =>
  api.get<TopResponse>('/rating/top/', { params: clean(query) }).then((r) => r.data)

export const listRating = (query: RatingQuery = {}) =>
  api.get<Paginated<RatingRow>>('/rating/athletes/', { params: clean(query) }).then((r) => r.data)

export const getRegionRating = (query: RatingQuery = {}) =>
  api.get<{ results: RegionRatingRow[] }>('/rating/regions/', { params: clean(query) }).then(
    (r) => r.data,
  )
