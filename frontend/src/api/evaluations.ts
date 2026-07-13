import type { PeriodParams } from '@/composables/usePeriodQuery'
import type { Paginated } from '@/types/catalog'
import type { Evaluation } from '@/types/measurement'

import { api } from './client'

// An optional period (BCKND-70) filters the athlete's history to evaluations within the range.
export const listEvaluations = (
  params: { athlete?: number; session?: number; ordering?: string } & PeriodParams,
) => api.get<Paginated<Evaluation>>('/evaluations/', { params }).then((r) => r.data)
