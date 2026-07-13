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
