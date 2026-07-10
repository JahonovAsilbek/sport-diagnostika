<script setup lang="ts">
import AutoComplete, { type AutoCompleteCompleteEvent } from 'primevue/autocomplete'
import { ref } from 'vue'

import { listAthletes } from '@/api/athletes'
import type { Athlete } from '@/types/athlete'

// Search-as-you-type athlete picker (scoped server-side). Binds the whole Athlete object.
const model = defineModel<Athlete | null>()
const suggestions = ref<Athlete[]>([])

async function search(event: AutoCompleteCompleteEvent) {
  const data = await listAthletes({ search: event.query })
  suggestions.value = data.results
}
</script>

<template>
  <AutoComplete
    v-model="model"
    :suggestions="suggestions"
    option-label="full_name"
    placeholder="Sportchini qidiring"
    dropdown
    fluid
    @complete="search"
  />
</template>
