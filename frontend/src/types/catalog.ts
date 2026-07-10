import type { DarajaLevel } from '@/constants/labels'

export type Gender = 'male' | 'female'
export type OrgType = 'OTM' | 'OPSTTM'
export type ValueType = 'seconds' | 'minsec' | 'count' | 'cm_signed'
export type Direction = 'higher' | 'lower_is_better'

export interface Region {
  id: number
  name: string
  code: string
}

export interface District {
  id: number
  name: string
  region: number
}

export interface Organization {
  id: number
  name: string
  type: OrgType
  region: number
  district: number | null
}

export interface SportType {
  id: number
  name: string
  code: string
}

export interface AgeCategory {
  id: number
  ordinal: number
  name: string
  age_min: number
  age_max: number
}

export interface Exercise {
  id: number
  name: string
  unit: string
  value_type: ValueType
  direction: Direction
  order: number
  is_active: boolean
}

export interface BatteryItem {
  order: number
  exercise: Exercise
}

export interface TestBattery {
  id: number
  age_category: number
  gender: Gender
  is_active: boolean
  items: BatteryItem[]
}

export interface NormBand {
  points: number
  lower_bound: number | null
  upper_bound: number | null
}

export interface Norm {
  id: number
  exercise: Exercise
  age_min: number
  age_max: number
  gender: Gender
  valid_from: string
  is_active: boolean
  bands: NormBand[]
}

/** Write shape — `exercise` is a PK and bands are nested (API.md §4; replaced atomically). */
export interface NormWrite {
  exercise: number
  age_min: number
  age_max: number
  gender: Gender
  valid_from: string
  is_active: boolean
  bands: NormBand[]
}

export interface DarajaThreshold {
  id: number
  level: DarajaLevel
  total_min: number
  total_max: number
}

/** DRF PageNumberPagination envelope. */
export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
