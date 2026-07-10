<script setup lang="ts">
import Select from 'primevue/select'
import { onMounted } from 'vue'

import { useCatalogStore } from '@/stores/catalog'

const model = defineModel<number | null>()
defineProps<{ placeholder?: string }>()

const catalog = useCatalogStore()
onMounted(() => catalog.ensureLoaded())
</script>

<template>
  <Select
    v-model="model"
    :options="catalog.regions"
    option-label="name"
    option-value="id"
    :placeholder="placeholder ?? 'Viloyat'"
    filter
    show-clear
    fluid
  />
</template>
