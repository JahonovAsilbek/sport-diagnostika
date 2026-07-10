<script setup lang="ts">
import Chart from 'primevue/chart'
import Message from 'primevue/message'
import { computed, onMounted, ref } from 'vue'

import { getRegionRating, type RegionRatingRow } from '@/api/rating'

// Per-region daraja-I counts (national picture) — only mounted for privileged roles. Self-fetches
// the same /rating/regions/ the rating view uses.
const rows = ref<RegionRatingRow[]>([])
const loading = ref(true)

const data = computed(() => ({
  labels: rows.value.map((r) => r.region),
  datasets: [
    { label: 'I daraja', data: rows.value.map((r) => r.daraja_i_count), backgroundColor: '#10b981' },
  ],
}))
const options = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y',
  plugins: { legend: { display: false } },
  scales: { x: { beginAtZero: true, ticks: { precision: 0 } } },
}

onMounted(async () => {
  try {
    rows.value = (await getRegionRating()).results
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-if="loading" class="bars__loading"><i class="pi pi-spin pi-spinner" /></div>
  <Message v-else-if="!rows.length" severity="info" variant="simple">
    Viloyat maʼlumoti yoʻq.
  </Message>
  <div v-else class="bars"><Chart type="bar" :data="data" :options="options" /></div>
</template>

<style scoped>
.bars {
  height: 300px;
}
.bars__loading {
  height: 300px;
  display: grid;
  place-items: center;
  font-size: 1.5rem;
  color: var(--p-text-muted-color);
}
</style>
