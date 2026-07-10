import type { Paginated } from '@/types/catalog'
import type { Evaluation } from '@/types/measurement'

import { api } from './client'

export const listEvaluations = (params: {
  athlete?: number
  session?: number
  ordering?: string
}) => api.get<Paginated<Evaluation>>('/evaluations/', { params }).then((r) => r.data)
