<script setup lang="ts">
import Select from 'primevue/select'
import { ref, watch } from 'vue'

import { getOrganizations } from '@/api/catalog'
import type { Organization } from '@/types/catalog'

// Organizations are scope-dependent and can be many — fetch them filtered by region on demand
// (not cached globally). Falls back to all orgs the caller is allowed to see when region is null.
const model = defineModel<number | null>()
const props = defineProps<{ region?: number | null }>()

const options = ref<Organization[]>([])
const loading = ref(false)
let first = true

watch(
  () => props.region,
  async (region) => {
    if (!first) model.value = null
    first = false
    loading.value = true
    try {
      options.value = await getOrganizations(region ? { region } : undefined)
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)
</script>

<template>
  <Select
    v-model="model"
    :options="options"
    option-label="name"
    option-value="id"
    :loading="loading"
    :placeholder="$t('common.fields.organization')"
    filter
    show-clear
    fluid
  />
</template>
