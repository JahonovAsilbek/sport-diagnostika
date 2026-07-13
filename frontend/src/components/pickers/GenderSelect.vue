<script setup lang="ts">
import Select from 'primevue/select'
import { computed } from 'vue'

import { genderLabel } from '@/i18n/labels'
import type { Gender } from '@/types/catalog'

const model = defineModel<Gender | null>()
defineProps<{ placeholder?: string }>()

const GENDERS: Gender[] = ['male', 'female']
// Computed so labels re-resolve when the locale changes.
const options = computed(() => GENDERS.map((value) => ({ value, label: genderLabel(value) })))
</script>

<template>
  <Select
    v-model="model"
    :options="options"
    option-label="label"
    option-value="value"
    :placeholder="placeholder ?? $t('common.fields.gender')"
    show-clear
    fluid
  />
</template>
