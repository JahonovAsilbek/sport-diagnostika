<script setup lang="ts">
import Message from 'primevue/message'
import { onMounted, ref } from 'vue'

import { listRecommendations, type Recommendation } from '@/api/recommendations'

const props = defineProps<{ athleteId: number }>()

const recs = ref<Recommendation[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    recs.value = (await listRecommendations({ athlete: props.athleteId })).results
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-if="loading" class="recs__loading"><i class="pi pi-spin pi-spinner" /></div>
  <Message v-else-if="!recs.length" severity="info" variant="simple">
    {{ $t('recommendations.panel.empty') }}
  </Message>
  <ul v-else class="recs">
    <li v-for="rec in recs" :key="rec.id" class="recs__item">
      <i class="pi pi-lightbulb" />
      <span>{{ rec.text }}</span>
    </li>
  </ul>
</template>

<style scoped>
.recs__loading {
  padding: 1.5rem;
  text-align: center;
  color: var(--p-text-muted-color);
}
.recs {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-width: 640px;
}
.recs__item {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  padding: 0.75rem 1rem;
  background: var(--p-content-hover-background, #f8fafc);
  border-radius: 8px;
}
.recs__item i {
  color: var(--p-yellow-500, #eab308);
  margin-top: 0.15rem;
}
</style>
