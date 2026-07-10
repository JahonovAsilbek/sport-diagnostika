<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'

import { toMessage } from '@/api/client'
import {
  finalizeSession,
  getBattery,
  getSession,
  saveMeasurements,
  updateSession,
} from '@/api/measurements'
import DarajaBadge from '@/components/DarajaBadge.vue'
import PageHeader from '@/components/PageHeader.vue'
import type { DarajaLevel } from '@/constants/labels'
import { useCatalogStore } from '@/stores/catalog'
import type { Exercise, TestBattery } from '@/types/catalog'
import type { Evaluation, TestSession } from '@/types/measurement'
import { rawPlaceholder, validateRaw } from '@/utils/rawValue'

const route = useRoute()
const toast = useToast()
const catalog = useCatalogStore()

const id = Number(route.params.id)
const session = ref<TestSession | null>(null)
const battery = ref<TestBattery | null>(null)
const batteryError = ref<string | null>(null)
const evaluation = ref<Evaluation | null>(null)
const loading = ref(true)
const saving = ref(false)
const finalizing = ref(false)

const values = reactive<Record<number, string>>({})
const height = ref<number | null>(null)
const weight = ref<number | null>(null)

const isDraft = computed(() => session.value?.status === 'draft')
const exercises = computed<Exercise[]>(() =>
  battery.value ? battery.value.items.map((i) => i.exercise) : [],
)

function exerciseName(exId: number): string {
  return (
    exercises.value.find((e) => e.id === exId)?.name ??
    catalog.exercises.find((e) => e.id === exId)?.name ??
    `#${exId}`
  )
}

onMounted(async () => {
  await catalog.ensureLoaded()
  try {
    const s = await getSession(id)
    session.value = s
    height.value = s.height_cm ? Number(s.height_cm) : null
    weight.value = s.weight_kg ? Number(s.weight_kg) : null
    for (const m of s.measurements) values[m.exercise] = m.raw_value
    try {
      battery.value = await getBattery(id)
    } catch (e) {
      batteryError.value = toMessage(e)
    }
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Xatolik', detail: toMessage(e), life: 4000 })
  } finally {
    loading.value = false
  }
})

function collectMeasurements(): { exercise: number; raw_value: string }[] {
  return exercises.value
    .filter((ex) => (values[ex.id] ?? '').trim() !== '')
    .map((ex) => ({ exercise: ex.id, raw_value: values[ex.id].trim() }))
}

function formatErrors(): string | null {
  for (const ex of exercises.value) {
    const err = validateRaw(ex.value_type, values[ex.id] ?? '')
    if (err) return `${ex.name}: ${err}`
  }
  return null
}

async function persist(): Promise<boolean> {
  const fmtErr = formatErrors()
  if (fmtErr) {
    toast.add({ severity: 'warn', summary: 'Format xatosi', detail: fmtErr, life: 4000 })
    return false
  }
  await saveMeasurements(id, collectMeasurements())
  await updateSession(id, {
    height_cm: height.value !== null ? String(height.value) : null,
    weight_kg: weight.value !== null ? String(weight.value) : null,
  })
  return true
}

async function saveDraft() {
  saving.value = true
  try {
    if (await persist()) toast.add({ severity: 'success', summary: 'Qoralama saqlandi', life: 2500 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Xatolik', detail: toMessage(e), life: 4000 })
  } finally {
    saving.value = false
  }
}

async function finalize() {
  finalizing.value = true
  try {
    if (!(await persist())) return
    evaluation.value = await finalizeSession(id)
    if (session.value) session.value.status = 'finalized'
    toast.add({ severity: 'success', summary: 'Yakunlandi', life: 2500 })
  } catch (e) {
    // The backend 400 names the missing battery exercises.
    toast.add({ severity: 'error', summary: 'Yakunlab boʻlmadi', detail: toMessage(e), life: 6000 })
  } finally {
    finalizing.value = false
  }
}
</script>

<template>
  <div v-if="session">
    <PageHeader :title="`Test sessiyasi #${session.id}`" :subtitle="session.date">
      <template #actions>
        <Tag
          :value="isDraft ? 'Qoralama' : 'Yakunlangan'"
          :severity="isDraft ? 'warn' : 'success'"
        />
      </template>
    </PageHeader>

    <Message v-if="batteryError" severity="warn">
      {{ batteryError }} — administrator bu guruh uchun batareyani sozlashi kerak.
    </Message>

    <!-- Result (shown right after finalize) -->
    <div v-if="evaluation" class="result">
      <div class="result__score">
        <span class="result__total">{{ evaluation.physical_total }}</span>
        <span class="result__max">/ 50</span>
        <DarajaBadge :level="(evaluation.daraja as DarajaLevel | null)" />
      </div>
      <DataTable :value="evaluation.indicators" data-key="exercise" class="result__table">
        <Column header="Mashq">
          <template #body="{ data }">{{ exerciseName(data.exercise) }}</template>
        </Column>
        <Column field="raw_value" header="Natija" />
        <Column field="points" header="Ball" />
      </DataTable>
    </div>

    <!-- Draft entry form -->
    <template v-else-if="isDraft && battery">
      <div class="entry">
        <div v-for="ex in exercises" :key="ex.id" class="entry__row">
          <label class="entry__label">{{ ex.name }} <small>({{ ex.unit }})</small></label>
          <InputText v-model="values[ex.id]" :placeholder="rawPlaceholder(ex.value_type)" fluid />
        </div>
        <div class="entry__row">
          <label class="entry__label">Boʻy (sm)</label>
          <InputNumber v-model="height" :min="0" :max="260" fluid />
        </div>
        <div class="entry__row">
          <label class="entry__label">Vazn (kg)</label>
          <InputNumber v-model="weight" :min="0" :max="300" :max-fraction-digits="1" fluid />
        </div>
      </div>
      <div class="entry__actions">
        <Button
          label="Qoralamani saqlash"
          icon="pi pi-save"
          severity="secondary"
          :loading="saving"
          @click="saveDraft"
        />
        <Button label="Yakunlash" icon="pi pi-check-circle" :loading="finalizing" @click="finalize" />
      </div>
    </template>

    <!-- Finalized (reloaded — the evaluation lives in the Results section, F6) -->
    <template v-else-if="!isDraft">
      <Message severity="success" variant="simple">
        Sessiya yakunlangan. Natijani Natijalar boʻlimida koʻrishingiz mumkin (F6).
      </Message>
      <DataTable :value="session.measurements" data-key="exercise" class="result__table">
        <Column header="Mashq">
          <template #body="{ data }">{{ exerciseName(data.exercise) }}</template>
        </Column>
        <Column field="raw_value" header="Natija" />
      </DataTable>
    </template>
  </div>

  <div v-else-if="loading" class="loading"><i class="pi pi-spin pi-spinner" /></div>
</template>

<style scoped>
.result {
  margin-bottom: 1.5rem;
}
.result__score {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.result__total {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--p-primary-color);
}
.result__max {
  color: var(--p-text-muted-color);
  margin-right: 0.75rem;
}
.result__table {
  max-width: 560px;
}
.entry {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  max-width: 480px;
  margin-bottom: 1.5rem;
}
.entry__row {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.entry__label {
  font-size: 0.9rem;
  font-weight: 500;
}
.entry__actions {
  display: flex;
  gap: 0.5rem;
}
.loading {
  text-align: center;
  padding: 3rem;
  font-size: 1.5rem;
  color: var(--p-text-muted-color);
}
</style>
