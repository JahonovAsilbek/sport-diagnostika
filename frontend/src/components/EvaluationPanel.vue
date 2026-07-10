<script setup lang="ts">
import Chart from 'primevue/chart'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Message from 'primevue/message'
import { computed, onMounted, ref } from 'vue'

import { listEvaluations } from '@/api/evaluations'
import DarajaBadge from '@/components/DarajaBadge.vue'
import { useCatalogStore } from '@/stores/catalog'
import type { Evaluation } from '@/types/measurement'

// Latest result (FRNTND-16) + trend + history (FRNTND-17) for one athlete.
const props = defineProps<{ athleteId: number }>()

const catalog = useCatalogStore()
const evaluations = ref<Evaluation[]>([])
const loading = ref(true)

const latest = computed<Evaluation | null>(() => evaluations.value[0] ?? null)

function exName(id: number): string {
  return catalog.exercises.find((e) => e.id === id)?.name ?? `#${id}`
}

const chartData = computed(() => {
  const asc = [...evaluations.value].reverse() // oldest → newest
  return {
    labels: asc.map((e) => e.session_date),
    datasets: [
      {
        label: 'Umumiy ball',
        data: asc.map((e) => e.physical_total),
        borderColor: '#10b981',
        backgroundColor: '#10b98133',
        tension: 0.3,
        fill: false,
      },
    ],
  }
})
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: { y: { min: 0, max: 50 } },
  plugins: { legend: { display: false } },
}

onMounted(async () => {
  await catalog.ensureLoaded()
  try {
    const data = await listEvaluations({ athlete: props.athleteId, ordering: '-session_date' })
    evaluations.value = data.results
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-if="loading" class="eval__loading"><i class="pi pi-spin pi-spinner" /></div>
  <Message v-else-if="!latest" severity="info" variant="simple">
    Bu sportchi hali baholanmagan.
  </Message>
  <div v-else class="eval">
    <div class="eval__score">
      <span class="eval__total">{{ latest.physical_total }}</span>
      <span class="eval__max">/ 50</span>
      <DarajaBadge :level="latest.daraja" />
      <span class="eval__date">{{ latest.session_date }}</span>
    </div>

    <DataTable :value="latest.indicators" data-key="exercise" class="eval__table">
      <Column header="Mashq">
        <template #body="{ data }">{{ exName(data.exercise) }}</template>
      </Column>
      <Column field="raw_value" header="Natija" />
      <Column field="points" header="Ball" />
    </DataTable>

    <template v-if="evaluations.length > 1">
      <h4 class="eval__h">Dinamika</h4>
      <div class="eval__chart"><Chart type="line" :data="chartData" :options="chartOptions" /></div>
    </template>

    <h4 class="eval__h">Tarix</h4>
    <DataTable :value="evaluations" data-key="evaluation_id" paginator :rows="8" class="eval__table">
      <Column field="session_date" header="Sana" sortable />
      <Column field="physical_total" header="Ball" sortable />
      <Column header="Daraja">
        <template #body="{ data }"><DarajaBadge :level="data.daraja" /></template>
      </Column>
    </DataTable>
  </div>
</template>

<style scoped>
.eval__loading {
  padding: 2rem;
  text-align: center;
  font-size: 1.5rem;
  color: var(--p-text-muted-color);
}
.eval__score {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.eval__total {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--p-primary-color);
}
.eval__max {
  color: var(--p-text-muted-color);
  margin-right: 0.75rem;
}
.eval__date {
  margin-left: auto;
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
}
.eval__table {
  max-width: 560px;
  margin-bottom: 1rem;
}
.eval__h {
  margin: 1.5rem 0 0.5rem;
}
.eval__chart {
  height: 240px;
  max-width: 640px;
}
</style>
