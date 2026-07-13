<script setup lang="ts">
import Select from 'primevue/select'
import { onMounted, ref } from 'vue'

import { getCoaches } from '@/api/users'

const model = defineModel<number | null>()
defineProps<{ placeholder?: string }>()

const options = ref<{ id: number; label: string }[]>([])
onMounted(async () => {
  const coaches = await getCoaches()
  options.value = coaches.map((c) => ({ id: c.id, label: c.full_name || c.username }))
})
</script>

<template>
  <Select
    v-model="model"
    :options="options"
    option-label="label"
    option-value="id"
    :placeholder="placeholder ?? $t('common.fields.coach')"
    filter
    show-clear
    fluid
  />
</template>
