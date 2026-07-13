<script setup lang="ts">
import Chart from 'primevue/chart'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Message from 'primevue/message'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { listEvaluations } from '@/api/evaluations'
import DarajaBadge from '@/components/DarajaBadge.vue'
import PeriodSelector from '@/components/PeriodSelector.vue'
import { cleanPeriod, type PeriodParams } from '@/composables/usePeriodQuery'
import { useCatalogStore } from '@/stores/catalog'
import type { Evaluation } from '@/types/measurement'

// Latest result (FRNTND-16) + trend + history (FRNTND-17) for one athlete.
const props = defineProps<{ athleteId: number }>()

const catalog = useCatalogStore()
const { t } = useI18n({ useScope: 'global' })
const evaluations = ref<Evaluation[]>([])
const loading = ref(true)
// Local period filter (FRNTND-26) — narrows the history to evaluations within the range.
const period = ref<PeriodParams>({})

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
        label: t('measurements.evaluation.totalScore'),
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

async function load() {
  loading.value = true
  try {
    const data = await listEvaluations({
      athlete: props.athleteId,
      ordering: '-session_date',
      ...cleanPeriod(period.value),
    })
    // Newest first, deterministically — several evaluations can share a session_date, so break the
    // tie by evaluation_id (higher = created later = more recent).
    evaluations.value = data.results
      .slice()
      .sort(
        (a, b) =>
          b.session_date.localeCompare(a.session_date) || b.evaluation_id - a.evaluation_id,
      )
  } finally {
    loading.value = false
  }
}

function onPeriodChange(value: PeriodParams) {
  period.value = value
  load()
}

onMounted(async () => {
  await catalog.ensureLoaded()
  await load()
})
</script>

<template>
  <div class="eval-panel">
    <div class="eval-panel__period">
      <PeriodSelector :model-value="period" @update:model-value="onPeriodChange" />
    </div>
    <div v-if="loading" class="eval__loading"><i class="pi pi-spin pi-spinner" /></div>
    <Message v-else-if="!latest" severity="info" variant="simple">
      {{ $t('measurements.evaluation.notEvaluated') }}
    </Message>
    <div v-else class="eval">
      <div class="eval__score">
        <span class="eval__total">{{ latest.physical_total }}</span>
        <span class="eval__max">/ 50</span>
        <DarajaBadge :level="latest.daraja" />
        <span class="eval__date">{{ latest.session_date }}</span>
      </div>

      <DataTable :value="latest.indicators" data-key="exercise" class="eval__table">
        <Column :header="$t('measurements.cols.exercise')">
          <template #body="{ data }">{{ exName(data.exercise) }}</template>
        </Column>
        <Column field="raw_value" :header="$t('measurements.cols.result')" />
        <Column field="points" :header="$t('measurements.cols.points')" />
      </DataTable>

      <template v-if="evaluations.length > 1">
        <h4 class="eval__h">{{ $t('measurements.evaluation.dynamics') }}</h4>
        <div class="eval__chart">
          <Chart type="line" :data="chartData" :options="chartOptions" />
        </div>
      </template>

      <h4 class="eval__h">{{ $t('measurements.evaluation.history') }}</h4>
      <DataTable
        :value="evaluations"
        data-key="evaluation_id"
        paginator
        :rows="8"
        class="eval__table"
      >
        <Column field="session_date" :header="$t('common.fields.date')" sortable />
        <Column field="physical_total" :header="$t('measurements.cols.points')" sortable />
        <Column :header="$t('measurements.evaluation.levelCol')">
          <template #body="{ data }"><DarajaBadge :level="data.daraja" /></template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>

<style scoped>
.eval-panel__period {
  margin-bottom: 1rem;
}
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
  position: relative; /* constrain the chart.js canvas to the 240px box (else it overflows) */
  height: 240px;
  max-width: 640px;
  margin-bottom: 1rem;
}
</style>
