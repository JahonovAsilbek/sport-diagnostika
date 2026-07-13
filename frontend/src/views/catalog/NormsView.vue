<script setup lang="ts">
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import DatePicker from 'primevue/datepicker'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { createNorm, deleteNorm, getDarajaThresholds, getNorms, updateNorm } from '@/api/catalog'
import { toMessage } from '@/api/client'
import ExerciseSelect from '@/components/pickers/ExerciseSelect.vue'
import GenderSelect from '@/components/pickers/GenderSelect.vue'
import PageHeader from '@/components/PageHeader.vue'
import { genderLabel } from '@/i18n/labels'
import type { DarajaThreshold, Gender, Norm, NormBand, NormWrite } from '@/types/catalog'
import { validateBands } from '@/utils/normBands'

const { t } = useI18n({ useScope: 'global' })
const toast = useToast()
const confirm = useConfirm()

const POINTS = [10, 8, 6]

const norms = ref<Norm[]>([])
const thresholds = ref<DarajaThreshold[]>([])
const loading = ref(false)
const filter = reactive({ exercise: null as number | null, gender: null as Gender | null })

async function load() {
  loading.value = true
  try {
    const res = await getNorms({
      exercise: filter.exercise ?? undefined,
      gender: filter.gender ?? undefined,
    })
    norms.value = res.results
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: toMessage(e), life: 4000 })
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await load()
  thresholds.value = await getDarajaThresholds()
})

// --- editor ---
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const formErrors = ref<string[]>([])

const form = reactive({
  exercise: null as number | null,
  gender: null as Gender | null,
  age_min: null as number | null,
  age_max: null as number | null,
  valid_from: new Date() as Date | null,
  is_active: true,
  bands: POINTS.map((points) => ({ points, lower_bound: null, upper_bound: null }) as NormBand),
})

function resetForm() {
  form.exercise = null
  form.gender = null
  form.age_min = null
  form.age_max = null
  form.valid_from = new Date()
  form.is_active = true
  form.bands = POINTS.map((points) => ({ points, lower_bound: null, upper_bound: null }))
  formErrors.value = []
}

function openCreate() {
  resetForm()
  editingId.value = null
  dialogVisible.value = true
}

function openEdit(norm: Norm) {
  editingId.value = norm.id
  form.exercise = norm.exercise.id
  form.gender = norm.gender
  form.age_min = norm.age_min
  form.age_max = norm.age_max
  form.valid_from = norm.valid_from ? new Date(norm.valid_from) : new Date()
  form.is_active = norm.is_active
  form.bands = POINTS.map((points) => {
    const existing = norm.bands.find((b) => b.points === points)
    return {
      points,
      lower_bound: existing?.lower_bound ?? null,
      upper_bound: existing?.upper_bound ?? null,
    }
  })
  formErrors.value = []
  dialogVisible.value = true
}

function isoDate(d: Date | null): string {
  const date = d ?? new Date()
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(
    date.getDate(),
  ).padStart(2, '0')}`
}

async function save() {
  const errors: string[] = []
  if (!form.exercise) errors.push(t('catalog.norms.validation.exercise'))
  if (!form.gender) errors.push(t('catalog.norms.validation.gender'))
  if (form.age_min === null || form.age_max === null)
    errors.push(t('catalog.norms.validation.ageRange'))
  errors.push(...validateBands(form.bands))
  formErrors.value = errors
  if (errors.length) return

  const payload: NormWrite = {
    exercise: form.exercise!,
    gender: form.gender!,
    age_min: form.age_min!,
    age_max: form.age_max!,
    valid_from: isoDate(form.valid_from),
    is_active: form.is_active,
    bands: form.bands,
  }
  saving.value = true
  try {
    if (editingId.value) await updateNorm(editingId.value, payload)
    else await createNorm(payload)
    toast.add({ severity: 'success', summary: t('catalog.norms.saved'), life: 2500 })
    dialogVisible.value = false
    await load()
  } catch (e) {
    toast.add({
      severity: 'error',
      summary: t('catalog.norms.saveError'),
      detail: toMessage(e),
      life: 4000,
    })
  } finally {
    saving.value = false
  }
}

function confirmDelete(norm: Norm) {
  confirm.require({
    message: t('catalog.norms.deleteConfirm', { name: norm.exercise.name }),
    header: t('common.confirm'),
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: t('common.delete'),
    rejectLabel: t('common.cancel'),
    acceptProps: { severity: 'danger' },
    accept: async () => {
      try {
        await deleteNorm(norm.id)
        toast.add({ severity: 'success', summary: t('catalog.norms.deleted'), life: 2500 })
        await load()
      } catch (e) {
        toast.add({ severity: 'error', summary: t('common.error'), detail: toMessage(e), life: 4000 })
      }
    },
  })
}

function bandsSummary(bands: NormBand[]): string {
  return bands
    .map((b) => `${b.points}: [${b.lower_bound ?? '−∞'}, ${b.upper_bound ?? '∞'})`)
    .join('  ·  ')
}
</script>

<template>
  <div>
    <PageHeader :title="$t('catalog.norms.title')" :subtitle="$t('catalog.norms.subtitle')">
      <template #actions>
        <Button :label="$t('catalog.norms.newNorm')" icon="pi pi-plus" @click="openCreate" />
      </template>
    </PageHeader>

    <div class="norms__filters">
      <ExerciseSelect
        v-model="filter.exercise"
        :placeholder="$t('catalog.norms.filterExercise')"
        @update:model-value="load"
      />
      <GenderSelect
        v-model="filter.gender"
        :placeholder="$t('catalog.norms.filterGender')"
        @update:model-value="load"
      />
    </div>

    <DataTable :value="norms" :loading="loading" paginator :rows="10" data-key="id">
      <template #empty>{{ $t('catalog.norms.empty') }}</template>
      <Column :header="$t('catalog.columns.exercise')">
        <template #body="{ data }">{{ data.exercise.name }}</template>
      </Column>
      <Column :header="$t('common.fields.gender')">
        <template #body="{ data }">{{ genderLabel(data.gender as Gender) }}</template>
      </Column>
      <Column :header="$t('catalog.norms.age')">
        <template #body="{ data }">{{ data.age_min }}–{{ data.age_max }}</template>
      </Column>
      <Column :header="$t('catalog.norms.bandsColumn')">
        <template #body="{ data }">
          <span class="norms__bands">{{ bandsSummary(data.bands) }}</span>
        </template>
      </Column>
      <Column field="valid_from" :header="$t('catalog.norms.validFrom')" />
      <Column :header="$t('common.fields.status')">
        <template #body="{ data }">
          <Tag
            :value="data.is_active ? $t('catalog.active') : $t('catalog.inactive')"
            :severity="data.is_active ? 'success' : 'secondary'"
          />
        </template>
      </Column>
      <Column header="" style="width: 6rem">
        <template #body="{ data }">
          <Button
            icon="pi pi-pencil"
            text
            rounded
            :aria-label="$t('common.edit')"
            @click="openEdit(data)"
          />
          <Button
            icon="pi pi-trash"
            text
            rounded
            severity="danger"
            :aria-label="$t('common.delete')"
            @click="confirmDelete(data)"
          />
        </template>
      </Column>
    </DataTable>

    <h3 class="norms__section">{{ $t('catalog.norms.thresholdsTitle') }}</h3>
    <p class="norms__hint">{{ $t('catalog.norms.thresholdsHint') }}</p>
    <DataTable :value="thresholds" data-key="id" class="norms__thresholds">
      <Column field="level" :header="$t('catalog.norms.level')" />
      <Column :header="$t('catalog.norms.pointsRange')">
        <template #body="{ data }">{{ data.total_min }}–{{ data.total_max }}</template>
      </Column>
    </DataTable>

    <Dialog
      v-model:visible="dialogVisible"
      :header="editingId ? $t('catalog.norms.editNorm') : $t('catalog.norms.newNorm')"
      modal
      :style="{ width: '540px' }"
    >
      <div class="norms__form">
        <div class="norms__field">
          <label>{{ $t('catalog.columns.exercise') }}</label>
          <ExerciseSelect v-model="form.exercise" />
        </div>
        <div class="norms__row">
          <div class="norms__field">
            <label>{{ $t('common.fields.gender') }}</label>
            <GenderSelect v-model="form.gender" />
          </div>
          <div class="norms__field">
            <label>{{ $t('catalog.norms.ageMin') }}</label>
            <InputNumber v-model="form.age_min" :min="0" :max="99" fluid />
          </div>
          <div class="norms__field">
            <label>{{ $t('catalog.norms.ageMax') }}</label>
            <InputNumber v-model="form.age_max" :min="0" :max="99" fluid />
          </div>
        </div>
        <div class="norms__row">
          <div class="norms__field">
            <label>{{ $t('catalog.norms.validFromDate') }}</label>
            <DatePicker v-model="form.valid_from" date-format="yy-mm-dd" show-icon fluid />
          </div>
          <div class="norms__field norms__field--check">
            <Checkbox v-model="form.is_active" input-id="is_active" binary />
            <label for="is_active">{{ $t('catalog.active') }}</label>
          </div>
        </div>

        <label class="norms__bands-label">{{ $t('catalog.norms.bandsLabel') }}</label>
        <div v-for="(band, i) in form.bands" :key="band.points" class="norms__band-row">
          <span class="norms__band-points">{{ $t('catalog.norms.pointsSuffix', { n: band.points }) }}</span>
          <InputNumber
            v-model="form.bands[i].lower_bound"
            :min-fraction-digits="0"
            :max-fraction-digits="2"
            :placeholder="$t('catalog.norms.lowerPlaceholder')"
            fluid
          />
          <InputNumber
            v-model="form.bands[i].upper_bound"
            :min-fraction-digits="0"
            :max-fraction-digits="2"
            :placeholder="$t('catalog.norms.upperPlaceholder')"
            fluid
          />
        </div>

        <Message v-for="err in formErrors" :key="err" severity="error" size="small" variant="simple">
          {{ err }}
        </Message>
      </div>

      <template #footer>
        <Button :label="$t('common.cancel')" text @click="dialogVisible = false" />
        <Button :label="$t('common.save')" icon="pi pi-check" :loading="saving" @click="save" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.norms__filters {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
  max-width: 520px;
}
.norms__bands {
  font-variant-numeric: tabular-nums;
  font-size: 0.85rem;
}
.norms__section {
  margin: 2rem 0 0.25rem;
}
.norms__hint {
  margin: 0 0 0.75rem;
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
}
.norms__thresholds {
  max-width: 320px;
}
.norms__form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.norms__field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  flex: 1;
}
.norms__field label {
  font-size: 0.85rem;
  font-weight: 500;
}
.norms__field--check {
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
  align-self: flex-end;
  padding-bottom: 0.5rem;
}
.norms__row {
  display: flex;
  gap: 0.75rem;
}
.norms__bands-label {
  font-size: 0.85rem;
  font-weight: 500;
  margin-top: 0.5rem;
}
.norms__band-row {
  display: grid;
  grid-template-columns: 4rem 1fr 1fr;
  align-items: center;
  gap: 0.5rem;
}
.norms__band-points {
  font-weight: 600;
}
</style>
