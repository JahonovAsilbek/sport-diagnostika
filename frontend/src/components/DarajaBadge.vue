<script setup lang="ts">
import Tag from 'primevue/tag'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { DARAJA_SEVERITY, type DarajaLevel } from '@/constants/labels'
import { darajaLabel } from '@/i18n/labels'

// `none` = scored but below daraja III ("Nishonsiz"); null = not evaluated yet.
const props = defineProps<{ level: DarajaLevel | 'none' | null }>()

const { t } = useI18n({ useScope: 'global' })
const label = computed(() => {
  if (props.level === 'none') return t('enums.daraja.none')
  if (!props.level) return t('enums.daraja.notEvaluated')
  return darajaLabel(props.level)
})
const severity = computed(() =>
  props.level && props.level !== 'none' ? DARAJA_SEVERITY[props.level] : 'secondary',
)
</script>

<template>
  <Tag :value="label" :severity="severity" />
</template>
