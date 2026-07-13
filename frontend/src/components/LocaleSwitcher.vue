<script setup lang="ts">
import Select from 'primevue/select'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { LOCALE_META, SUPPORTED_LOCALES, setLocale, type Locale } from '@/i18n'

const { locale } = useI18n({ useScope: 'global' })

const options = SUPPORTED_LOCALES.map((value) => ({ value, ...LOCALE_META[value] }))

const current = computed<Locale>({
  get: () => locale.value as Locale,
  set: (value) => setLocale(value),
})
</script>

<template>
  <Select
    v-model="current"
    :options="options"
    option-label="label"
    option-value="value"
    :aria-label="$t('nav.language')"
    class="locale-switcher"
  >
    <template #value="{ value }">
      <span class="locale-switcher__code">{{ LOCALE_META[value as Locale]?.short ?? value }}</span>
    </template>
    <template #option="{ option }">
      <span class="locale-switcher__opt">
        <strong>{{ option.short }}</strong>
        <span>{{ option.label }}</span>
      </span>
    </template>
  </Select>
</template>

<style scoped>
.locale-switcher {
  min-width: 5rem;
}
.locale-switcher__code {
  font-weight: 600;
  font-size: 0.85rem;
}
.locale-switcher__opt {
  display: inline-flex;
  align-items: baseline;
  gap: 0.5rem;
}
.locale-switcher__opt strong {
  min-width: 1.75rem;
  color: var(--p-text-muted-color);
}
</style>
