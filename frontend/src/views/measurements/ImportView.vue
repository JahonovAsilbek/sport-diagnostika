<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import DatePicker from 'primevue/datepicker'
import FileUpload, { type FileUploadSelectEvent } from 'primevue/fileupload'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import { useToast } from 'primevue/usetoast'
import { computed, onBeforeUnmount, ref } from 'vue'

import { toMessage } from '@/api/client'
import { commitImport, downloadTemplate, getImport, uploadImport } from '@/api/imports'
import AgeCategorySelect from '@/components/pickers/AgeCategorySelect.vue'
import GenderSelect from '@/components/pickers/GenderSelect.vue'
import PageHeader from '@/components/PageHeader.vue'
import type { Gender } from '@/types/catalog'
import type { ImportBatch } from '@/types/measurement'

const toast = useToast()

const ageCategory = ref<number | null>(null)
const gender = ref<Gender | null>(null)
const date = ref<Date>(new Date())
const file = ref<File | null>(null)

const batch = ref<ImportBatch | null>(null)
const uploading = ref(false)
const committing = ref(false)

const ready = computed(() => ageCategory.value !== null && gender.value !== null)
const validating = computed(() => batch.value?.status === 'validating')
const errorRows = computed(() => batch.value?.rows.filter((r) => r.errors.length > 0) ?? [])

function isoDate(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

async function template() {
  if (!ready.value) return
  try {
    const blob = await downloadTemplate(ageCategory.value!, gender.value!)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'import_shablon.xlsx'
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Xatolik', detail: toMessage(e), life: 4000 })
  }
}

function onSelect(event: FileUploadSelectEvent) {
  file.value = Array.isArray(event.files) ? event.files[0] : event.files
}

let pollTimer: ReturnType<typeof setTimeout> | undefined
async function poll(batchId: number) {
  try {
    const b = await getImport(batchId)
    batch.value = b
    if (b.status === 'validating') pollTimer = setTimeout(() => poll(batchId), 1500)
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Xatolik', detail: toMessage(e), life: 4000 })
  }
}
onBeforeUnmount(() => clearTimeout(pollTimer))

async function upload() {
  if (!ready.value || !file.value) return
  uploading.value = true
  try {
    const b = await uploadImport(file.value, ageCategory.value!, gender.value!, isoDate(date.value))
    batch.value = b
    if (b.status === 'validating') poll(b.id)
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Yuklashda xatolik', detail: toMessage(e), life: 5000 })
  } finally {
    uploading.value = false
  }
}

async function commit() {
  if (!batch.value) return
  committing.value = true
  try {
    batch.value = await commitImport(batch.value.id)
    toast.add({ severity: 'success', summary: 'Saqlandi', life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Xatolik', detail: toMessage(e), life: 5000 })
  } finally {
    committing.value = false
  }
}
</script>

<template>
  <div class="import">
    <PageHeader title="Excel import" subtitle="Guruh boʻyicha shablon → toʻldirish → yuklash" />

    <div class="import__group">
      <AgeCategorySelect v-model="ageCategory" />
      <GenderSelect v-model="gender" />
      <Button
        label="Shablon yuklab olish"
        icon="pi pi-download"
        severity="secondary"
        outlined
        :disabled="!ready"
        @click="template"
      />
    </div>

    <div class="import__upload">
      <FileUpload
        mode="basic"
        accept=".xlsx"
        :auto="false"
        custom-upload
        choose-label="Fayl tanlash"
        @select="onSelect"
      />
      <DatePicker v-model="date" date-format="yy-mm-dd" show-icon />
      <Button
        label="Yuklash"
        icon="pi pi-upload"
        :disabled="!ready || !file"
        :loading="uploading"
        @click="upload"
      />
    </div>
    <small class="import__hint">Sana barcha satrlar uchun sessiya sanasi sifatida ishlatiladi.</small>

    <div v-if="batch" class="import__result">
      <div v-if="validating" class="import__validating">
        <i class="pi pi-spin pi-spinner" /> Tekshirilmoqda…
      </div>

      <template v-else>
        <div class="import__summary">
          <Tag :value="batch.status" :severity="batch.status === 'failed' ? 'danger' : 'info'" />
          <span>Satrlar: {{ batch.row_count }}</span>
          <span :class="{ 'import__err': batch.error_count > 0 }">Xatolar: {{ batch.error_count }}</span>
        </div>

        <Message v-if="batch.error" severity="error">{{ batch.error }}</Message>

        <DataTable v-if="errorRows.length" :value="errorRows" data-key="row_number" class="import__errors">
          <Column field="row_number" header="Satr" style="width: 5rem" />
          <Column header="Xatolar">
            <template #body="{ data }">{{ data.errors.join('; ') }}</template>
          </Column>
        </DataTable>

        <Button
          v-if="batch.status === 'validated'"
          label="Saqlash (commit)"
          icon="pi pi-check"
          :loading="committing"
          class="import__commit"
          @click="commit"
        />
        <Message v-else-if="batch.status === 'committed'" severity="success" variant="simple">
          Import saqlandi — sessiyalar yaratildi va baholandi.
        </Message>
      </template>
    </div>
  </div>
</template>

<style scoped>
.import__group,
.import__upload {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 0.75rem;
}
.import__group > *:not(button),
.import__upload :deep(.p-datepicker) {
  min-width: 180px;
}
.import__hint {
  color: var(--p-text-muted-color);
  display: block;
  margin-bottom: 1rem;
}
.import__result {
  margin-top: 1.5rem;
}
.import__validating {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--p-text-muted-color);
}
.import__summary {
  display: flex;
  gap: 1.25rem;
  align-items: center;
  margin-bottom: 1rem;
}
.import__err {
  color: var(--p-red-500, #ef4444);
  font-weight: 600;
}
.import__errors {
  max-width: 640px;
  margin-bottom: 1rem;
}
</style>
