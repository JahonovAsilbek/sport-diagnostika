import type { Paginated } from '@/types/catalog'

import { api } from './client'

export interface Recommendation {
  id: number
  text: string
  exercise: number | null
  created_at: string
}

export const listRecommendations = (params: { athlete?: number; evaluation?: number }) =>
  api.get<Paginated<Recommendation>>('/recommendations/', { params }).then((r) => r.data)
