<script setup lang="ts">
import Select from 'primevue/select'

import { GENDER_LABELS } from '@/constants/labels'
import type { Gender } from '@/types/catalog'

const model = defineModel<Gender | null>()
defineProps<{ placeholder?: string }>()

const options = (Object.keys(GENDER_LABELS) as Gender[]).map((value) => ({
  value,
  label: GENDER_LABELS[value],
}))
</script>

<template>
  <Select
    v-model="model"
    :options="options"
    option-label="label"
    option-value="value"
    :placeholder="placeholder ?? 'Jins'"
    show-clear
    fluid
  />
</template>
