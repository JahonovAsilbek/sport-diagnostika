<script setup lang="ts">
import Select from 'primevue/select'
import { ref, watch } from 'vue'

import { useCatalogStore } from '@/stores/catalog'
import type { District } from '@/types/catalog'

// Cascade: options depend on the selected region. Clearing/changing the region resets the pick,
// but the initial value (edit forms) is preserved on first load.
const model = defineModel<number | null>()
const props = defineProps<{ region: number | null }>()

const catalog = useCatalogStore()
const districts = ref<District[]>([])
let first = true

watch(
  () => props.region,
  async (region) => {
    if (!first) model.value = null
    first = false
    districts.value = region ? await catalog.districtsFor(region) : []
  },
  { immediate: true },
)
</script>

<template>
  <Select
    v-model="model"
    :options="districts"
    option-label="name"
    option-value="id"
    :disabled="!region"
    placeholder="Tuman"
    filter
    show-clear
    fluid
  />
</template>
