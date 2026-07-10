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
import { DIRECTION_LABELS, GENDER_LABELS, VALUE_TYPE_LABELS } from '@/constants/labels'
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
    <PageHeader title="Katalog" subtitle="Maʼlumotnoma — viloyatlar, sport turlari, mashqlar">
      <template #actions>
        <Button
          v-if="auth.role === 'super_admin'"
          label="Normalarni boshqarish"
          icon="pi pi-sliders-h"
          @click="router.push('/catalog/norms')"
        />
      </template>
    </PageHeader>

    <Tabs value="regions">
      <TabList>
        <Tab value="regions">Viloyatlar</Tab>
        <Tab value="sports">Sport turlari</Tab>
        <Tab value="ages">Yosh toifalari</Tab>
        <Tab value="exercises">Mashqlar</Tab>
        <Tab value="batteries">Batareyalar</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="regions">
          <DataTable :value="catalog.regions" paginator :rows="10" data-key="id">
            <Column field="name" header="Nomi" sortable />
            <Column field="code" header="Kodi" />
          </DataTable>
        </TabPanel>

        <TabPanel value="sports">
          <DataTable :value="catalog.sportTypes" paginator :rows="10" data-key="id">
            <Column field="name" header="Nomi" sortable />
            <Column field="code" header="Kodi" />
          </DataTable>
        </TabPanel>

        <TabPanel value="ages">
          <DataTable :value="catalog.ageCategories" data-key="id">
            <Column field="ordinal" header="#" sortable />
            <Column field="name" header="Toifa" />
            <Column header="Yosh oraligʻi">
              <template #body="{ data }">{{ data.age_min }}–{{ data.age_max }}</template>
            </Column>
          </DataTable>
        </TabPanel>

        <TabPanel value="exercises">
          <DataTable :value="catalog.exercises" paginator :rows="10" data-key="id">
            <Column field="name" header="Mashq" sortable />
            <Column field="unit" header="Birlik" />
            <Column header="Turi">
              <template #body="{ data }">
                {{ VALUE_TYPE_LABELS[data.value_type as ValueType] }}
              </template>
            </Column>
            <Column header="Yoʻnalish">
              <template #body="{ data }">
                {{ DIRECTION_LABELS[data.direction as Direction] }}
              </template>
            </Column>
            <Column header="Holat">
              <template #body="{ data }">
                <Tag
                  :value="data.is_active ? 'Faol' : 'Nofaol'"
                  :severity="data.is_active ? 'success' : 'secondary'"
                />
              </template>
            </Column>
          </DataTable>
        </TabPanel>

        <TabPanel value="batteries">
          <DataTable :value="batteries" paginator :rows="10" data-key="id">
            <Column header="Yosh toifasi">
              <template #body="{ data }">{{ ageName(data.age_category) }}</template>
            </Column>
            <Column header="Jins">
              <template #body="{ data }">{{ GENDER_LABELS[data.gender as Gender] }}</template>
            </Column>
            <Column header="Mashqlar">
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
