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
    :options="catalog.sportTypes"
    option-label="name"
    option-value="id"
    :placeholder="placeholder ?? $t('common.fields.sport')"
    filter
    show-clear
    fluid
  />
</template>
