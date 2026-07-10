<script setup lang="ts">
import Tag from 'primevue/tag'
import { computed } from 'vue'

import { DARAJA_LABELS, DARAJA_SEVERITY, type DarajaLevel } from '@/constants/labels'

const props = defineProps<{ level: DarajaLevel | null }>()

const label = computed(() => (props.level ? DARAJA_LABELS[props.level] : 'Baholanmagan'))
const severity = computed(() => (props.level ? DARAJA_SEVERITY[props.level] : 'secondary'))
</script>

<template>
  <Tag :value="label" :severity="severity" />
</template>
