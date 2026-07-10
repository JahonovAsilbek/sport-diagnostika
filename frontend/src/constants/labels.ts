// English enum keys → Uzbek display labels. The product UI is Uzbek-facing (CLAUDE.md §4):
// the backend speaks stable English enum values, the UI renders these. Extend per feature.
import type { Role } from '@/types/auth'

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
