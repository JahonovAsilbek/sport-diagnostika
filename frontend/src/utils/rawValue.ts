import i18n from '@/i18n'
import type { ValueType } from '@/types/catalog'

// Raw measurement values are entered + stored as strings (the backend parses per value_type).
export function rawPlaceholder(vt: ValueType): string {
  switch (vt) {
    case 'minsec':
      return 'mm:ss' // format token — locale-independent
    case 'seconds':
      return i18n.global.t('measurements.raw.seconds')
    case 'count':
      return i18n.global.t('measurements.raw.count')
    case 'cm_signed':
      return i18n.global.t('measurements.raw.cmSigned')
  }
}

const PATTERNS: Record<ValueType, RegExp> = {
  seconds: /^\d+(\.\d+)?$/,
  minsec: /^\d{1,2}:[0-5]\d$/,
  count: /^\d+$/,
  cm_signed: /^-?\d+(\.\d+)?$/,
}

/** Client-side format check per value_type. Returns a localized error, or null when OK/empty. */
export function validateRaw(vt: ValueType, value: string): string | null {
  const v = value.trim()
  if (v === '') return null
  return PATTERNS[vt].test(v) ? null : i18n.global.t('measurements.raw.formatInvalid')
}

/**
 * Format a stored value back into its entry form. The backend keeps `raw_value` as a
 * `Decimal(8,2)`, so a draft reloads as e.g. "70.00" — which fails the `count` regex and shows
 * ugly trailing zeros. Convert per value_type: count → integer, minsec → "m:ss" (stored as total
 * seconds), seconds/cm_signed → drop trailing zeros. Non-numeric input is returned as-is.
 */
export function formatRaw(vt: ValueType, value: string | number | null | undefined): string {
  const s = String(value ?? '').trim()
  if (s === '') return ''
  const n = Number(s)
  if (!Number.isFinite(n)) return s
  switch (vt) {
    case 'count':
      return String(Math.round(n))
    case 'minsec': {
      const total = Math.round(n)
      return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`
    }
    case 'seconds':
    case 'cm_signed':
      return String(n) // Number() drops trailing zeros: 220.00 → "220", 12.40 → "12.4"
  }
}
