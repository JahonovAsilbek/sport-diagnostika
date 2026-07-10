<script setup lang="ts">
defineProps<{ title: string; subtitle?: string }>()
</script>

<template>
  <header class="page-header">
    <div>
      <h1 class="page-header__title">{{ title }}</h1>
      <p v-if="subtitle" class="page-header__subtitle">{{ subtitle }}</p>
    </div>
    <div class="page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1.5rem;
}
.page-header__title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}
.page-header__subtitle {
  margin: 0.25rem 0 0;
  color: var(--p-text-muted-color);
}
.page-header__actions {
  display: flex;
  gap: 0.5rem;
}
</style>
