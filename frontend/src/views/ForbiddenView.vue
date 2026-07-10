<script setup lang="ts">
import Button from 'primevue/button'
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="forbidden">
    <i class="pi pi-lock forbidden__icon" />
    <h1>403</h1>
    <p>Ushbu boʻlimga kirish uchun ruxsatingiz yoʻq.</p>
    <Button label="Bosh sahifa" icon="pi pi-home" @click="router.push('/')" />
  </div>
</template>

<style scoped>
.forbidden {
  text-align: center;
  padding: 4rem 1rem;
}
.forbidden__icon {
  font-size: 2.5rem;
  color: var(--p-text-muted-color);
}
.forbidden h1 {
  font-size: 3rem;
  margin: 0.5rem 0 0;
}
.forbidden p {
  color: var(--p-text-muted-color);
  margin-bottom: 1.5rem;
}
</style>
