import type { Paginated } from '@/types/catalog'

import { api } from './client'

export interface Recommendation {
  id: number
  text: string
  // The related exercise NAME (backend SerializerMethodField), or null for a physical_total
  // rule / a since-deleted rule.
  exercise: string | null
  created_at: string
}

export const listRecommendations = (params: { athlete?: number; evaluation?: number }) =>
  api.get<Paginated<Recommendation>>('/recommendations/', { params }).then((r) => r.data)

// --- Recommendation rules (super_admin only) ---
export type Comparator = 'lte' | 'lt' | 'gte' | 'gt'

export const COMPARATOR_LABELS: Record<Comparator, string> = {
  lte: '≤',
  lt: '<',
  gte: '≥',
  gt: '>',
}

export interface RecommendationRule {
  id: number
  // exercise id → the rule targets that exercise's points (0–10); null → physical_total (0–50).
  exercise: number | null
  comparator: Comparator
  threshold: number
  template_text: string
  is_active: boolean
}

export type RecommendationRuleWrite = Omit<RecommendationRule, 'id'>

export const listRules = () =>
  api.get<Paginated<RecommendationRule>>('/recommendation-rules/').then((r) => r.data)

export const createRule = (payload: RecommendationRuleWrite) =>
  api.post<RecommendationRule>('/recommendation-rules/', payload).then((r) => r.data)

export const updateRule = (id: number, payload: Partial<RecommendationRuleWrite>) =>
  api.patch<RecommendationRule>(`/recommendation-rules/${id}/`, payload).then((r) => r.data)

export const deleteRule = (id: number) => api.delete(`/recommendation-rules/${id}/`)
