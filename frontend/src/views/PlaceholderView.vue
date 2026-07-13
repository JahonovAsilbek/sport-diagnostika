<script setup lang="ts">
import { useRoute } from 'vue-router'

import PageHeader from '@/components/PageHeader.vue'

// Stub for a section whose real view arrives in a later F-block. The route's meta.title names it.
const route = useRoute()
</script>

<template>
  <PageHeader
    :title="(route.meta.title as string) ?? $t('errors.placeholder.title')"
    :subtitle="$t('errors.placeholder.subtitle')"
  />
</template>
