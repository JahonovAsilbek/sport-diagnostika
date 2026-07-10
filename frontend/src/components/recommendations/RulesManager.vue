<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, reactive, ref } from 'vue'

import { toMessage } from '@/api/client'
import {
  COMPARATOR_LABELS,
  createRule,
  deleteRule,
  listRules,
  updateRule,
  type Comparator,
  type RecommendationRule,
  type RecommendationRuleWrite,
} from '@/api/recommendations'
import { useCatalogStore } from '@/stores/catalog'

// Admin-managed recommendation rules (super_admin). A rule fires when an evaluation's metric
// satisfies `comparator threshold` — exercise set → the exercise's points (0–10), null →
// physical_total (0–50). Thresholds are DATA (SCORING.md §8), never hardcoded.
const toast = useToast()
const confirm = useConfirm()
const catalog = useCatalogStore()

const rules = ref<RecommendationRule[]>([])
const loading = ref(false)

const dialogOpen = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = reactive<RecommendationRuleWrite>({
  exercise: null,
  comparator: 'lte',
  threshold: 0,
  template_text: '',
  is_active: true,
})

const targetOptions = computed(() => [
  { label: 'Umumiy ball (0–50)', value: null as number | null },
  ...catalog.exercises.map((e) => ({ label: e.name, value: e.id as number | null })),
])
const comparatorOptions = (Object.keys(COMPARATOR_LABELS) as Comparator[]).map((c) => ({
  label: `${COMPARATOR_LABELS[c]}  (${c})`,
  value: c,
}))
// Exercise points top out at 10; physical_total at 50 (mirrors the backend validation).
const thresholdMax = computed(() => (form.exercise === null ? 50 : 10))

function targetName(exerciseId: number | null): string {
  if (exerciseId === null) return 'Umumiy ball'
  return catalog.exercises.find((e) => e.id === exerciseId)?.name ?? `#${exerciseId}`
}

async function load() {
  loading.value = true
  try {
    rules.value = (await listRules()).results
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Xatolik', detail: toMessage(e), life: 4000 })
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    exercise: null,
    comparator: 'lte',
    threshold: 0,
    template_text: '',
    is_active: true,
  })
  dialogOpen.value = true
}

function openEdit(rule: RecommendationRule) {
  editingId.value = rule.id
  Object.assign(form, {
    exercise: rule.exercise,
    comparator: rule.comparator,
    threshold: rule.threshold,
    template_text: rule.template_text,
    is_active: rule.is_active,
  })
  dialogOpen.value = true
}

async function save() {
  if (!form.template_text.trim()) {
    toast.add({ severity: 'warn', summary: 'Matn kiriting', detail: 'Tavsiya matni boʻsh.', life: 3500 })
    return
  }
  saving.value = true
  try {
    const payload = { ...form }
    if (editingId.value === null) await createRule(payload)
    else await updateRule(editingId.value, payload)
    toast.add({ severity: 'success', summary: 'Saqlandi', life: 2500 })
    dialogOpen.value = false
    await load()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Xatolik', detail: toMessage(e), life: 5000 })
  } finally {
    saving.value = false
  }
}

function remove(rule: RecommendationRule) {
  confirm.require({
    message: `"${targetName(rule.exercise)}" qoidasi oʻchirilsinmi?`,
    header: 'Tasdiqlang',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Oʻchirish',
    rejectLabel: 'Bekor',
    acceptProps: { severity: 'danger' },
    accept: async () => {
      try {
        await deleteRule(rule.id)
        toast.add({ severity: 'success', summary: 'Oʻchirildi', life: 2500 })
        await load()
      } catch (e) {
        toast.add({ severity: 'error', summary: 'Xatolik', detail: toMessage(e), life: 4000 })
      }
    },
  })
}

onMounted(() => {
  catalog.ensureLoaded()
  load()
})
</script>

<template>
  <div>
    <div class="rules__bar">
      <p class="rules__hint">
        Qoidalar baholashdan keyin tavsiyalarni avtomatik yaratadi (chegaralar — DATA).
      </p>
      <Button label="Yangi qoida" icon="pi pi-plus" @click="openCreate" />
    </div>

    <DataTable :value="rules" :loading="loading" data-key="id" class="rules__table">
      <template #empty>Qoidalar yoʻq.</template>
      <Column header="Nishon">
        <template #body="{ data }">{{ targetName(data.exercise) }}</template>
      </Column>
      <Column header="Shart">
        <template #body="{ data }">{{ COMPARATOR_LABELS[data.comparator as Comparator] }} {{ data.threshold }}</template>
      </Column>
      <Column header="Tavsiya matni">
        <template #body="{ data }"><span class="rules__text">{{ data.template_text }}</span></template>
      </Column>
      <Column header="Holat">
        <template #body="{ data }">
          <Tag
            :value="data.is_active ? 'Faol' : 'Nofaol'"
            :severity="data.is_active ? 'success' : 'secondary'"
          />
        </template>
      </Column>
      <Column header="" class="rules__actions">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" text rounded @click="openEdit(data)" />
          <Button icon="pi pi-trash" text rounded severity="danger" @click="remove(data)" />
        </template>
      </Column>
    </DataTable>

    <Dialog
      v-model:visible="dialogOpen"
      :header="editingId === null ? 'Yangi qoida' : 'Qoidani tahrirlash'"
      modal
      :style="{ width: '30rem' }"
    >
      <div class="rules__form">
        <label>Nishon</label>
        <Select v-model="form.exercise" :options="targetOptions" option-label="label" option-value="value" fluid />

        <label>Shart</label>
        <Select v-model="form.comparator" :options="comparatorOptions" option-label="label" option-value="value" fluid />

        <label>Chegara (0–{{ thresholdMax }})</label>
        <InputNumber v-model="form.threshold" :min="0" :max="thresholdMax" fluid />

        <label>Tavsiya matni</label>
        <Textarea v-model="form.template_text" rows="3" auto-resize fluid />

        <div class="rules__toggle">
          <ToggleSwitch v-model="form.is_active" input-id="rule-active" />
          <label for="rule-active">Faol</label>
        </div>
      </div>
      <template #footer>
        <Button label="Bekor" text @click="dialogOpen = false" />
        <Button label="Saqlash" icon="pi pi-check" :loading="saving" @click="save" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.rules__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}
.rules__hint {
  margin: 0;
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
}
.rules__text {
  color: var(--p-text-muted-color);
}
.rules__actions {
  width: 6rem;
  text-align: right;
}
.rules__form {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.rules__form label {
  font-size: 0.85rem;
  font-weight: 500;
  margin-top: 0.5rem;
}
.rules__toggle {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-top: 0.75rem;
}
.rules__toggle label {
  margin-top: 0;
}
</style>
