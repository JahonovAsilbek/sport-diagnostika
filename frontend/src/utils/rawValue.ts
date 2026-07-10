import type { ValueType } from '@/types/catalog'

// Raw measurement values are entered + stored as strings (the backend parses per value_type).
export function rawPlaceholder(vt: ValueType): string {
  switch (vt) {
    case 'minsec':
      return 'mm:ss'
    case 'seconds':
      return 'soniya (mas. 12.4)'
    case 'count':
      return 'son'
    case 'cm_signed':
      return 'sm (± ruxsat)'
  }
}

const PATTERNS: Record<ValueType, RegExp> = {
  seconds: /^\d+(\.\d+)?$/,
  minsec: /^\d{1,2}:[0-5]\d$/,
  count: /^\d+$/,
  cm_signed: /^-?\d+(\.\d+)?$/,
}

/** Client-side format check per value_type. Returns an Uzbek error, or null when OK/empty. */
export function validateRaw(vt: ValueType, value: string): string | null {
  const v = value.trim()
  if (v === '') return null
  return PATTERNS[vt].test(v) ? null : 'Format notoʻgʻri.'
}
