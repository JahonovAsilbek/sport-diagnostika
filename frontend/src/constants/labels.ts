// Non-translated enum concerns that must stay out of i18n: the daraja level type and its PrimeVue
// Tag severities (colors are locale-independent). All localized enum LABELS now live in
// src/i18n/ — the reactive helpers in src/i18n/labels.ts, backed by src/i18n/locales/enums.ts.
export type DarajaLevel = 'I' | 'II' | 'III'

// PrimeVue Tag severities — daraja I (best) → green, II → amber, III → red.
export type Severity = 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast'

export const DARAJA_SEVERITY: Record<DarajaLevel, Severity> = {
  I: 'success',
  II: 'warn',
  III: 'danger',
}
