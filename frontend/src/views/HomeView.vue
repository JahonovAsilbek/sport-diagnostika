<script setup lang="ts">
import Button from 'primevue/button'
import Message from 'primevue/message'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { toMessage } from '@/api/client'
import { getOverview, type StatsOverview } from '@/api/stats'
import DarajaDonut from '@/components/dashboard/DarajaDonut.vue'
import RegionBars from '@/components/dashboard/RegionBars.vue'
import StatCard from '@/components/dashboard/StatCard.vue'
import PageHeader from '@/components/PageHeader.vue'
import { darajaLabel } from '@/i18n/labels'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const { t } = useI18n({ useScope: 'global' })

// Per-role framing of the same scoped numbers (ministry → national, coach → own athletes).
const subtitle = computed(() => (auth.role ? t(`home.scope.${auth.role}`) : ''))

// The national by-region chart is oversight — same gate as the rating regions tab.
const canSeeRegions = computed(
  () => !!auth.role && ['super_admin', 'ministry'].includes(auth.role),
)

const quickLinks = computed(() => [
  { label: t('nav.athletes'), icon: 'pi pi-users', to: '/athletes' },
  { label: t('nav.measurements'), icon: 'pi pi-pencil', to: '/measurements' },
  { label: t('nav.rating'), icon: 'pi pi-chart-bar', to: '/rating' },
  { label: t('nav.reports'), icon: 'pi pi-file', to: '/reports' },
])

const stats = ref<StatsOverview | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    stats.value = await getOverview()
  } catch (e) {
    error.value = toMessage(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader
      :title="$t('home.welcome', { name: auth.user?.full_name || auth.user?.username })"
      :subtitle="subtitle"
    />

    <div v-if="loading" class="dash__loading"><i class="pi pi-spin pi-spinner" /></div>

    <Message v-else-if="error" severity="error">
      <div class="dash__error">
        <span>{{ error }}</span>
        <Button :label="$t('common.retry')" icon="pi pi-refresh" size="small" text @click="load" />
      </div>
    </Message>

    <template v-else-if="stats">
      <div class="dash__kpis">
        <StatCard :label="$t('home.kpi.activeAthletes')" :value="stats.athletes_total" icon="pi pi-users" />
        <StatCard
          :label="darajaLabel('I')"
          :value="stats.by_daraja.I"
          icon="pi pi-star-fill"
          accent="#10b981"
        />
        <StatCard
          :label="$t('home.kpi.recentSessions')"
          :value="stats.recent_sessions"
          icon="pi pi-calendar"
        />
        <StatCard :label="$t('home.kpi.regions')" :value="stats.regions" icon="pi pi-map" />
      </div>

      <p class="dash__orgs">
        {{ $t('home.orgBreakdown') }} — OTM: <b>{{ stats.by_organization_type.OTM }}</b> · OPSTTM:
        <b>{{ stats.by_organization_type.OPSTTM }}</b>
      </p>

      <div class="dash__charts">
        <section class="dash__panel">
          <h3 class="dash__h">{{ $t('home.charts.darajaDistribution') }}</h3>
          <DarajaDonut :by-daraja="stats.by_daraja" />
        </section>
        <section v-if="canSeeRegions" class="dash__panel">
          <h3 class="dash__h">{{ $t('home.charts.byRegion') }}</h3>
          <RegionBars />
        </section>
      </div>

      <h3 class="dash__h">{{ $t('home.quickLinksTitle') }}</h3>
      <div class="dash__links">
        <button
          v-for="link in quickLinks"
          :key="link.to"
          class="dash__link"
          @click="router.push(link.to)"
        >
          <i :class="link.icon" />
          <span>{{ link.label }}</span>
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dash__loading {
  text-align: center;
  padding: 3rem;
  font-size: 1.5rem;
  color: var(--p-text-muted-color);
}
.dash__error {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}
.dash__kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 0.75rem;
}
.dash__orgs {
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
  margin: 0 0 1.75rem;
}
.dash__charts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}
.dash__panel {
  padding: 1.25rem;
  border: 1px solid var(--p-content-border-color, #e2e8f0);
  border-radius: 14px;
}
.dash__h {
  margin: 0 0 1rem;
  font-size: 1.05rem;
}
.dash__links {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.85rem;
}
.dash__link {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1.25rem 1rem;
  border: 1px solid var(--p-content-border-color, #e2e8f0);
  border-radius: 12px;
  background: var(--p-content-background, #fff);
  cursor: pointer;
  color: var(--p-text-color);
  font-size: 0.95rem;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.dash__link:hover {
  border-color: var(--p-primary-color);
  box-shadow: 0 0 0 1px var(--p-primary-color);
}
.dash__link i {
  font-size: 1.4rem;
  color: var(--p-primary-color);
}
</style>
