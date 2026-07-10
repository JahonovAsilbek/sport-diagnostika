<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable, {
  type DataTablePageEvent,
  type DataTableSortEvent,
} from 'primevue/datatable'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'
import { useToast } from 'primevue/usetoast'
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { type AthleteFilters, listAthletes } from '@/api/athletes'
import { toMessage } from '@/api/client'
import AgeCategorySelect from '@/components/pickers/AgeCategorySelect.vue'
import GenderSelect from '@/components/pickers/GenderSelect.vue'
import RegionSelect from '@/components/pickers/RegionSelect.vue'
import SportSelect from '@/components/pickers/SportSelect.vue'
import PageHeader from '@/components/PageHeader.vue'
import { GENDER_LABELS } from '@/constants/labels'
import { useAuthStore } from '@/stores/auth'
import { useCatalogStore } from '@/stores/catalog'
import type { Athlete } from '@/types/athlete'
import type { Gender } from '@/types/catalog'
import { canWrite } from '@/utils/permissions'

const router = useRouter()
const auth = useAuthStore()
const catalog = useCatalogStore()
const toast = useToast()

const PAGE_SIZE = 25
const rows = ref<Athlete[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const ordering = ref('last_name')

const filters = reactive({
  search: '',
  region: null as number | null,
  sport_type: null as number | null,
  gender: null as Gender | null,
  age_category: null as number | null,
})

async function load() {
  loading.value = true
  try {
    const params: AthleteFilters = { ...filters, ordering: ordering.value, page: page.value }
    const data = await listAthletes(params)
    rows.value = data.results
    total.value = data.count
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Xatolik', detail: toMessage(e), life: 4000 })
  } finally {
    loading.value = false
  }
}

function reload() {
  page.value = 1
  load()
}

let searchTimer: ReturnType<typeof setTimeout> | undefined
function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(reload, 350)
}

function onPage(event: DataTablePageEvent) {
  page.value = event.page + 1
  load()
}

function onSort(event: DataTableSortEvent) {
  const field = event.sortField as string | undefined
  ordering.value = field ? `${event.sortOrder === -1 ? '-' : ''}${field}` : 'last_name'
  reload()
}

const regionName = (id: number | null) =>
  id ? (catalog.regions.find((r) => r.id === id)?.name ?? '—') : '—'
const sportName = (id: number | null) =>
  id ? (catalog.sportTypes.find((s) => s.id === id)?.name ?? '—') : '—'

onMounted(() => {
  catalog.ensureLoaded()
  load()
})
</script>

<template>
  <div>
    <PageHeader title="Sportchilar" subtitle="Ro'yxat va filtrlar">
      <template #actions>
        <Button
          v-if="canWrite(auth.role)"
          label="Yangi sportchi"
          icon="pi pi-plus"
          @click="router.push('/athletes/new')"
        />
      </template>
    </PageHeader>

    <div class="athletes__filters">
      <IconField class="athletes__search">
        <InputIcon class="pi pi-search" />
        <InputText v-model="filters.search" placeholder="Ism boʻyicha qidirish" @input="onSearch" />
      </IconField>
      <RegionSelect v-model="filters.region" @update:model-value="reload" />
      <SportSelect v-model="filters.sport_type" @update:model-value="reload" />
      <GenderSelect v-model="filters.gender" @update:model-value="reload" />
      <AgeCategorySelect v-model="filters.age_category" @update:model-value="reload" />
    </div>

    <DataTable
      :value="rows"
      :loading="loading"
      lazy
      paginator
      :rows="PAGE_SIZE"
      :total-records="total"
      :first="(page - 1) * PAGE_SIZE"
      data-key="id"
      row-hover
      class="athletes__table"
      @page="onPage"
      @sort="onSort"
      @row-click="router.push(`/athletes/${$event.data.id}`)"
    >
      <template #empty>Sportchi topilmadi.</template>
      <Column field="last_name" header="F.I.O" sortable>
        <template #body="{ data }">
          <span class="athletes__name">{{ data.full_name }}</span>
        </template>
      </Column>
      <Column field="birth_year" header="Tugʻ. yili" sortable />
      <Column header="Jins">
        <template #body="{ data }">{{ GENDER_LABELS[data.gender as Gender] }}</template>
      </Column>
      <Column header="Sport">
        <template #body="{ data }">{{ sportName(data.sport_type) }}</template>
      </Column>
      <Column header="Viloyat">
        <template #body="{ data }">{{ regionName(data.region) }}</template>
      </Column>
      <Column header="TOIFA">
        <template #body="{ data }">{{ data.age_category?.name ?? '—' }}</template>
      </Column>
      <Column header="Blok">
        <template #body="{ data }">{{ data.block ?? '—' }}</template>
      </Column>
    </DataTable>
  </div>
</template>

<style scoped>
.athletes__filters {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}
.athletes__filters > * {
  min-width: 180px;
  flex: 1 1 180px;
}
.athletes__search {
  flex: 2 1 220px;
}
.athletes__name {
  font-weight: 500;
  color: var(--p-primary-color);
}
.athletes__table :deep(tbody tr) {
  cursor: pointer;
}
</style>
