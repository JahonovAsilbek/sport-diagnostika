<script setup lang="ts">
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import { useToast } from 'primevue/usetoast'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { toMessage } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

// Bare-but-functional login (FRNTND-1). FRNTND-5 adds validation, "remember me" and polish.
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const toast = useToast()

const username = ref('')
const password = ref('')
const loading = ref(false)

async function submit() {
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    router.push(redirect)
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Kirish xatosi', detail: toMessage(e), life: 4000 })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login">
    <form class="login__card" @submit.prevent="submit">
      <h1 class="login__brand">SPORT-DIAGNOSTIKA.UZ</h1>
      <p class="login__hint">Tizimga kirish</p>
      <label for="username">Login</label>
      <InputText id="username" v-model="username" autocomplete="username" fluid />
      <label for="password">Parol</label>
      <Password
        input-id="password"
        v-model="password"
        :feedback="false"
        toggle-mask
        fluid
        autocomplete="current-password"
      />
      <Button type="submit" label="Kirish" :loading="loading" fluid class="login__submit" />
    </form>
  </div>
</template>

<style scoped>
.login {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 1rem;
}
.login__card {
  width: 100%;
  max-width: 360px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 2rem;
  border-radius: 12px;
  background: var(--p-content-background, #fff);
  box-shadow: 0 6px 24px rgb(0 0 0 / 8%);
}
.login__brand {
  margin: 0;
  font-size: 1.25rem;
  text-align: center;
}
.login__hint {
  margin: 0 0 1rem;
  text-align: center;
  color: var(--p-text-muted-color);
}
.login__card label {
  font-size: 0.875rem;
  font-weight: 500;
}
.login__submit {
  margin-top: 1rem;
}
</style>
