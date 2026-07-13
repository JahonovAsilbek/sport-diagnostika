<script setup lang="ts">
import Chart from 'primevue/chart'
import Message from 'primevue/message'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { DarajaLevel } from '@/constants/labels'
import { darajaLabel } from '@/i18n/labels'

// Distribution of athletes across daraja (latest evaluation each). Degrades to an empty-state
// message when there's no evaluation data yet (FRNTND-24: charts degrade gracefully).
const props = defineProps<{ byDaraja: Record<DarajaLevel | 'none', number> }>()

const { t } = useI18n({ useScope: 'global' })

const ORDER: (DarajaLevel | 'none')[] = ['I', 'II', 'III', 'none']
const COLORS: Record<DarajaLevel | 'none', string> = {
  I: '#10b981',
  II: '#f59e0b',
  III: '#ef4444',
  none: '#94a3b8',
}
const labelFor = (k: DarajaLevel | 'none') => (k === 'none' ? t('enums.daraja.none') : darajaLabel(k))

const total = computed(() => ORDER.reduce((sum, k) => sum + (props.byDaraja[k] || 0), 0))
const data = computed(() => ({
  labels: ORDER.map((k) => labelFor(k)),
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
  <Message v-if="!total" severity="info" variant="simple">{{ $t('dashboard.noEvaluationData') }}</Message>
  <div v-else class="donut"><Chart type="doughnut" :data="data" :options="options" /></div>
</template>

<style scoped>
.donut {
  height: 260px;
}
</style>
