<script setup lang="ts">
import PageHeader from '@/components/PageHeader.vue'
import { roleLabel } from '@/constants/labels'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <div>
    <PageHeader
      :title="`Xush kelibsiz, ${auth.user?.full_name || auth.user?.username}`"
      :subtitle="roleLabel(auth.role)"
    />
    <p>Boshqaruv paneli (dashboard) F10 blokida toʻldiriladi.</p>
  </div>
</template>
