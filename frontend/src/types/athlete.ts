import type { AgeCategory, Gender } from '@/types/catalog'

export interface Athlete {
  id: number
  last_name: string
  first_name: string
  middle_name: string | null
  full_name: string
  birth_year: number
  gender: Gender
  region: number | null
  district: number | null
  organization: number | null
  sport_type: number | null
  coach: number | null
  razryad: string | null
  training_experience: number | null
  main_competitions: string | null
  block: string | null // OTM / OPSTTM classification (derived)
  age_category: AgeCategory | null // derived TOIFA at today's date; null if out of range
  is_active: boolean
  created_at: string
}

export interface AthleteWrite {
  last_name: string
  first_name: string
  middle_name?: string | null
  birth_year: number | null
  gender: Gender | null
  region: number | null
  district: number | null
  organization: number | null
  sport_type: number | null
  coach: number | null
  razryad?: string | null
  training_experience?: number | null
  main_competitions?: string | null
  is_active?: boolean
}
