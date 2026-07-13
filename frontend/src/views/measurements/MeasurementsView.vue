<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import DatePicker from 'primevue/datepicker'
import Dialog from 'primevue/dialog'
import Tag from 'primevue/tag'
import { useToast } from 'primevue/usetoast'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { toMessage } from '@/api/client'
import { createSession, listSessions } from '@/api/measurements'
import AthleteAutocomplete from '@/components/pickers/AthleteAutocomplete.vue'
import PageHeader from '@/components/PageHeader.vue'
import { useAuthStore } from '@/stores/auth'
import type { Athlete } from '@/types/athlete'
import type { TestSession } from '@/types/measurement'
import { canWrite } from '@/utils/permissions'

const router = useRouter()
const toast = useToast()
const auth = useAuthStore()
const { t } = useI18n({ useScope: 'global' })

const sessions = ref<TestSession[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    sessions.value = (await listSessions()).results
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: toMessage(e), life: 4000 })
  } finally {
    loading.value = false
  }
}

onMounted(load)

// --- new session dialog ---
const dialog = ref(false)
const newAthlete = ref<Athlete | null>(null)
const newDate = ref<Date>(new Date())
const creating = ref(false)

function isoDate(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

async function create() {
  if (!newAthlete.value) return
  creating.value = true
  try {
    const session = await createSession({ athlete: newAthlete.value.id, date: isoDate(newDate.value) })
    dialog.value = false
    router.push(`/measurements/session/${session.id}`)
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: toMessage(e), life: 4000 })
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader :title="$t('measurements.list.title')" :subtitle="$t('measurements.list.subtitle')">
      <template #actions>
        <Button
          :label="$t('measurements.list.excelImport')"
          icon="pi pi-file-excel"
          severity="secondary"
          outlined
          @click="router.push('/measurements/import')"
        />
        <Button
          v-if="canWrite(auth.role)"
          :label="$t('measurements.list.newSession')"
          icon="pi pi-plus"
          @click="dialog = true"
        />
      </template>
    </PageHeader>

    <DataTable
      :value="sessions"
      :loading="loading"
      paginator
      :rows="10"
      data-key="id"
      row-hover
      @row-click="router.push(`/measurements/session/${$event.data.id}`)"
    >
      <template #empty>{{ $t('measurements.list.empty') }}</template>
      <Column field="date" :header="$t('common.fields.date')" sortable />
      <Column :header="$t('common.fields.status')">
        <template #body="{ data }">
          <Tag
            :value="data.status === 'draft' ? $t('measurements.status.draft') : $t('measurements.status.finalized')"
            :severity="data.status === 'draft' ? 'warn' : 'success'"
          />
        </template>
      </Column>
      <Column header="" style="width: 8rem">
        <template #body="{ data }">
          <Button :label="$t('measurements.list.open')" text icon="pi pi-arrow-right" @click="router.push(`/measurements/session/${data.id}`)" />
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="dialog" :header="$t('measurements.list.dialogTitle')" modal :style="{ width: '420px' }">
      <div class="new-session">
        <div class="field">
          <label>{{ $t('common.fields.athlete') }}</label>
          <AthleteAutocomplete v-model="newAthlete" />
        </div>
        <div class="field">
          <label>{{ $t('common.fields.date') }}</label>
          <DatePicker v-model="newDate" date-format="yy-mm-dd" show-icon fluid />
        </div>
      </div>
      <template #footer>
        <Button :label="$t('common.cancel')" text @click="dialog = false" />
        <Button :label="$t('measurements.list.create')" icon="pi pi-check" :disabled="!newAthlete" :loading="creating" @click="create" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.new-session {
  display: flex;
  flex-direction: column;
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
</style>
