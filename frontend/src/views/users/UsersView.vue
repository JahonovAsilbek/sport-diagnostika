<script setup lang="ts">
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { toMessage } from '@/api/client'
import {
  createUser,
  deactivateUser,
  listUsers,
  resetPassword,
  updateUser,
  type UserFilters,
} from '@/api/users'
import PageHeader from '@/components/PageHeader.vue'
import OrganizationSelect from '@/components/pickers/OrganizationSelect.vue'
import RegionSelect from '@/components/pickers/RegionSelect.vue'
import { roleLabel } from '@/i18n/labels'
import { useAuthStore } from '@/stores/auth'
import type { Role, User, UserWrite } from '@/types/auth'

const { t } = useI18n({ useScope: 'global' })
const toast = useToast()
const confirm = useConfirm()
const auth = useAuthStore()

const ALL_ROLES: Role[] = ['super_admin', 'region_admin', 'coach', 'lab_operator', 'ministry']
// A region_admin cannot create super_admins (the backend enforces it; hide the option too).
const roleOptions = computed(() =>
  ALL_ROLES.filter((r) => auth.role === 'super_admin' || r !== 'super_admin').map((r) => ({
    value: r,
    label: roleLabel(r),
  })),
)
const roleFilterOptions = computed(() => [
  { value: null, label: t('users.allRoles') },
  ...ALL_ROLES.map((r) => ({ value: r, label: roleLabel(r) })),
])

const rows = ref<User[]>([])
const loading = ref(false)
const filters = reactive({ role: null as Role | null, search: '', activeOnly: false })

async function load() {
  loading.value = true
  try {
    const params: UserFilters = {}
    if (filters.role) params.role = filters.role
    if (filters.search.trim()) params.search = filters.search.trim()
    if (filters.activeOnly) params.is_active = true
    rows.value = (await listUsers(params)).results
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: toMessage(e), life: 4000 })
  } finally {
    loading.value = false
  }
}
onMounted(load)

// --- create / edit ---
const dialog = ref(false)
const editing = ref<User | null>(null)
const saving = ref(false)
const errors = ref<string[]>([])
const form = reactive<UserWrite>({
  username: '',
  password: '',
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  role: null,
  is_active: true,
  region: null,
  organization: null,
})

function reset(u: User | null) {
  editing.value = u
  errors.value = []
  Object.assign(form, {
    username: u?.username ?? '',
    password: '',
    first_name: u?.first_name ?? '',
    last_name: u?.last_name ?? '',
    email: u?.email ?? '',
    phone: u?.phone ?? '',
    role: u?.role ?? null,
    is_active: u?.is_active ?? true,
    region: u?.region?.id ?? null,
    organization: u?.organization?.id ?? null,
  })
}
function openNew() {
  reset(null)
  dialog.value = true
}
function openEdit(u: User) {
  reset(u)
  dialog.value = true
}

function validate(): boolean {
  const e: string[] = []
  if (!form.username.trim()) e.push(t('users.validation.username'))
  if (!editing.value && !form.password) e.push(t('users.validation.password'))
  if (!form.role) e.push(t('users.validation.role'))
  errors.value = e
  return e.length === 0
}

async function save() {
  if (!validate()) return
  saving.value = true
  try {
    const payload: UserWrite = { ...form }
    // On edit an empty password means "keep the current one" — don't send it.
    if (editing.value && !payload.password) delete payload.password
    if (editing.value) await updateUser(editing.value.id, payload)
    else await createUser(payload)
    toast.add({ severity: 'success', summary: t('users.saved'), life: 2500 })
    dialog.value = false
    await load()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: toMessage(e), life: 5000 })
  } finally {
    saving.value = false
  }
}

function deactivate(u: User) {
  confirm.require({
    message: t('users.deactivateConfirm', { name: u.full_name || u.username }),
    header: t('common.confirm'),
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: t('users.deactivate'),
    rejectLabel: t('common.cancel'),
    acceptProps: { severity: 'danger' },
    accept: async () => {
      try {
        await deactivateUser(u.id)
        await load()
      } catch (e) {
        toast.add({ severity: 'error', summary: t('common.error'), detail: toMessage(e), life: 4000 })
      }
    },
  })
}

// --- reset password ---
const pwDialog = ref(false)
const pwTarget = ref<User | null>(null)
const pwValue = ref('')
const pwSaving = ref(false)
function openReset(u: User) {
  pwTarget.value = u
  pwValue.value = ''
  pwDialog.value = true
}
async function doReset() {
  if (!pwTarget.value || !pwValue.value) return
  pwSaving.value = true
  try {
    await resetPassword(pwTarget.value.id, pwValue.value)
    toast.add({ severity: 'success', summary: t('users.resetDone'), life: 2500 })
    pwDialog.value = false
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: toMessage(e), life: 5000 })
  } finally {
    pwSaving.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader :title="$t('users.title')">
      <template #actions>
        <Button :label="$t('users.new')" icon="pi pi-plus" @click="openNew" />
      </template>
    </PageHeader>

    <div class="users__filters">
      <Select
        v-model="filters.role"
        :options="roleFilterOptions"
        option-label="label"
        option-value="value"
        class="users__role"
        @update:model-value="load"
      />
      <IconField>
        <InputIcon class="pi pi-search" />
        <InputText
          v-model="filters.search"
          :placeholder="$t('users.searchPlaceholder')"
          @keyup.enter="load"
        />
      </IconField>
      <label class="users__check">
        <Checkbox v-model="filters.activeOnly" binary @update:model-value="load" />
        {{ $t('users.onlyActive') }}
      </label>
    </div>

    <DataTable :value="rows" :loading="loading" data-key="id" paginator :rows="15" row-hover>
      <template #empty>{{ $t('users.empty') }}</template>
      <Column field="username" :header="$t('users.username')" sortable />
      <Column field="full_name" :header="$t('common.fields.name')" />
      <Column :header="$t('users.role')">
        <template #body="{ data }">{{ roleLabel(data.role) }}</template>
      </Column>
      <Column :header="$t('common.fields.region')">
        <template #body="{ data }">{{ data.region?.name ?? '—' }}</template>
      </Column>
      <Column :header="$t('common.fields.organization')">
        <template #body="{ data }">{{ data.organization?.name ?? '—' }}</template>
      </Column>
      <Column :header="$t('common.fields.status')">
        <template #body="{ data }">
          <Tag
            :value="data.is_active ? $t('users.active') : $t('catalog.inactive')"
            :severity="data.is_active ? 'success' : 'secondary'"
          />
        </template>
      </Column>
      <Column :header="$t('common.actions')" class="users__actions">
        <template #body="{ data }">
          <Button
            icon="pi pi-pencil"
            text
            rounded
            :aria-label="$t('common.edit')"
            @click="openEdit(data)"
          />
          <Button
            icon="pi pi-key"
            text
            rounded
            :aria-label="$t('users.resetPassword')"
            @click="openReset(data)"
          />
          <Button
            v-if="data.is_active"
            icon="pi pi-ban"
            text
            rounded
            severity="danger"
            :aria-label="$t('users.deactivate')"
            @click="deactivate(data)"
          />
        </template>
      </Column>
    </DataTable>

    <Dialog
      v-model:visible="dialog"
      modal
      :header="editing ? $t('users.edit') : $t('users.new')"
      :style="{ width: '30rem' }"
    >
      <div class="users__form">
        <div class="field">
          <label>{{ $t('users.username') }} *</label>
          <InputText v-model="form.username" :disabled="!!editing" fluid />
        </div>
        <div class="field">
          <label>{{ $t('users.password') }} {{ editing ? '' : '*' }}</label>
          <Password v-model="form.password" :feedback="false" toggle-mask fluid />
          <small v-if="editing" class="users__hint">{{ $t('users.passwordEditHint') }}</small>
        </div>
        <div class="field">
          <label>{{ $t('users.firstName') }}</label>
          <InputText v-model="form.first_name" fluid />
        </div>
        <div class="field">
          <label>{{ $t('users.lastName') }}</label>
          <InputText v-model="form.last_name" fluid />
        </div>
        <div class="field">
          <label>{{ $t('users.role') }} *</label>
          <Select
            v-model="form.role"
            :options="roleOptions"
            option-label="label"
            option-value="value"
            fluid
          />
        </div>
        <div class="field">
          <label>{{ $t('common.fields.region') }}</label>
          <RegionSelect v-model="form.region" />
        </div>
        <div class="field">
          <label>{{ $t('common.fields.organization') }}</label>
          <OrganizationSelect v-model="form.organization" :region="form.region" />
        </div>
        <div class="field">
          <label>{{ $t('users.email') }}</label>
          <InputText v-model="form.email" fluid />
        </div>
        <div class="field">
          <label>{{ $t('users.phone') }}</label>
          <InputText v-model="form.phone" fluid />
        </div>
        <label class="users__check">
          <Checkbox v-model="form.is_active" binary />
          {{ $t('users.active') }}
        </label>
      </div>

      <Message v-for="err in errors" :key="err" severity="error" size="small" variant="simple">
        {{ err }}
      </Message>

      <template #footer>
        <Button :label="$t('common.cancel')" text @click="dialog = false" />
        <Button :label="$t('common.save')" icon="pi pi-check" :loading="saving" @click="save" />
      </template>
    </Dialog>

    <Dialog
      v-model:visible="pwDialog"
      modal
      :header="$t('users.resetPassword')"
      :style="{ width: '24rem' }"
    >
      <div class="field">
        <label>{{ $t('users.newPassword') }}</label>
        <Password v-model="pwValue" :feedback="false" toggle-mask fluid />
      </div>
      <template #footer>
        <Button :label="$t('common.cancel')" text @click="pwDialog = false" />
        <Button
          :label="$t('common.save')"
          icon="pi pi-check"
          :loading="pwSaving"
          :disabled="!pwValue"
          @click="doReset"
        />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.users__filters {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}
.users__role {
  min-width: 12rem;
}
.users__check {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}
.users__actions {
  white-space: nowrap;
}
.users__form {
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
.users__hint {
  color: var(--p-text-muted-color);
  font-size: 0.8rem;
}
</style>
