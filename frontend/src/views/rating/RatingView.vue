<script setup lang="ts">
import Column from 'primevue/column'
import DataTable, { type DataTablePageEvent } from 'primevue/datatable'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import TabPanel from 'primevue/tabpanel'
import TabPanels from 'primevue/tabpanels'
import Tabs from 'primevue/tabs'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { toMessage } from '@/api/client'
import {
  getRegionRating,
  getTopAthletes,
  listRating,
  type RatingQuery,
  type RatingRow,
  type RegionRatingRow,
} from '@/api/rating'
import DarajaBadge from '@/components/DarajaBadge.vue'
import PageHeader from '@/components/PageHeader.vue'
import AgeCategorySelect from '@/components/pickers/AgeCategorySelect.vue'
import GenderSelect from '@/components/pickers/GenderSelect.vue'
import RegionSelect from '@/components/pickers/RegionSelect.vue'
import SportSelect from '@/components/pickers/SportSelect.vue'
import TopAthletes from '@/components/rating/TopAthletes.vue'
import { useAuthStore } from '@/stores/auth'
import { useCatalogStore } from '@/stores/catalog'
import type { Gender } from '@/types/catalog'

const router = useRouter()
const toast = useToast()
const auth = useAuthStore()
const catalog = useCatalogStore()

const PAGE_SIZE = 25

// Region ranking is oversight — ministry/super_admin see the country; a region_admin sees
// their own region (the backend scopes the rows). Coaches/operators don't get the tab.
const canSeeRegions = computed(
  () => !!auth.role && ['super_admin', 'ministry', 'region_admin'].includes(auth.role),
)

const filters = reactive({
  region: null as number | null,
  sport_type: null as number | null,
  age_category: null as number | null,
  gender: null as Gender | null,
})
const activeTab = ref('top')

const topRows = ref<RatingRow[]>([])
const topLoading = ref(false)

const fullRows = ref<RatingRow[]>([])
const fullTotal = ref(0)
const fullPage = ref(1)
const fullLoading = ref(false)

const regionRows = ref<RegionRatingRow[]>([])
const regionLoading = ref(false)

// A tab only refetches when its data is stale for the current filters.
const loaded = reactive({ top: false, full: false, regions: false })

function queryFor(): RatingQuery {
  return {
    region: filters.region,
    sport_type: filters.sport_type,
    age_category: filters.age_category,
    gender: filters.gender,
  }
}

async function fetchTop() {
  topLoading.value = true
  try {
    topRows.value = (await getTopAthletes({ ...queryFor(), limit: 10 })).results
    loaded.top = true
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Xatolik', detail: toMessage(e), life: 4000 })
  } finally {
    topLoading.value = false
  }
}

async function fetchFull() {
  fullLoading.value = true
  try {
    const data = await listRating({ ...queryFor(), page: fullPage.value })
    fullRows.value = data.results
    fullTotal.value = data.count
    loaded.full = true
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Xatolik', detail: toMessage(e), life: 4000 })
  } finally {
    fullLoading.value = false
  }
}

async function fetchRegions() {
  regionLoading.value = true
  try {
    regionRows.value = (await getRegionRating(queryFor())).results
    loaded.regions = true
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Xatolik', detail: toMessage(e), life: 4000 })
  } finally {
    regionLoading.value = false
  }
}

function loadActive() {
  if (activeTab.value === 'top' && !loaded.top) fetchTop()
  else if (activeTab.value === 'full' && !loaded.full) fetchFull()
  else if (activeTab.value === 'regions' && !loaded.regions) fetchRegions()
}

function onFilterChange() {
  loaded.top = loaded.full = loaded.regions = false
  fullPage.value = 1
  loadActive()
}

function onFullPage(event: DataTablePageEvent) {
  fullPage.value = event.page + 1
  fetchFull()
}

watch(activeTab, loadActive)

onMounted(() => {
  catalog.ensureLoaded()
  loadActive()
})
</script>

<template>
  <div>
    <PageHeader title="Reyting" subtitle="Eng kuchli sportchilar va viloyatlar reytingi" />

    <div class="rating__filters">
      <RegionSelect v-model="filters.region" @update:model-value="onFilterChange" />
      <SportSelect v-model="filters.sport_type" @update:model-value="onFilterChange" />
      <AgeCategorySelect v-model="filters.age_category" @update:model-value="onFilterChange" />
      <GenderSelect v-model="filters.gender" @update:model-value="onFilterChange" />
    </div>

    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="top"><i class="pi pi-star" /> Top sportchilar</Tab>
        <Tab value="full"><i class="pi pi-list" /> Toʻliq reyting</Tab>
        <Tab v-if="canSeeRegions" value="regions"><i class="pi pi-map" /> Viloyatlar</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="top">
          <TopAthletes :rows="topRows" :loading="topLoading" />
        </TabPanel>

        <TabPanel value="full">
          <DataTable
            :value="fullRows"
            :loading="fullLoading"
            lazy
            paginator
            :rows="PAGE_SIZE"
            :total-records="fullTotal"
            :first="(fullPage - 1) * PAGE_SIZE"
            data-key="athlete.id"
            row-hover
            class="rating__table"
            @page="onFullPage"
            @row-click="router.push(`/athletes/${$event.data.athlete.id}`)"
          >
            <template #empty>Baholangan sportchi topilmadi.</template>
            <Column header="Oʻrin" class="rating__rank">
              <template #body="{ data }">{{ data.rank }}</template>
            </Column>
            <Column header="F.I.O">
              <template #body="{ data }">
                <span class="rating__name">{{ data.athlete.full_name }}</span>
              </template>
            </Column>
            <Column header="Ball">
              <template #body="{ data }">{{ data.ranking_score }}</template>
            </Column>
            <Column header="Daraja">
              <template #body="{ data }"><DarajaBadge :level="data.daraja" /></template>
            </Column>
          </DataTable>
        </TabPanel>

        <TabPanel v-if="canSeeRegions" value="regions">
          <DataTable
            :value="regionRows"
            :loading="regionLoading"
            data-key="region"
            class="rating__table"
          >
            <template #empty>Maʼlumot yoʻq.</template>
            <Column field="rank" header="Oʻrin" class="rating__rank" />
            <Column field="region" header="Viloyat" />
            <Column header="I daraja">
              <template #body="{ data }">{{ data.daraja_i_count }}</template>
            </Column>
            <Column header="Oʻrtacha ball">
              <template #body="{ data }">{{ data.avg_score ?? '—' }}</template>
            </Column>
          </DataTable>
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<style scoped>
.rating__filters {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}
.rating__filters > * {
  min-width: 180px;
  flex: 1 1 180px;
}
.rating__table {
  margin-top: 0.5rem;
}
.rating__table :deep(tbody tr) {
  cursor: pointer;
}
.rating__rank {
  width: 5rem;
}
.rating__name {
  font-weight: 500;
  color: var(--p-primary-color);
}
</style>
