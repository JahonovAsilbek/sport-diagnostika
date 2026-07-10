<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'

import { toMessage } from '@/api/client'
import {
  createReport,
  downloadReport,
  listReports,
  REPORT_FORMAT_LABELS,
  REPORT_STATUS_LABELS,
  REPORT_STATUS_SEVERITY,
  REPORT_TYPE_LABELS,
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
import { GENDER_LABELS } from '@/constants/labels'
import { useCatalogStore } from '@/stores/catalog'
import type { Athlete } from '@/types/athlete'
import type { Gender } from '@/types/catalog'

const toast = useToast()
const catalog = useCatalogStore()

const typeOptions = (Object.keys(REPORT_TYPE_LABELS) as ReportType[]).map((t) => ({
  label: REPORT_TYPE_LABELS[t],
  value: t,
}))
const formatOptions = (Object.keys(REPORT_FORMAT_LABELS) as ReportFormat[]).map((f) => ({
  label: REPORT_FORMAT_LABELS[f],
  value: f,
}))

const type = ref<ReportType>('athlete')
const format = ref<ReportFormat>('pdf')
const athlete = ref<Athlete | null>(null)
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
  if (isAthlete.value) return athlete.value ? { athlete: athlete.value.id } : {}
  const params: Record<string, number | string> = {}
  if (filters.region) params.region = filters.region
  if (filters.sport_type) params.sport_type = filters.sport_type
  if (filters.age_category) params.age_category = filters.age_category
  if (filters.gender) params.gender = filters.gender
  return params
}

async function submit() {
  if (isAthlete.value && !athlete.value) {
    toast.add({ severity: 'warn', summary: 'Sportchi tanlang', life: 3000 })
    return
  }
  submitting.value = true
  try {
    await createReport({ type: type.value, format: format.value, params: buildParams() })
    toast.add({ severity: 'success', summary: 'Soʻrov qabul qilindi', life: 2500 })
    await refresh()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Xatolik', detail: toMessage(e), life: 5000 })
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
    toast.add({ severity: 'error', summary: 'Xatolik', detail: toMessage(e), life: 4000 })
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
    toast.add({ severity: 'error', summary: 'Yuklab boʻlmadi', detail: toMessage(e), life: 4000 })
  } finally {
    downloadingId.value = null
  }
}

function paramsSummary(r: Report): string {
  const p = r.params
  if (r.type === 'athlete') return p.athlete ? `Sportchi #${p.athlete}` : '—'
  const parts: string[] = []
  if (p.region) parts.push(catalog.regions.find((x) => x.id === p.region)?.name ?? `#${p.region}`)
  if (p.sport_type)
    parts.push(catalog.sportTypes.find((x) => x.id === p.sport_type)?.name ?? `#${p.sport_type}`)
  if (p.age_category)
    parts.push(catalog.ageCategories.find((x) => x.id === p.age_category)?.name ?? '')
  if (p.gender) parts.push(GENDER_LABELS[p.gender as Gender])
  return parts.filter(Boolean).join(' · ') || 'Barchasi'
}

onMounted(() => {
  catalog.ensureLoaded()
  refresh()
})
onUnmounted(() => clearTimeout(pollTimer))
</script>

<template>
  <div>
    <PageHeader title="Hisobotlar" subtitle="Hisobot soʻrang va tayyor boʻlganda yuklab oling" />

    <div class="rep__form">
      <div class="rep__field">
        <label>Turi</label>
        <Select v-model="type" :options="typeOptions" option-label="label" option-value="value" fluid />
      </div>
      <div class="rep__field">
        <label>Format</label>
        <Select v-model="format" :options="formatOptions" option-label="label" option-value="value" fluid />
      </div>

      <div v-if="isAthlete" class="rep__field rep__field--wide">
        <label>Sportchi</label>
        <AthleteAutocomplete v-model="athlete" />
      </div>
      <template v-else>
        <div class="rep__field"><label>Viloyat</label><RegionSelect v-model="filters.region" /></div>
        <div class="rep__field"><label>Sport</label><SportSelect v-model="filters.sport_type" /></div>
        <div class="rep__field">
          <label>TOIFA</label><AgeCategorySelect v-model="filters.age_category" />
        </div>
        <div class="rep__field"><label>Jins</label><GenderSelect v-model="filters.gender" /></div>
      </template>

      <Button
        label="Soʻrash"
        icon="pi pi-file-export"
        class="rep__submit"
        :loading="submitting"
        @click="submit"
      />
    </div>

    <DataTable :value="reports" :loading="loading" data-key="id" paginator :rows="10" class="rep__table">
      <template #empty>Hali hisobot soʻralmagan.</template>
      <Column field="id" header="#" class="rep__id" />
      <Column header="Turi">
        <template #body="{ data }">{{ REPORT_TYPE_LABELS[data.type as ReportType] }}</template>
      </Column>
      <Column header="Format">
        <template #body="{ data }">{{ REPORT_FORMAT_LABELS[data.format as ReportFormat] }}</template>
      </Column>
      <Column header="Parametrlar">
        <template #body="{ data }"><span class="rep__params">{{ paramsSummary(data) }}</span></template>
      </Column>
      <Column header="Holat">
        <template #body="{ data }">
          <Tag
            :value="REPORT_STATUS_LABELS[data.status as ReportStatus]"
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
            label="Yuklab olish"
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
