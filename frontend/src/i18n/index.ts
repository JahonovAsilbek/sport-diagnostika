import { createI18n } from 'vue-i18n'

import {
  DEFAULT_LOCALE,
  LOCALE_STORAGE_KEY,
  isSupportedLocale,
  type Locale,
} from './config'
import { messages } from './messages'

export function getStoredLocale(): Locale {
  const stored = localStorage.getItem(LOCALE_STORAGE_KEY)
  return isSupportedLocale(stored) ? stored : DEFAULT_LOCALE
}

const i18n = createI18n({
  legacy: false, // Composition API mode — components use useI18n(); .ts modules use i18n.global.t
  globalInjection: true, // $t available in templates
  locale: getStoredLocale(),
  fallbackLocale: DEFAULT_LOCALE, // missing keys (incl. all of kk) resolve to uz
  messages,
})

export function setLocale(locale: Locale): void {
  i18n.global.locale.value = locale
  localStorage.setItem(LOCALE_STORAGE_KEY, locale)
  document.documentElement.lang = locale
}

// Reflect the initial choice on <html lang> before first paint.
document.documentElement.lang = getStoredLocale()

export default i18n
export { SUPPORTED_LOCALES, DEFAULT_LOCALE, LOCALE_META, isSupportedLocale } from './config'
export type { Locale } from './config'
