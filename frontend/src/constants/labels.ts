// English enum keys → Uzbek display labels. The product UI is Uzbek-facing (CLAUDE.md §4):
// the backend speaks stable English enum values, the UI renders these. Extend per feature.
import type { Role } from '@/types/auth'
import type { Direction, Gender, OrgType, ValueType } from '@/types/catalog'

export const ROLE_LABELS: Record<Role, string> = {
  super_admin: 'Super admin',
  region_admin: 'Viloyat admin',
  coach: 'Murabbiy',
  lab_operator: 'Laboratoriya operatori',
  ministry: 'Vazirlik vakili',
}

export function roleLabel(role: Role | null | undefined): string {
  return role ? ROLE_LABELS[role] : '—'
}

export type DarajaLevel = 'I' | 'II' | 'III'

export const DARAJA_LABELS: Record<DarajaLevel, string> = {
  I: 'I daraja',
  II: 'II daraja',
  III: 'III daraja',
}

// PrimeVue Tag severities — daraja I (best) → green, II → amber, III → red.
export type Severity = 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast'

export const DARAJA_SEVERITY: Record<DarajaLevel, Severity> = {
  I: 'success',
  II: 'warn',
  III: 'danger',
}

export const GENDER_LABELS: Record<Gender, string> = {
  male: 'Erkak',
  female: 'Ayol',
}

export const ORG_TYPE_LABELS: Record<OrgType, string> = {
  OTM: 'OTM',
  OPSTTM: 'OPSTTM',
}

export const VALUE_TYPE_LABELS: Record<ValueType, string> = {
  seconds: 'Soniya',
  minsec: 'Daqiqa:soniya',
  count: 'Son',
  cm_signed: 'Santimetr (ishorali)',
}

export const DIRECTION_LABELS: Record<Direction, string> = {
  higher: "Koʻproq — yaxshiroq",
  lower_is_better: 'Kamroq — yaxshiroq',
}
