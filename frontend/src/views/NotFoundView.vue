<script setup lang="ts">
import Button from 'primevue/button'
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="sd-container notfound">
    <h1>404</h1>
    <p>{{ $t('errors.notFound.message') }}</p>
    <Button :label="$t('nav.home')" icon="pi pi-home" @click="router.push('/')" />
  </div>
</template>

<style scoped>
.notfound {
  text-align: center;
  padding-top: 4rem;
}
.notfound h1 {
  font-size: 3rem;
  margin: 0;
}
</style>
