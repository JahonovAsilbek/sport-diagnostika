import type { DarajaLevel } from '@/constants/labels'

import { api } from './client'

// Role-scoped dashboard numbers (API §12). Every count is scoped to the requester server-side;
// `regions` is the national total for super_admin/ministry, else the caller's distinct regions.
export interface StatsOverview {
  athletes_total: number
  by_organization_type: Record<'OTM' | 'OPSTTM', number>
  by_daraja: Record<DarajaLevel | 'none', number>
  regions: number
  recent_sessions: number
}

export const getOverview = () => api.get<StatsOverview>('/stats/overview/').then((r) => r.data)
