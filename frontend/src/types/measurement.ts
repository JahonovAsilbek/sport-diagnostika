import type { DarajaLevel } from '@/constants/labels'
import type { Gender } from '@/types/catalog'

export type SessionStatus = 'draft' | 'finalized'

export interface Measurement {
  exercise: number
  raw_value: string
}

export interface TestSession {
  id: number
  athlete: number
  date: string
  entered_by: number | null
  source: string
  status: SessionStatus
  age_category: number | null
  gender: Gender
  region: number | null
  organization: number | null
  sport_type: number | null
  height_cm: string | null
  weight_kg: string | null
  measurements: Measurement[]
  created_at: string
}

export interface IndicatorScore {
  exercise: number
  raw_value: string
  points: number
}

export interface Evaluation {
  evaluation_id: number
  session: number
  athlete: number
  session_date: string
  age_category: number | null
  gender: Gender
  region: number | null
  sport_type: number | null
  physical_total: number
  ranking_score: number
  daraja: DarajaLevel | 'none'
  color: 'green' | 'yellow' | 'red'
  computed_at: string
  indicators: IndicatorScore[]
}

// --- Excel import (FRNTND-15) ---
export type ImportStatus = 'validating' | 'validated' | 'failed' | 'committed'
export type ImportRowStatus = 'pending' | 'valid' | 'invalid' | 'committed'

export interface ImportRow {
  row_number: number
  status: ImportRowStatus
  raw_data: Record<string, unknown>
  errors: string[]
  athlete: number | null
  created_session: number | null
}

export interface ImportBatch {
  id: number
  status: ImportStatus
  age_category: number | null
  gender: Gender
  date: string
  row_count: number
  error_count: number
  error: string | null
  rows: ImportRow[]
  created_at: string
}
