<script setup lang="ts">
import Button from 'primevue/button'
import { useRouter } from 'vue-router'

import PageHeader from '@/components/PageHeader.vue'
import { roleLabel } from '@/constants/labels'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function doLogout() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="sd-container">
    <PageHeader
      :title="`Xush kelibsiz, ${auth.user?.full_name || auth.user?.username}`"
      :subtitle="roleLabel(auth.role)"
    >
      <template #actions>
        <Button
          label="Chiqish"
          icon="pi pi-sign-out"
          severity="secondary"
          outlined
          @click="doLogout"
        />
      </template>
    </PageHeader>
    <p>Boshqaruv paneli keyingi bloklarda toʻldiriladi.</p>
  </div>
</template>
