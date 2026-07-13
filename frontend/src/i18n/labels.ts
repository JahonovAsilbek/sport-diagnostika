// Enum → localized label helpers. The backend speaks stable English enum values; these render the
// locale-appropriate text. Functions (not const maps) so they re-resolve on locale change and stay
// callable from plain .ts modules (api/*) as well as templates/computeds — reactivity comes from
// i18n.global.t reading the reactive locale.
import type { ReportStatus, ReportType } from '@/api/reports'
import type { DarajaLevel } from '@/constants/labels'
import type { Role } from '@/types/auth'
import type { Direction, Gender, OrgType, ValueType } from '@/types/catalog'

import i18n from './index'

// Call as a method on the global composer so `this` binding survives (don't destructure `t`).
const tr = (key: string): string => i18n.global.t(key)

export function roleLabel(role: Role | null | undefined): string {
  return role ? tr(`enums.role.${role}`) : '—'
}

export function darajaLabel(level: DarajaLevel): string {
  return tr(`enums.daraja.${level}`)
}

export function genderLabel(gender: Gender): string {
  return tr(`enums.gender.${gender}`)
}

export function orgTypeLabel(type: OrgType): string {
  return tr(`enums.orgType.${type}`)
}

export function valueTypeLabel(valueType: ValueType): string {
  return tr(`enums.valueType.${valueType}`)
}

export function directionLabel(direction: Direction): string {
  return tr(`enums.direction.${direction}`)
}

export function reportTypeLabel(type: ReportType): string {
  return tr(`enums.reportType.${type}`)
}

export function reportStatusLabel(status: ReportStatus): string {
  return tr(`enums.reportStatus.${status}`)
}
