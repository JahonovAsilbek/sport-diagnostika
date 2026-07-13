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
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--gradient-card);
  transition:
    border-color 160ms ease,
    box-shadow 160ms ease;
}
.stat:hover {
  border-color: color-mix(in srgb, var(--color-primary) 45%, var(--color-border));
  box-shadow: var(--shadow-sm);
}
.stat__icon {
  flex-shrink: 0;
  width: 2.75rem;
  height: 2.75rem;
  display: grid;
  place-items: center;
  border-radius: var(--radius);
  background: var(--color-bg-soft);
  font-size: 1.4rem;
  color: var(--color-primary);
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
