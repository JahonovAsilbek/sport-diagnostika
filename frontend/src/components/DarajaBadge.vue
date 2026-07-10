<script setup lang="ts">
import Tag from 'primevue/tag'
import { computed } from 'vue'

import { DARAJA_LABELS, DARAJA_SEVERITY, type DarajaLevel } from '@/constants/labels'

// `none` = scored but below daraja III ("Nishonsiz"); null = not evaluated yet.
const props = defineProps<{ level: DarajaLevel | 'none' | null }>()

const label = computed(() => {
  if (props.level === 'none') return 'Nishonsiz'
  if (!props.level) return 'Baholanmagan'
  return DARAJA_LABELS[props.level]
})
const severity = computed(() =>
  props.level && props.level !== 'none' ? DARAJA_SEVERITY[props.level] : 'secondary',
)
</script>

<template>
  <Tag :value="label" :severity="severity" />
</template>
