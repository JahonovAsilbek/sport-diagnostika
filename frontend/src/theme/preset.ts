import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'

// The SPA theme mirrors the root landing (assets/css/style.css): a clean, minimal LIGHT theme with
// a blue primary. Built on Aura so every PrimeVue component inherits the full token graph — we only
// override the primary palette (500 = the landing's --primary #1d4ed8).
const primary = {
  50: '#eff4ff',
  100: '#dbe4fe',
  200: '#bfd0fe',
  300: '#93aefd',
  400: '#6084fa',
  500: '#1d4ed8',
  600: '#1a45c0',
  700: '#1e40af',
  800: '#1e3a8a',
  900: '#1c3576',
  950: '#131f47',
}

export const SportPreset = definePreset(Aura, {
  semantic: {
    primary,
    focusRing: { width: '2px', style: 'solid', color: '{primary.color}', offset: '2px' },
  },
})
