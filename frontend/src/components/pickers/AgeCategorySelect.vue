<script setup lang="ts">
import Select from 'primevue/select'
import { computed, onMounted } from 'vue'

import { useCatalogStore } from '@/stores/catalog'

const model = defineModel<number | null>()
defineProps<{ placeholder?: string }>()

const catalog = useCatalogStore()
onMounted(() => catalog.ensureLoaded())

// Label each category with its age span, e.g. "TOIFA 3 (10–11 yosh)".
const options = computed(() =>
  catalog.ageCategories.map((c) => ({
    id: c.id,
    label: `${c.name} (${c.age_min}–${c.age_max} yosh)`,
  })),
)
</script>

<template>
  <Select
    v-model="model"
    :options="options"
    option-label="label"
    option-value="id"
    :placeholder="placeholder ?? 'Yosh toifasi'"
    show-clear
    fluid
  />
</template>
