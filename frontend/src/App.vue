<script setup lang="ts">
import ConfirmDialog from 'primevue/confirmdialog'
import Toast from 'primevue/toast'
</script>

<template>
  <Toast position="top-right" />
  <ConfirmDialog />
  <RouterView />
</template>
