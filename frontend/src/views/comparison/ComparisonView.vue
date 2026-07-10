<script setup lang="ts">
import Button from 'primevue/button'
import Chip from 'primevue/chip'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getAthlete } from '@/api/athletes'
import { toMessage } from '@/api/client'
import {
  compareAthletes,
  type ComparisonAthlete,
  type ComparisonResult,
} from '@/api/comparison'
import AthleteAutocomplete from '@/components/pickers/AthleteAutocomplete.vue'
import DarajaBadge from '@/components/DarajaBadge.vue'
import PageHeader from '@/components/PageHeader.vue'
import type { Athlete } from '@/types/athlete'

const route = useRoute()
const router = useRouter()
const toast = useToast()

// A lightweight {id, full_name} is all a chip needs — decoupled from the full Athlete so we
// can hydrate the selection from a shareable URL / the comparison result too.
type Pick = { id: number; full_name: string }

const selected = ref<Pick[]>([])
const picker = ref<Athlete | null>(null)
const result = ref<ComparisonResult | null>(null)
const loading = ref(false)

// Picking from the autocomplete adds a chip (max 3, no dupes) and clears the input.
watch(picker, (a) => {
  if (!a) return
  if (selected.value.length < 3 && !selected.value.some((s) => s.id === a.id)) {
    selected.value.push({ id: a.id, full_name: a.full_name })
  }
  picker.value = null
})

function remove(id: number) {
  selected.value = selected.value.filter((s) => s.id !== id)
}

const athletes = computed<ComparisonAthlete[]>(() => result.value?.athletes ?? [])

function cell(a: ComparisonAthlete, name: string) {
  return a.indicators.find((i) => i.exercise === name)
}

// The ordered union of exercise names across the selected athletes (batteries may differ).
const exerciseNames = computed<string[]>(() => {
  const names: string[] = []
  for (const a of athletes.value)
    for (const ind of a.indicators) if (!names.includes(ind.exercise)) names.push(ind.exercise)
  return names
})

interface Cell {
  points: number | null
  raw: string | null
  win: boolean
}
interface Row {
  name: string
  cells: Cell[]
}

// Precomputed grid: one row per exercise, cells aligned to `athletes` order, winner flagged
// (highest points in the row; ties highlight all).
const matrix = computed<Row[]>(() =>
  exerciseNames.value.map((name) => {
    const inds = athletes.value.map((a) => cell(a, name))
    let max: number | null = null
    for (const ind of inds) if (ind && (max === null || ind.points > max)) max = ind.points
    return {
      name,
      cells: inds.map((ind) => ({
        points: ind ? ind.points : null,
        raw: ind ? ind.raw_value : null,
        win: !!ind && max !== null && ind.points === max,
      })),
    }
  }),
)

async function compare() {
  if (selected.value.length < 2) return
  loading.value = true
  try {
    const ids = selected.value.map((s) => s.id)
    result.value = await compareAthletes(ids)
    // Reflect the selection in the URL for shareable links.
    router.replace({ query: { athletes: ids.join(',') } })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Xatolik', detail: toMessage(e), life: 4000 })
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const raw = route.query.athletes
  if (typeof raw !== 'string' || !raw.trim()) return
  const ids = raw
    .split(',')
    .map((s) => Number(s.trim()))
    .filter((n) => Number.isInteger(n) && n > 0)
  if (ids.length >= 2 && ids.length <= 3) {
    // A full comparison link — run it and hydrate the chips from the result.
    loading.value = true
    try {
      result.value = await compareAthletes(ids)
      selected.value = result.value.athletes.map((a) => ({ id: a.id, full_name: a.full_name }))
    } catch (e) {
      toast.add({ severity: 'error', summary: 'Xatolik', detail: toMessage(e), life: 4000 })
    } finally {
      loading.value = false
    }
  } else if (ids.length === 1) {
    // Pre-seeded from an athlete card — just select them, wait for a second pick.
    try {
      const a = await getAthlete(ids[0])
      selected.value = [{ id: a.id, full_name: a.full_name }]
    } catch {
      /* out of scope / gone — leave the selection empty */
    }
  }
})
</script>

<template>
  <div>
    <PageHeader title="Taqqoslash" subtitle="2–3 sportchini yonma-yon solishtiring" />

    <div class="cmp__pick">
      <AthleteAutocomplete v-model="picker" :disabled="selected.length >= 3" class="cmp__auto" />
      <Button
        label="Taqqoslash"
        icon="pi pi-arrow-right-arrow-left"
        :disabled="selected.length < 2 || loading"
        :loading="loading"
        @click="compare"
      />
    </div>

    <div v-if="selected.length" class="cmp__chips">
      <Chip
        v-for="s in selected"
        :key="s.id"
        :label="s.full_name"
        removable
        @remove="remove(s.id)"
      />
    </div>
    <small v-else class="cmp__hint">Solishtirish uchun kamida 2 ta sportchi tanlang.</small>

    <div v-if="result" class="cmp__result">
      <div class="cmp__cards" :style="{ '--cols': athletes.length }">
        <div
          v-for="a in athletes"
          :key="a.id"
          class="cmp__card"
          :class="{ 'cmp__card--leader': a.id === result.leader }"
        >
          <div class="cmp__card-name">{{ a.full_name }}</div>
          <div class="cmp__card-total">
            <span>{{ a.physical_total ?? '—' }}</span><small>/ 50</small>
          </div>
          <DarajaBadge :level="a.daraja" />
          <Tag
            v-if="a.id === result.leader"
            value="Yetakchi"
            icon="pi pi-crown"
            severity="success"
            class="cmp__leader"
          />
        </div>
      </div>

      <table v-if="matrix.length" class="cmp__table">
        <thead>
          <tr>
            <th>Mashq</th>
            <th v-for="a in athletes" :key="a.id">{{ a.full_name }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in matrix" :key="row.name">
            <td class="cmp__ex">{{ row.name }}</td>
            <td v-for="(c, i) in row.cells" :key="i" :class="{ 'cmp__win': c.win }">
              <template v-if="c.points !== null">
                <b>{{ c.points }}</b> <small>({{ c.raw }})</small>
              </template>
              <template v-else>—</template>
            </td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td>Umumiy ball</td>
            <td
              v-for="a in athletes"
              :key="a.id"
              :class="{ 'cmp__win': a.id === result.leader }"
            >
              <b>{{ a.physical_total ?? '—' }}</b>
            </td>
          </tr>
        </tfoot>
      </table>
      <Message v-else severity="info" variant="simple">
        Tanlangan sportchilarda baholangan umumiy mashqlar yoʻq.
      </Message>

      <small class="cmp__note">
        Batareyalar yosh×jins boʻyicha farq qiladi — faqat umumiy mashqlar solishtiriladi.
      </small>
    </div>
  </div>
</template>

<style scoped>
.cmp__pick {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 0.75rem;
}
.cmp__auto {
  flex: 1 1 320px;
  max-width: 420px;
}
.cmp__chips {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 1.25rem;
}
.cmp__hint {
  display: block;
  color: var(--p-text-muted-color);
  margin-bottom: 1.25rem;
}
.cmp__cards {
  display: grid;
  grid-template-columns: repeat(var(--cols), minmax(0, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  max-width: 720px;
}
.cmp__card {
  position: relative;
  padding: 1rem;
  border: 1px solid var(--p-content-border-color, #e2e8f0);
  border-radius: 12px;
  text-align: center;
}
.cmp__card--leader {
  border-color: var(--p-primary-color);
  box-shadow: 0 0 0 1px var(--p-primary-color);
}
.cmp__card-name {
  font-weight: 600;
  margin-bottom: 0.5rem;
}
.cmp__card-total {
  font-size: 2rem;
  font-weight: 700;
  color: var(--p-primary-color);
  margin-bottom: 0.5rem;
}
.cmp__card-total small {
  font-size: 0.9rem;
  font-weight: 400;
  color: var(--p-text-muted-color);
  margin-left: 0.25rem;
}
.cmp__leader {
  position: absolute;
  top: -0.6rem;
  right: -0.4rem;
}
.cmp__table {
  border-collapse: collapse;
  width: 100%;
  max-width: 720px;
}
.cmp__table th,
.cmp__table td {
  padding: 0.6rem 0.85rem;
  text-align: center;
  border-bottom: 1px solid var(--p-content-border-color, #e2e8f0);
}
.cmp__table thead th {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
  font-weight: 600;
}
.cmp__table .cmp__ex {
  text-align: left;
  font-weight: 500;
}
.cmp__table td small {
  color: var(--p-text-muted-color);
}
.cmp__table tfoot td {
  border-top: 2px solid var(--p-content-border-color, #cbd5e1);
  border-bottom: none;
  font-size: 1.05rem;
}
.cmp__win {
  background: var(--p-green-50, #f0fdf4);
  color: var(--p-green-700, #15803d);
}
.cmp__note {
  display: block;
  margin-top: 0.75rem;
  color: var(--p-text-muted-color);
}
</style>
