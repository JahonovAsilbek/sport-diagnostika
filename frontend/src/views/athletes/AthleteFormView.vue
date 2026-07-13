<script setup lang="ts">
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Textarea from 'primevue/textarea'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { createAthlete, getAthlete, transferAthlete, updateAthlete } from '@/api/athletes'
import { toMessage } from '@/api/client'
import CoachSelect from '@/components/pickers/CoachSelect.vue'
import DistrictSelect from '@/components/pickers/DistrictSelect.vue'
import GenderSelect from '@/components/pickers/GenderSelect.vue'
import OrganizationSelect from '@/components/pickers/OrganizationSelect.vue'
import RegionSelect from '@/components/pickers/RegionSelect.vue'
import SportSelect from '@/components/pickers/SportSelect.vue'
import PageHeader from '@/components/PageHeader.vue'
import type { Gender } from '@/types/catalog'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const { t } = useI18n({ useScope: 'global' })

const editingId = ref<number | null>(route.params.id ? Number(route.params.id) : null)
const saving = ref(false)
const errors = ref<string[]>([])
// Placement (region/district/organization/sport/coach) is transfer-only (BCKND-68). Track the
// loaded values so an edit that changes any of them routes through the transfer endpoint.
const original = reactive({
  region: null as number | null,
  district: null as number | null,
  organization: null as number | null,
  sport_type: null as number | null,
  coach: null as number | null,
})
const reason = ref('')

const form = reactive({
  last_name: '',
  first_name: '',
  middle_name: '',
  birth_year: null as number | null,
  gender: null as Gender | null,
  region: null as number | null,
  district: null as number | null,
  organization: null as number | null,
  sport_type: null as number | null,
  coach: null as number | null,
  razryad: '',
  training_experience: '',
  main_competitions: '',
  is_active: true,
})

onMounted(async () => {
  if (!editingId.value) return
  try {
    const a = await getAthlete(editingId.value)
    Object.assign(form, {
      last_name: a.last_name,
      first_name: a.first_name,
      middle_name: a.middle_name ?? '',
      birth_year: a.birth_year,
      gender: a.gender,
      region: a.region,
      district: a.district,
      organization: a.organization,
      sport_type: a.sport_type,
      coach: a.coach,
      razryad: a.razryad ?? '',
      training_experience: a.training_experience ?? '',
      main_competitions: a.main_competitions ?? '',
      is_active: a.is_active,
    })
    Object.assign(original, {
      region: a.region,
      district: a.district,
      organization: a.organization,
      sport_type: a.sport_type,
      coach: a.coach,
    })
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: toMessage(e), life: 4000 })
  }
})

// True when editing and any placement field differs from the loaded athlete → needs a transfer.
const ASSIGNMENT = ['region', 'district', 'organization', 'sport_type', 'coach'] as const
const placementChanged = computed(
  () => !!editingId.value && ASSIGNMENT.some((field) => form[field] !== original[field]),
)

function validate(): boolean {
  const e: string[] = []
  if (!form.last_name.trim()) e.push(t('athletes.form.validation.lastName'))
  if (!form.first_name.trim()) e.push(t('athletes.form.validation.firstName'))
  if (form.birth_year === null) e.push(t('athletes.form.validation.birthYear'))
  if (!form.gender) e.push(t('athletes.form.validation.gender'))
  if (!form.region) e.push(t('athletes.form.validation.region'))
  if (!form.organization) e.push(t('athletes.form.validation.organization'))
  if (!form.sport_type) e.push(t('athletes.form.validation.sport'))
  errors.value = e
  return e.length === 0
}

// The mutable profile fields — everything except the transfer-only placement.
function profile() {
  return {
    last_name: form.last_name.trim(),
    first_name: form.first_name.trim(),
    middle_name: form.middle_name.trim(),
    birth_year: form.birth_year,
    gender: form.gender,
    razryad: form.razryad.trim(),
    training_experience: form.training_experience.trim(),
    main_competitions: form.main_competitions.trim(),
    is_active: form.is_active,
  }
}

async function save() {
  if (!validate()) return
  // A placement change on edit is a transfer, which records a reason (BCKND-68).
  if (placementChanged.value && !reason.value.trim()) {
    errors.value = [t('athletes.form.validation.transferReason')]
    return
  }
  saving.value = true
  try {
    let id = editingId.value
    if (!id) {
      // Create sets the initial placement in one call.
      const created = await createAthlete({
        ...profile(),
        region: form.region,
        district: form.district,
        organization: form.organization,
        sport_type: form.sport_type,
        coach: form.coach,
      })
      id = created.id
    } else {
      // Edit updates the profile only; placement moves go through the transfer endpoint.
      await updateAthlete(id, profile())
      if (placementChanged.value) {
        await transferAthlete(id, {
          region: form.region,
          district: form.district,
          organization: form.organization,
          sport_type: form.sport_type,
          coach: form.coach,
          reason: reason.value.trim(),
        })
      }
    }
    toast.add({ severity: 'success', summary: t('athletes.form.saved'), life: 2500 })
    router.push(`/athletes/${id}`)
  } catch (e) {
    toast.add({ severity: 'error', summary: t('athletes.form.saveError'), detail: toMessage(e), life: 5000 })
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="form-page">
    <PageHeader :title="editingId ? $t('athletes.form.editTitle') : $t('athletes.newAthlete')" />

    <div class="form-grid">
      <div class="field">
        <label>{{ $t('athletes.form.lastName') }} *</label>
        <InputText v-model="form.last_name" fluid />
      </div>
      <div class="field">
        <label>{{ $t('athletes.form.firstName') }} *</label>
        <InputText v-model="form.first_name" fluid />
      </div>
      <div class="field">
        <label>{{ $t('athletes.form.middleName') }}</label>
        <InputText v-model="form.middle_name" fluid />
      </div>
      <div class="field">
        <label>{{ $t('common.fields.birthYear') }} *</label>
        <InputNumber
          v-model="form.birth_year"
          :use-grouping="false"
          :min="1950"
          :max="2025"
          fluid
        />
      </div>
      <div class="field">
        <label>{{ $t('common.fields.gender') }} *</label>
        <GenderSelect v-model="form.gender" />
      </div>
      <div class="field">
        <label>{{ $t('common.fields.sport') }} *</label>
        <SportSelect v-model="form.sport_type" />
      </div>
      <div class="field">
        <label>{{ $t('common.fields.region') }} *</label>
        <RegionSelect v-model="form.region" />
      </div>
      <div class="field">
        <label>{{ $t('common.fields.district') }}</label>
        <DistrictSelect v-model="form.district" :region="form.region" />
      </div>
      <div class="field">
        <label>{{ $t('common.fields.organization') }} *</label>
        <OrganizationSelect v-model="form.organization" :region="form.region" />
      </div>
      <div class="field">
        <label>{{ $t('common.fields.coach') }}</label>
        <CoachSelect v-model="form.coach" />
      </div>
      <div v-if="placementChanged" class="field field--wide field--transfer">
        <label>{{ $t('athletes.form.transferReason') }} *</label>
        <InputText v-model="reason" fluid />
        <small class="form-transfer-hint">{{ $t('athletes.form.transferReasonHint') }}</small>
      </div>
      <div class="field">
        <label>{{ $t('athletes.razryad') }}</label>
        <InputText v-model="form.razryad" fluid />
      </div>
      <div class="field">
        <label>{{ $t('athletes.form.trainingExperience') }}</label>
        <InputText v-model="form.training_experience" fluid />
      </div>
      <div class="field field--wide">
        <label>{{ $t('athletes.mainCompetitions') }}</label>
        <Textarea v-model="form.main_competitions" rows="2" auto-resize fluid />
      </div>
      <div class="field field--check">
        <Checkbox v-model="form.is_active" input-id="is_active" binary />
        <label for="is_active">{{ $t('athletes.active') }}</label>
      </div>
    </div>

    <Message v-for="err in errors" :key="err" severity="error" size="small" variant="simple">
      {{ err }}
    </Message>

    <div class="form-actions">
      <Button :label="$t('common.cancel')" text @click="router.back()" />
      <Button :label="$t('common.save')" icon="pi pi-check" :loading="saving" @click="save" />
    </div>
  </div>
</template>

<style scoped>
.form-page {
  max-width: 820px;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.field label {
  font-size: 0.85rem;
  font-weight: 500;
}
.field--wide {
  grid-column: 1 / -1;
}
.field--check {
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
}
.field--transfer {
  padding: 0.75rem;
  border: 1px solid var(--p-primary-color);
  border-radius: 8px;
}
.form-transfer-hint {
  color: var(--p-text-muted-color);
  font-size: 0.8rem;
}
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1.5rem;
}
@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
