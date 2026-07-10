<script setup lang="ts">
import Message from 'primevue/message'
import { useRouter } from 'vue-router'

import type { RatingRow } from '@/api/rating'
import DarajaBadge from '@/components/DarajaBadge.vue'

// The headline "Top Athletes" list (TZ). Presentational — the parent owns fetching + filters.
defineProps<{ rows: RatingRow[]; loading: boolean }>()

const router = useRouter()

// Gold / silver / bronze for the podium; the rest just show their rank number.
const MEDAL: Record<number, string> = { 1: 'medal-gold', 2: 'medal-silver', 3: 'medal-bronze' }
</script>

<template>
  <div v-if="loading" class="top__loading"><i class="pi pi-spin pi-spinner" /></div>
  <Message v-else-if="!rows.length" severity="info" variant="simple">
    Ushbu filtr uchun baholangan sportchi topilmadi.
  </Message>
  <ol v-else class="top">
    <li
      v-for="row in rows"
      :key="row.athlete.id"
      class="top__row"
      @click="router.push(`/athletes/${row.athlete.id}`)"
    >
      <span class="top__rank" :class="MEDAL[row.rank]">
        <i v-if="MEDAL[row.rank]" class="pi pi-star-fill" />
        <template v-else>{{ row.rank }}</template>
      </span>
      <span class="top__name">{{ row.athlete.full_name }}</span>
      <DarajaBadge :level="row.daraja" />
      <span class="top__score">{{ row.ranking_score }}</span>
    </li>
  </ol>
</template>

<style scoped>
.top__loading {
  padding: 2rem;
  text-align: center;
  font-size: 1.5rem;
  color: var(--p-text-muted-color);
}
.top {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 620px;
}
.top__row {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0.7rem 1rem;
  background: var(--p-content-hover-background, #f8fafc);
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
}
.top__row:hover {
  background: var(--p-highlight-background, #eef2ff);
}
.top__rank {
  flex: 0 0 2rem;
  height: 2rem;
  display: grid;
  place-items: center;
  border-radius: 50%;
  font-weight: 700;
  background: var(--p-surface-200, #e2e8f0);
  color: var(--p-text-color);
}
.top__rank.medal-gold {
  background: #fde047;
  color: #713f12;
}
.top__rank.medal-silver {
  background: #e2e8f0;
  color: #475569;
}
.top__rank.medal-bronze {
  background: #fdba74;
  color: #7c2d12;
}
.top__name {
  flex: 1 1 auto;
  font-weight: 500;
}
.top__score {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--p-primary-color);
  min-width: 2.5rem;
  text-align: right;
}
</style>
