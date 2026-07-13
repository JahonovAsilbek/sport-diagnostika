<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import TabPanel from 'primevue/tabpanel'
import TabPanels from 'primevue/tabpanels'
import Tabs from 'primevue/tabs'
import Tag from 'primevue/tag'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { getBatteries } from '@/api/catalog'
import PageHeader from '@/components/PageHeader.vue'
import { directionLabel, genderLabel, valueTypeLabel } from '@/i18n/labels'
import { useAuthStore } from '@/stores/auth'
import { useCatalogStore } from '@/stores/catalog'
import type { Direction, Gender, TestBattery, ValueType } from '@/types/catalog'

const catalog = useCatalogStore()
const auth = useAuthStore()
const router = useRouter()

const batteries = ref<TestBattery[]>([])

onMounted(async () => {
  await catalog.ensureLoaded()
  batteries.value = await getBatteries()
})

function ageName(id: number) {
  return catalog.ageCategories.find((c) => c.id === id)?.name ?? String(id)
}
</script>

<template>
  <div>
    <PageHeader :title="$t('nav.catalog')" :subtitle="$t('catalog.subtitle')">
      <template #actions>
        <Button
          v-if="auth.role === 'super_admin'"
          :label="$t('catalog.manageNorms')"
          icon="pi pi-sliders-h"
          @click="router.push('/catalog/norms')"
        />
      </template>
    </PageHeader>

    <Tabs value="regions">
      <TabList>
        <Tab value="regions">{{ $t('catalog.tabs.regions') }}</Tab>
        <Tab value="sports">{{ $t('catalog.tabs.sports') }}</Tab>
        <Tab value="ages">{{ $t('catalog.tabs.ages') }}</Tab>
        <Tab value="exercises">{{ $t('catalog.tabs.exercises') }}</Tab>
        <Tab value="batteries">{{ $t('catalog.tabs.batteries') }}</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="regions">
          <DataTable :value="catalog.regions" paginator :rows="10" data-key="id">
            <Column field="name" :header="$t('common.fields.name')" sortable />
            <Column field="code" :header="$t('catalog.columns.code')" />
          </DataTable>
        </TabPanel>

        <TabPanel value="sports">
          <DataTable :value="catalog.sportTypes" paginator :rows="10" data-key="id">
            <Column field="name" :header="$t('common.fields.name')" sortable />
            <Column field="code" :header="$t('catalog.columns.code')" />
          </DataTable>
        </TabPanel>

        <TabPanel value="ages">
          <DataTable :value="catalog.ageCategories" data-key="id">
            <Column field="ordinal" header="#" sortable />
            <Column field="name" :header="$t('catalog.columns.category')" />
            <Column :header="$t('catalog.columns.ageRange')">
              <template #body="{ data }">{{ data.age_min }}–{{ data.age_max }}</template>
            </Column>
          </DataTable>
        </TabPanel>

        <TabPanel value="exercises">
          <DataTable :value="catalog.exercises" paginator :rows="10" data-key="id">
            <Column field="name" :header="$t('catalog.columns.exercise')" sortable />
            <Column field="unit" :header="$t('catalog.columns.unit')" />
            <Column :header="$t('catalog.columns.type')">
              <template #body="{ data }">
                {{ valueTypeLabel(data.value_type as ValueType) }}
              </template>
            </Column>
            <Column :header="$t('catalog.columns.direction')">
              <template #body="{ data }">
                {{ directionLabel(data.direction as Direction) }}
              </template>
            </Column>
            <Column :header="$t('common.fields.status')">
              <template #body="{ data }">
                <Tag
                  :value="data.is_active ? $t('catalog.active') : $t('catalog.inactive')"
                  :severity="data.is_active ? 'success' : 'secondary'"
                />
              </template>
            </Column>
          </DataTable>
        </TabPanel>

        <TabPanel value="batteries">
          <DataTable :value="batteries" paginator :rows="10" data-key="id">
            <Column :header="$t('common.fields.ageCategory')">
              <template #body="{ data }">{{ ageName(data.age_category) }}</template>
            </Column>
            <Column :header="$t('common.fields.gender')">
              <template #body="{ data }">{{ genderLabel(data.gender as Gender) }}</template>
            </Column>
            <Column :header="$t('catalog.columns.exercises')">
              <template #body="{ data }">
                {{ data.items.map((i: TestBattery['items'][number]) => i.exercise.name).join(', ') }}
              </template>
            </Column>
          </DataTable>
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>
