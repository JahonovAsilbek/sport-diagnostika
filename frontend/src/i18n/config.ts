// Locale registry — the leaf module of the i18n graph (no imports, so messages.ts and index.ts
// can both depend on it without a cycle). uz is the source of truth and the fallback; ru + en are
// fully translated; kk (Qoraqalpoqcha) ships empty and falls back to uz until a native speaker
// fills it (FRNTND-25 decision).
export const SUPPORTED_LOCALES = ['uz', 'ru', 'kk', 'en'] as const
export type Locale = (typeof SUPPORTED_LOCALES)[number]

export const DEFAULT_LOCALE: Locale = 'uz'
export const LOCALE_STORAGE_KEY = 'locale'

// Endonym + a compact code for the switcher. No flag emojis on purpose: uz and kk share a country,
// so a flag would misrepresent the language.
export const LOCALE_META: Record<Locale, { label: string; short: string }> = {
  uz: { label: 'Oʻzbekcha', short: 'UZ' },
  ru: { label: 'Русский', short: 'RU' },
  kk: { label: 'Qaraqalpaqsha', short: 'KK' },
  en: { label: 'English', short: 'EN' },
}

export function isSupportedLocale(value: string | null | undefined): value is Locale {
  return !!value && (SUPPORTED_LOCALES as readonly string[]).includes(value)
}
