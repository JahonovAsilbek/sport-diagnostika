<script setup lang="ts">
import Select from 'primevue/select'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import { useCatalogStore } from '@/stores/catalog'

const model = defineModel<number | null>()
defineProps<{ placeholder?: string }>()

const catalog = useCatalogStore()
const { t } = useI18n({ useScope: 'global' })
onMounted(() => catalog.ensureLoaded())

// Label each category with its age span, e.g. "TOIFA 3 (10–11 yosh)". The name is domain content
// (kept Uzbek); only the age-span suffix is localized.
const options = computed(() =>
  catalog.ageCategories.map((c) => ({
    id: c.id,
    label: `${c.name} (${t('common.ageSpan', { min: c.age_min, max: c.age_max })})`,
  })),
)
</script>

<template>
  <Select
    v-model="model"
    :options="options"
    option-label="label"
    option-value="id"
    :placeholder="placeholder ?? $t('common.fields.ageCategory')"
    show-clear
    fluid
  />
</template>
