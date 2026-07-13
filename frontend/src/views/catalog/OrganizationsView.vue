<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import {
  createOrganization,
  deleteOrganization,
  getOrganizations,
  updateOrganization,
} from '@/api/catalog'
import { toMessage } from '@/api/client'
import PageHeader from '@/components/PageHeader.vue'
import DistrictSelect from '@/components/pickers/DistrictSelect.vue'
import RegionSelect from '@/components/pickers/RegionSelect.vue'
import { orgTypeLabel } from '@/i18n/labels'
import { useCatalogStore } from '@/stores/catalog'
import type { Organization, OrganizationWrite, OrgType } from '@/types/catalog'

const { t } = useI18n({ useScope: 'global' })
const toast = useToast()
const confirm = useConfirm()
const catalog = useCatalogStore()

const TYPES: OrgType[] = ['OTM', 'OPSTTM']
const typeOptions = computed(() => TYPES.map((value) => ({ value, label: orgTypeLabel(value) })))

const rows = ref<Organization[]>([])
const loading = ref(false)
const filters = reactive({ region: null as number | null, type: null as OrgType | null })

function regionName(id: number | null): string {
  return catalog.regions.find((r) => r.id === id)?.name ?? '—'
}

async function load() {
  loading.value = true
  try {
    const params: { region?: number; type?: OrgType } = {}
    if (filters.region) params.region = filters.region
    if (filters.type) params.type = filters.type
    rows.value = await getOrganizations(params)
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: toMessage(e), life: 4000 })
  } finally {
    loading.value = false
  }
}
onMounted(async () => {
  await catalog.ensureLoaded()
  await load()
})

// --- create / edit ---
const dialog = ref(false)
const editing = ref<Organization | null>(null)
const saving = ref(false)
const errors = ref<string[]>([])
const form = reactive<OrganizationWrite>({ name: '', type: 'OPSTTM', region: null, district: null })

function reset(o: Organization | null) {
  editing.value = o
  errors.value = []
  Object.assign(form, {
    name: o?.name ?? '',
    type: o?.type ?? 'OPSTTM',
    region: o?.region ?? null,
    district: o?.district ?? null,
  })
}
function openNew() {
  reset(null)
  dialog.value = true
}
function openEdit(o: Organization) {
  reset(o)
  dialog.value = true
}

function validate(): boolean {
  const e: string[] = []
  if (!form.name.trim()) e.push(t('orgs.validation.name'))
  if (!form.type) e.push(t('orgs.validation.type'))
  if (!form.region) e.push(t('orgs.validation.region'))
  errors.value = e
  return e.length === 0
}

async function save() {
  if (!validate()) return
  saving.value = true
  try {
    const payload: OrganizationWrite = { ...form, name: form.name.trim() }
    if (editing.value) await updateOrganization(editing.value.id, payload)
    else await createOrganization(payload)
    toast.add({ severity: 'success', summary: t('orgs.saved'), life: 2500 })
    dialog.value = false
    await load()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: toMessage(e), life: 5000 })
  } finally {
    saving.value = false
  }
}

function remove(o: Organization) {
  confirm.require({
    message: t('orgs.deleteConfirm', { name: o.name }),
    header: t('common.confirm'),
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: t('common.delete'),
    rejectLabel: t('common.cancel'),
    acceptProps: { severity: 'danger' },
    accept: async () => {
      try {
        await deleteOrganization(o.id)
        toast.add({ severity: 'success', summary: t('orgs.deleted'), life: 2500 })
        await load()
      } catch (e) {
        toast.add({ severity: 'error', summary: t('common.error'), detail: toMessage(e), life: 4000 })
      }
    },
  })
}
</script>

<template>
  <div>
    <PageHeader :title="$t('orgs.title')">
      <template #actions>
        <Button :label="$t('orgs.new')" icon="pi pi-plus" @click="openNew" />
      </template>
    </PageHeader>

    <div class="orgs__filters">
      <RegionSelect v-model="filters.region" @update:model-value="load" />
      <Select
        v-model="filters.type"
        :options="typeOptions"
        option-label="label"
        option-value="value"
        :placeholder="$t('orgs.type')"
        show-clear
        class="orgs__type"
        @update:model-value="load"
      />
    </div>

    <DataTable :value="rows" :loading="loading" data-key="id" paginator :rows="15" row-hover>
      <template #empty>{{ $t('orgs.empty') }}</template>
      <Column field="name" :header="$t('orgs.name')" sortable />
      <Column :header="$t('orgs.type')">
        <template #body="{ data }"><Tag :value="orgTypeLabel(data.type)" severity="secondary" /></template>
      </Column>
      <Column :header="$t('common.fields.region')">
        <template #body="{ data }">{{ regionName(data.region) }}</template>
      </Column>
      <Column :header="$t('common.actions')" class="orgs__actions">
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
            @click="remove(data)"
          />
        </template>
      </Column>
    </DataTable>

    <Dialog
      v-model:visible="dialog"
      modal
      :header="editing ? $t('orgs.edit') : $t('orgs.new')"
      :style="{ width: '28rem' }"
    >
      <div class="orgs__form">
        <div class="field">
          <label>{{ $t('orgs.name') }} *</label>
          <InputText v-model="form.name" fluid />
        </div>
        <div class="field">
          <label>{{ $t('orgs.type') }} *</label>
          <Select
            v-model="form.type"
            :options="typeOptions"
            option-label="label"
            option-value="value"
            fluid
          />
        </div>
        <div class="field">
          <label>{{ $t('common.fields.region') }} *</label>
          <RegionSelect v-model="form.region" />
        </div>
        <div class="field">
          <label>{{ $t('common.fields.district') }}</label>
          <DistrictSelect v-model="form.district" :region="form.region" />
        </div>
      </div>

      <Message v-for="err in errors" :key="err" severity="error" size="small" variant="simple">
        {{ err }}
      </Message>

      <template #footer>
        <Button :label="$t('common.cancel')" text @click="dialog = false" />
        <Button :label="$t('common.save')" icon="pi pi-check" :loading="saving" @click="save" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.orgs__filters {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}
.orgs__type {
  min-width: 10rem;
}
.orgs__actions {
  white-space: nowrap;
}
.orgs__form {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.field label {
  font-size: 0.85rem;
  font-weight: 500;
}
</style>
