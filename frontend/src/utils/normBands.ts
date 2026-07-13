import i18n from '@/i18n'
import type { NormBand } from '@/types/catalog'

// Client-side mirror of the backend assert_bands_no_overlap (BCKND-26). Bands are half-open
// [lower, upper) intervals; none may overlap. A null lower = -∞, a null upper = +∞.
export function validateBands(bands: NormBand[]): string[] {
  const errors: string[] = []

  for (const b of bands) {
    if (b.lower_bound !== null && b.upper_bound !== null && b.lower_bound >= b.upper_bound) {
      errors.push(i18n.global.t('catalog.norms.validation.bandBounds', { points: b.points }))
    }
  }

  const sorted = [...bands].sort(
    (a, b) => (a.lower_bound ?? -Infinity) - (b.lower_bound ?? -Infinity),
  )
  for (let i = 1; i < sorted.length; i++) {
    const prevUpper = sorted[i - 1].upper_bound ?? Infinity
    const curLower = sorted[i].lower_bound ?? -Infinity
    if (curLower < prevUpper) {
      errors.push(i18n.global.t('catalog.norms.validation.bandsOverlap'))
      break
    }
  }

  return errors
}
