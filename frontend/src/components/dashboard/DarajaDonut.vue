<script setup lang="ts">
import Chart from 'primevue/chart'
import Message from 'primevue/message'
import { computed } from 'vue'

import { DARAJA_LABELS, type DarajaLevel } from '@/constants/labels'

// Distribution of athletes across daraja (latest evaluation each). Degrades to an empty-state
// message when there's no evaluation data yet (FRNTND-24: charts degrade gracefully).
const props = defineProps<{ byDaraja: Record<DarajaLevel | 'none', number> }>()

const ORDER: (DarajaLevel | 'none')[] = ['I', 'II', 'III', 'none']
const COLORS: Record<DarajaLevel | 'none', string> = {
  I: '#10b981',
  II: '#f59e0b',
  III: '#ef4444',
  none: '#94a3b8',
}
const LABELS: Record<DarajaLevel | 'none', string> = {
  I: DARAJA_LABELS.I,
  II: DARAJA_LABELS.II,
  III: DARAJA_LABELS.III,
  none: 'Nishonsiz',
}

const total = computed(() => ORDER.reduce((sum, k) => sum + (props.byDaraja[k] || 0), 0))
const data = computed(() => ({
  labels: ORDER.map((k) => LABELS[k]),
  datasets: [
    {
      data: ORDER.map((k) => props.byDaraja[k] || 0),
      backgroundColor: ORDER.map((k) => COLORS[k]),
    },
  ],
}))
const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom' } },
}
</script>

<template>
  <Message v-if="!total" severity="info" variant="simple">Baholash maʼlumoti yoʻq.</Message>
  <div v-else class="donut"><Chart type="doughnut" :data="data" :options="options" /></div>
</template>

<style scoped>
.donut {
  height: 260px;
}
</style>
