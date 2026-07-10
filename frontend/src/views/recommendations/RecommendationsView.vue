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
    <PageHeader title="Tavsiyalar" subtitle="Sportchi tavsiyalari va qoidalar" />

    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="athlete"><i class="pi pi-user" /> Sportchi tavsiyalari</Tab>
        <Tab v-if="canManageRules" value="rules"><i class="pi pi-sliders-h" /> Qoidalar</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="athlete">
          <AthleteAutocomplete v-model="picked" class="recs__pick" />
          <RecommendationsPanel v-if="picked" :key="picked.id" :athlete-id="picked.id" />
          <Message v-else severity="info" variant="simple">
            Tavsiyalarni koʻrish uchun sportchini tanlang.
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
.recs__pick {
  display: block;
  max-width: 420px;
  margin-bottom: 1.25rem;
}
</style>
