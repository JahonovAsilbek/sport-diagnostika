<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { toMessage } from '@/api/client'
import {
  createReport,
  downloadReport,
  listReports,
  REPORT_FORMAT_LABELS,
  REPORT_STATUS_SEVERITY,
  type Report,
  type ReportFormat,
  type ReportStatus,
  type ReportType,
} from '@/api/reports'
import AgeCategorySelect from '@/components/pickers/AgeCategorySelect.vue'
import AthleteAutocomplete from '@/components/pickers/AthleteAutocomplete.vue'
import GenderSelect from '@/components/pickers/GenderSelect.vue'
import RegionSelect from '@/components/pickers/RegionSelect.vue'
import SportSelect from '@/components/pickers/SportSelect.vue'
import PageHeader from '@/components/PageHeader.vue'
import PeriodSelector from '@/components/PeriodSelector.vue'
import { cleanPeriod, type PeriodParams } from '@/composables/usePeriodQuery'
import { genderLabel, reportStatusLabel, reportTypeLabel } from '@/i18n/labels'
import { useCatalogStore } from '@/stores/catalog'
import type { Athlete } from '@/types/athlete'
import type { Gender } from '@/types/catalog'

const toast = useToast()
const catalog = useCatalogStore()
const { t } = useI18n({ useScope: 'global' })

const REPORT_TYPES: ReportType[] = ['athlete', 'region', 'sport', 'republic']
const typeOptions = computed(() =>
  REPORT_TYPES.map((rt) => ({ label: reportTypeLabel(rt), value: rt })),
)
const formatOptions = (Object.keys(REPORT_FORMAT_LABELS) as ReportFormat[]).map((f) => ({
  label: REPORT_FORMAT_LABELS[f],
  value: f,
}))

const type = ref<ReportType>('athlete')
const format = ref<ReportFormat>('pdf')
const athlete = ref<Athlete | null>(null)
// Optional period (BCKND-70) — travels inside the report's params; validated server-side at request.
const period = ref<PeriodParams>({})
const filters = reactive({
  region: null as number | null,
  sport_type: null as number | null,
  age_category: null as number | null,
  gender: null as Gender | null,
})
const submitting = ref(false)

const reports = ref<Report[]>([])
const loading = ref(false)
const downloadingId = ref<number | null>(null)
let pollTimer: ReturnType<typeof setTimeout> | undefined

// The athlete report needs one athlete; the ranking/republic reports take optional filters.
const isAthlete = computed(() => type.value === 'athlete')

function buildParams(): Record<string, number | string> {
  const params: Record<string, number | string> = {}
  // Period applies to every report type (athlete history + rankings).
  const p = cleanPeriod(period.value)
  if (p.period_type) params.period_type = p.period_type
  if (p.period_year) params.period_year = p.period_year
  if (p.period_index) params.period_index = p.period_index

  if (isAthlete.value) {
    if (athlete.value) params.athlete = athlete.value.id
    return params
  }
  if (filters.region) params.region = filters.region
  if (filters.sport_type) params.sport_type = filters.sport_type
  if (filters.age_category) params.age_category = filters.age_category
  if (filters.gender) params.gender = filters.gender
  return params
}

async function submit() {
  if (isAthlete.value && !athlete.value) {
    toast.add({ severity: 'warn', summary: t('reports.selectAthlete'), life: 3000 })
    return
  }
  submitting.value = true
  try {
    await createReport({ type: type.value, format: format.value, params: buildParams() })
    toast.add({ severity: 'success', summary: t('reports.requestAccepted'), life: 2500 })
    await refresh()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: toMessage(e), life: 5000 })
  } finally {
    submitting.value = false
  }
}

function schedulePoll() {
  clearTimeout(pollTimer)
  const active = reports.value.some((r) => r.status === 'pending' || r.status === 'processing')
  if (active) pollTimer = setTimeout(refresh, 2500)
}

async function refresh() {
  loading.value = true
  try {
    reports.value = (await listReports()).results
    schedulePoll()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: toMessage(e), life: 4000 })
  } finally {
    loading.value = false
  }
}

async function download(report: Report) {
  downloadingId.value = report.id
  try {
    const { blob, filename } = await downloadReport(report.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    toast.add({ severity: 'error', summary: t('reports.downloadFailed'), detail: toMessage(e), life: 4000 })
  } finally {
    downloadingId.value = null
  }
}

function paramsSummary(r: Report): string {
  const p = r.params
  if (r.type === 'athlete') return p.athlete ? t('reports.athleteRef', { id: p.athlete }) : '—'
  const parts: string[] = []
  if (p.region) parts.push(catalog.regions.find((x) => x.id === p.region)?.name ?? `#${p.region}`)
  if (p.sport_type)
    parts.push(catalog.sportTypes.find((x) => x.id === p.sport_type)?.name ?? `#${p.sport_type}`)
  if (p.age_category)
    parts.push(catalog.ageCategories.find((x) => x.id === p.age_category)?.name ?? '')
  if (p.gender) parts.push(genderLabel(p.gender as Gender))
  return parts.filter(Boolean).join(' · ') || t('common.all')
}

onMounted(() => {
  catalog.ensureLoaded()
  refresh()
})
onUnmounted(() => clearTimeout(pollTimer))
</script>

<template>
  <div>
    <PageHeader :title="$t('nav.reports')" :subtitle="$t('reports.subtitle')" />

    <div class="rep__form">
      <div class="rep__field">
        <label>{{ $t('reports.type') }}</label>
        <Select v-model="type" :options="typeOptions" option-label="label" option-value="value" fluid />
      </div>
      <div class="rep__field">
        <label>{{ $t('reports.format') }}</label>
        <Select v-model="format" :options="formatOptions" option-label="label" option-value="value" fluid />
      </div>
      <div class="rep__field rep__field--wide">
        <label>{{ $t('period.label') }}</label>
        <PeriodSelector v-model="period" />
      </div>

      <div v-if="isAthlete" class="rep__field rep__field--wide">
        <label>{{ $t('common.fields.athlete') }}</label>
        <AthleteAutocomplete v-model="athlete" />
      </div>
      <template v-else>
        <div class="rep__field"><label>{{ $t('common.fields.region') }}</label><RegionSelect v-model="filters.region" /></div>
        <div class="rep__field"><label>{{ $t('common.fields.sport') }}</label><SportSelect v-model="filters.sport_type" /></div>
        <div class="rep__field">
          <label>{{ $t('common.fields.ageCategory') }}</label><AgeCategorySelect v-model="filters.age_category" />
        </div>
        <div class="rep__field"><label>{{ $t('common.fields.gender') }}</label><GenderSelect v-model="filters.gender" /></div>
      </template>

      <Button
        :label="$t('reports.request')"
        icon="pi pi-file-export"
        class="rep__submit"
        :loading="submitting"
        @click="submit"
      />
    </div>

    <DataTable :value="reports" :loading="loading" data-key="id" paginator :rows="10" class="rep__table">
      <template #empty>{{ $t('reports.empty') }}</template>
      <Column field="id" header="#" class="rep__id" />
      <Column :header="$t('reports.type')">
        <template #body="{ data }">{{ reportTypeLabel(data.type as ReportType) }}</template>
      </Column>
      <Column :header="$t('reports.format')">
        <template #body="{ data }">{{ REPORT_FORMAT_LABELS[data.format as ReportFormat] }}</template>
      </Column>
      <Column :header="$t('reports.params')">
        <template #body="{ data }"><span class="rep__params">{{ paramsSummary(data) }}</span></template>
      </Column>
      <Column :header="$t('common.fields.status')">
        <template #body="{ data }">
          <Tag
            :value="reportStatusLabel(data.status as ReportStatus)"
            :severity="REPORT_STATUS_SEVERITY[data.status as ReportStatus]"
          />
          <i
            v-if="data.status === 'pending' || data.status === 'processing'"
            class="pi pi-spin pi-spinner rep__spin"
          />
          <small v-if="data.status === 'failed' && data.error" class="rep__err">{{ data.error }}</small>
        </template>
      </Column>
      <Column header="" class="rep__actions">
        <template #body="{ data }">
          <Button
            :label="$t('common.download')"
            icon="pi pi-download"
            size="small"
            :disabled="data.status !== 'done'"
            :loading="downloadingId === data.id"
            @click="download(data)"
          />
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<style scoped>
.rep__form {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  align-items: flex-end;
  padding: 1rem;
  border: 1px solid var(--p-content-border-color, #e2e8f0);
  border-radius: 12px;
  margin-bottom: 1.5rem;
}
.rep__field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  flex: 1 1 160px;
  min-width: 150px;
}
.rep__field--wide {
  flex: 2 1 260px;
}
.rep__field label {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--p-text-muted-color);
}
.rep__submit {
  flex: 0 0 auto;
}
.rep__id {
  width: 3.5rem;
}
.rep__params {
  color: var(--p-text-muted-color);
}
.rep__spin {
  margin-left: 0.5rem;
  color: var(--p-text-muted-color);
}
.rep__err {
  display: block;
  color: var(--p-red-500, #ef4444);
  margin-top: 0.25rem;
}
.rep__actions {
  width: 11rem;
  text-align: right;
}
</style>
