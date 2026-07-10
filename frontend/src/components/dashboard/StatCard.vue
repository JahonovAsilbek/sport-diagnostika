<script setup lang="ts">
// A single KPI tile for the dashboard. `accent` tints the icon (defaults to the primary color).
defineProps<{ label: string; value: number | string; icon: string; accent?: string }>()
</script>

<template>
  <div class="stat">
    <i :class="['stat__icon', icon]" :style="accent ? { color: accent } : undefined" />
    <div class="stat__body">
      <div class="stat__value">{{ value }}</div>
      <div class="stat__label">{{ label }}</div>
    </div>
  </div>
</template>

<style scoped>
.stat {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.1rem 1.25rem;
  border: 1px solid var(--p-content-border-color, #e2e8f0);
  border-radius: 14px;
  background: var(--p-content-background, #fff);
}
.stat__icon {
  font-size: 1.6rem;
  color: var(--p-primary-color);
}
.stat__value {
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1.1;
}
.stat__label {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
  margin-top: 0.15rem;
}
</style>
