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

watch(
  () => props.region,
  async (region, prev) => {
    // Reset the dependent pick only on a real region change — NOT on the initial prefill in edit
    // forms, where region goes undefined/null → the loaded value (which must keep the district).
    if (prev != null && region !== prev) model.value = null
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
    :placeholder="$t('common.fields.district')"
    filter
    show-clear
    fluid
  />
</template>
