<script setup lang="ts">
import Message from 'primevue/message'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import TabPanel from 'primevue/tabpanel'
import TabPanels from 'primevue/tabpanels'
import Tabs from 'primevue/tabs'
import { computed, ref } from 'vue'

import AthleteAutocomplete from '@/components/pickers/AthleteAutocomplete.vue'
import PageHeader from '@/components/PageHeader.vue'
import RecommendationsPanel from '@/components/RecommendationsPanel.vue'
import RulesManager from '@/components/recommendations/RulesManager.vue'
import { useAuthStore } from '@/stores/auth'
import type { Athlete } from '@/types/athlete'

const auth = useAuthStore()

// Rules are internal config — super_admin only (coaches consume the generated text).
const canManageRules = computed(() => auth.role === 'super_admin')

const picked = ref<Athlete | null>(null)
const activeTab = ref('athlete')
</script>

<template>
  <div>
    <PageHeader :title="$t('nav.recommendations')" :subtitle="$t('recommendations.view.subtitle')" />

    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="athlete"><i class="pi pi-user" /> {{ $t('recommendations.view.athleteTab') }}</Tab>
        <Tab v-if="canManageRules" value="rules"><i class="pi pi-sliders-h" /> {{ $t('recommendations.view.rulesTab') }}</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="athlete">
          <AthleteAutocomplete v-model="picked" class="recs__pick" />
          <RecommendationsPanel v-if="picked" :key="picked.id" :athlete-id="picked.id" />
          <Message v-else severity="info" variant="simple">
            {{ $t('recommendations.view.pickPrompt') }}
          </Message>
        </TabPanel>
        <TabPanel v-if="canManageRules" value="rules">
          <RulesManager />
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<style scoped>
/* Don't set `display` here — it would override the AutoComplete's internal flex layout and detach
   the input from its dropdown button. `fluid` already makes it full-width (capped by max-width). */
.recs__pick {
  max-width: 420px;
  margin-bottom: 1.25rem;
}
</style>
