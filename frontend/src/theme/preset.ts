import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'

// The SPA theme, adopting the premium/ landing's visual language (premium/assets/css/base.css):
// an electric-cyan primary over deep-navy surfaces, dark by default. Built on Aura so every
// PrimeVue component inherits the full token graph — we only override the palette + the dark
// color scheme.

// Cyan primary, anchored on the premium tokens: 500 = --color-primary (#00D4FF),
// 700 = --color-primary-700 (#0099B5).
const primary = {
  50: '#e6fbff',
  100: '#c0f4ff',
  200: '#8aecff',
  300: '#4ee1ff',
  400: '#1ad8ff',
  500: '#00d4ff',
  600: '#00acd1',
  700: '#0099b5',
  800: '#077991',
  900: '#0e5f73',
  950: '#063d4b',
}

// Deep-navy surfaces. In dark mode PrimeVue reads the higher indexes as darker backgrounds:
// 950 = ground/page (--color-bg), 900 = content/cards (--color-bg-elev), 800 = soft/elevated,
// 700 = borders; low indexes are text.
const surface = {
  0: '#ffffff',
  50: '#e6eefb', // --color-text
  100: '#cbd8ee',
  200: '#9aa8c2', // --color-text-muted
  300: '#6a7894', // --color-text-dim
  400: '#4c5b7c',
  500: '#354566',
  600: '#26374f',
  700: '#1f3354', // --color-border
  800: '#15243c', // --color-bg-soft
  900: '#0e1b30', // --color-bg-elev
  950: '#07101f', // --color-bg
}

export const SportPreset = definePreset(Aura, {
  semantic: {
    primary,
    focusRing: { width: '2px', style: 'solid', color: '{primary.color}', offset: '2px' },
    colorScheme: {
      dark: {
        surface,
        primary: {
          color: '{primary.500}',
          contrastColor: '#04111e', // dark text on cyan (premium .btn-primary)
          hoverColor: '{primary.400}',
          activeColor: '{primary.600}',
        },
        highlight: {
          background: 'color-mix(in srgb, {primary.500}, transparent 86%)',
          focusBackground: 'color-mix(in srgb, {primary.500}, transparent 78%)',
          color: '{primary.300}',
          focusColor: '{primary.200}',
        },
      },
    },
  },
})
