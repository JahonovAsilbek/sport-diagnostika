// Composes the vue-i18n message tree from the per-namespace files in ./locales. Each namespace
// file default-exports `{ uz: {...}, ru: {...}, en: {...} }` (kk omitted → falls back to uz). The
// glob auto-discovers new namespace files, so adding one needs no edit here.
import { SUPPORTED_LOCALES, type Locale } from './config'

type NamespaceMessages = Record<string, unknown>
type NamespaceModule = Partial<Record<Locale, NamespaceMessages>>

const modules = import.meta.glob<NamespaceModule>('./locales/*.ts', {
  eager: true,
  import: 'default',
})

function buildMessages(): Record<Locale, Record<string, NamespaceMessages>> {
  const out = Object.fromEntries(SUPPORTED_LOCALES.map((locale) => [locale, {}])) as Record<
    Locale,
    Record<string, NamespaceMessages>
  >

  for (const [path, mod] of Object.entries(modules)) {
    const namespace = path.slice(path.lastIndexOf('/') + 1).replace(/\.ts$/, '')
    for (const locale of SUPPORTED_LOCALES) {
      const messages = mod[locale]
      if (messages) out[locale][namespace] = messages
    }
  }
  return out
}

export const messages = buildMessages()
