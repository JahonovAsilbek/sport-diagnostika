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
import { useToast } from 'primevue/usetoast'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { getAthlete } from '@/api/athletes'
import { getOrganizations } from '@/api/catalog'
import { toMessage } from '@/api/client'
import { listSessions } from '@/api/measurements'
import { getCoaches } from '@/api/users'
import EvaluationPanel from '@/components/EvaluationPanel.vue'
import PageHeader from '@/components/PageHeader.vue'
import RecommendationsPanel from '@/components/RecommendationsPanel.vue'
import { genderLabel } from '@/i18n/labels'
import { useAuthStore } from '@/stores/auth'
import { useCatalogStore } from '@/stores/catalog'
import type { Athlete } from '@/types/athlete'
import type { TestSession } from '@/types/measurement'
import { canWrite } from '@/utils/permissions'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const { t } = useI18n({ useScope: 'global' })
const auth = useAuthStore()
const catalog = useCatalogStore()

const id = Number(route.params.id)
const athlete = ref<Athlete | null>(null)
const loading = ref(true)
const districtName = ref('—')
const orgName = ref('—')
const coachName = ref('—')
const sessions = ref<TestSession[]>([])

const regionName = (rid: number | null) =>
  rid ? (catalog.regions.find((r) => r.id === rid)?.name ?? '—') : '—'
const sportName = (sid: number | null) =>
  sid ? (catalog.sportTypes.find((s) => s.id === sid)?.name ?? '—') : '—'

onMounted(async () => {
  await catalog.ensureLoaded()
  try {
    const a = await getAthlete(id)
    athlete.value = a
    // Resolve the names that aren't in the global cache (best-effort).
    if (a.region && a.district) {
      const districts = await catalog.districtsFor(a.region)
      districtName.value = districts.find((d) => d.id === a.district)?.name ?? '—'
    }
    if (a.organization) {
      const orgs = await getOrganizations(a.region ? { region: a.region } : undefined)
      orgName.value = orgs.find((o) => o.id === a.organization)?.name ?? '—'
    }
    if (a.coach) {
      const coaches = await getCoaches()
      const c = coaches.find((u) => u.id === a.coach)
      coachName.value = c ? c.full_name || c.username : '—'
    }
    sessions.value = (await listSessions({ athlete: id })).results
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: toMessage(e), life: 4000 })
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-if="athlete">
    <PageHeader :title="athlete.full_name" :subtitle="`${sportName(athlete.sport_type)} · ${athlete.birth_year}`">
      <template #actions>
        <Button
          :label="$t('nav.comparison')"
          icon="pi pi-arrow-right-arrow-left"
          severity="secondary"
          outlined
          @click="router.push(`/comparison?athletes=${athlete.id}`)"
        />
        <Button
          v-if="canWrite(auth.role)"
          :label="$t('common.edit')"
          icon="pi pi-pencil"
          @click="router.push(`/athletes/${athlete.id}/edit`)"
        />
      </template>
    </PageHeader>

    <div class="card-badges">
      <Tag v-if="athlete.age_category" :value="athlete.age_category.name" icon="pi pi-users" />
      <Tag v-if="athlete.block" :value="athlete.block" severity="info" />
      <Tag
        :value="athlete.is_active ? $t('athletes.active') : $t('athletes.inactive')"
        :severity="athlete.is_active ? 'success' : 'secondary'"
      />
    </div>

    <Tabs value="info">
      <TabList>
        <Tab value="info">{{ $t('athletes.card.tabs.info') }}</Tab>
        <Tab value="sessions">{{ $t('athletes.card.tabs.sessions') }}</Tab>
        <Tab value="evaluation">{{ $t('athletes.card.tabs.evaluation') }}</Tab>
        <Tab value="recs">{{ $t('nav.recommendations') }}</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="info">
          <dl class="info-grid">
            <div><dt>{{ $t('athletes.fullName') }}</dt><dd>{{ athlete.full_name }}</dd></div>
            <div><dt>{{ $t('common.fields.birthYear') }}</dt><dd>{{ athlete.birth_year }}</dd></div>
            <div><dt>{{ $t('common.fields.gender') }}</dt><dd>{{ genderLabel(athlete.gender) }}</dd></div>
            <div><dt>{{ $t('athletes.card.ageCategory') }}</dt><dd>{{ athlete.age_category?.name ?? '—' }}</dd></div>
            <div><dt>{{ $t('athletes.block') }}</dt><dd>{{ athlete.block ?? '—' }}</dd></div>
            <div><dt>{{ $t('common.fields.sport') }}</dt><dd>{{ sportName(athlete.sport_type) }}</dd></div>
            <div><dt>{{ $t('common.fields.region') }}</dt><dd>{{ regionName(athlete.region) }}</dd></div>
            <div><dt>{{ $t('common.fields.district') }}</dt><dd>{{ districtName }}</dd></div>
            <div><dt>{{ $t('common.fields.organization') }}</dt><dd>{{ orgName }}</dd></div>
            <div><dt>{{ $t('common.fields.coach') }}</dt><dd>{{ coachName }}</dd></div>
            <div><dt>{{ $t('athletes.razryad') }}</dt><dd>{{ athlete.razryad ?? '—' }}</dd></div>
            <div><dt>{{ $t('athletes.card.experience') }}</dt><dd>{{ athlete.training_experience ?? '—' }}</dd></div>
            <div class="info-grid__wide">
              <dt>{{ $t('athletes.mainCompetitions') }}</dt>
              <dd>{{ athlete.main_competitions ?? '—' }}</dd>
            </div>
          </dl>
        </TabPanel>
        <TabPanel value="sessions">
          <DataTable
            :value="sessions"
            data-key="id"
            paginator
            :rows="8"
            row-hover
            @row-click="router.push(`/measurements/session/${$event.data.id}`)"
          >
            <template #empty>{{ $t('athletes.card.sessionsEmpty') }}</template>
            <Column field="date" :header="$t('common.fields.date')" sortable />
            <Column :header="$t('common.fields.status')">
              <template #body="{ data }">
                <Tag
                  :value="
                    data.status === 'draft'
                      ? $t('athletes.card.session.draft')
                      : $t('athletes.card.session.finalized')
                  "
                  :severity="data.status === 'draft' ? 'warn' : 'success'"
                />
              </template>
            </Column>
          </DataTable>
        </TabPanel>
        <TabPanel value="evaluation">
          <EvaluationPanel :athlete-id="athlete.id" />
        </TabPanel>
        <TabPanel value="recs">
          <RecommendationsPanel :athlete-id="athlete.id" />
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>

  <div v-else-if="loading" class="card-loading">
    <i class="pi pi-spin pi-spinner" style="font-size: 1.5rem" />
  </div>
</template>

<style scoped>
.card-badges {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
}
.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem 2rem;
  margin: 0;
}
.info-grid__wide {
  grid-column: 1 / -1;
}
.info-grid dt {
  font-size: 0.8rem;
  color: var(--p-text-muted-color);
}
.info-grid dd {
  margin: 0.15rem 0 0;
  font-weight: 500;
}
.card-loading {
  text-align: center;
  padding: 3rem;
  color: var(--p-text-muted-color);
}
@media (max-width: 640px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
