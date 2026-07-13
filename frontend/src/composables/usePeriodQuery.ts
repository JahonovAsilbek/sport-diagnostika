import type { LocationQuery } from 'vue-router'

// Shared period model for the FRNTND-26 selector, matching the BCKND-70 query contract:
// period_type ∈ {quarter, half, year} + period_year + period_index (1–4 quarter / 1–2 half;
// ignored for year). All optional — an empty PeriodParams means "no period" (latest overall).
export const PERIOD_TYPES = ['quarter', 'half', 'year'] as const
export type PeriodType = (typeof PERIOD_TYPES)[number]

export interface PeriodParams {
  period_type?: PeriodType
  period_year?: number
  period_index?: number
}

// Drop empty/irrelevant fields so an incomplete pick degrades to "latest" and `year` never carries
// a stray index. The single normalizer used by the selector, the API layer, and URL sync.
export function cleanPeriod(p: PeriodParams | null | undefined): PeriodParams {
  if (!p || !p.period_type) return {}
  const out: PeriodParams = { period_type: p.period_type }
  if (p.period_year) out.period_year = p.period_year
  if (p.period_type !== 'year' && p.period_index) out.period_index = p.period_index
  return out
}

function isPeriodType(value: unknown): value is PeriodType {
  return typeof value === 'string' && (PERIOD_TYPES as readonly string[]).includes(value)
}

// Serialize to a flat string query (for router.replace) and back (hydrating from a shared link).
export function periodToQuery(p: PeriodParams): Record<string, string> {
  const c = cleanPeriod(p)
  const q: Record<string, string> = {}
  if (c.period_type) q.period_type = c.period_type
  if (c.period_year) q.period_year = String(c.period_year)
  if (c.period_index) q.period_index = String(c.period_index)
  return q
}

export function periodFromQuery(query: LocationQuery): PeriodParams {
  if (!isPeriodType(query.period_type)) return {}
  const year = Number(query.period_year)
  const index = Number(query.period_index)
  return cleanPeriod({
    period_type: query.period_type,
    period_year: Number.isFinite(year) && year > 0 ? year : undefined,
    period_index: Number.isFinite(index) && index > 0 ? index : undefined,
  })
}
