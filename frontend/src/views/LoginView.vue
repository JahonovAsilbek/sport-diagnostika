<script setup lang="ts">
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import { useToast } from 'primevue/usetoast'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { toMessage } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const toast = useToast()

const username = ref('')
const password = ref('')
const remember = ref(true)
const loading = ref(false)
const submitted = ref(false)

const usernameInvalid = computed(() => submitted.value && username.value.trim() === '')
const passwordInvalid = computed(() => submitted.value && password.value === '')

async function submit() {
  submitted.value = true
  if (usernameInvalid.value || passwordInvalid.value) return
  loading.value = true
  try {
    await auth.login(username.value.trim(), password.value, remember.value)
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
    <form class="login__card" novalidate @submit.prevent="submit">
      <h1 class="login__brand">SPORT-DIAGNOSTIKA.UZ</h1>
      <p class="login__hint">Tizimga kirish</p>

      <div class="login__field">
        <label for="username">Login</label>
        <InputText
          id="username"
          v-model="username"
          autocomplete="username"
          :invalid="usernameInvalid"
          fluid
        />
        <Message v-if="usernameInvalid" severity="error" size="small" variant="simple">
          Loginni kiriting.
        </Message>
      </div>

      <div class="login__field">
        <label for="password">Parol</label>
        <Password
          input-id="password"
          v-model="password"
          :feedback="false"
          toggle-mask
          :invalid="passwordInvalid"
          fluid
          autocomplete="current-password"
        />
        <Message v-if="passwordInvalid" severity="error" size="small" variant="simple">
          Parolni kiriting.
        </Message>
      </div>

      <div class="login__remember">
        <Checkbox v-model="remember" input-id="remember" binary />
        <label for="remember">Meni eslab qol</label>
      </div>

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
  gap: 0.75rem;
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
  margin: 0 0 0.5rem;
  text-align: center;
  color: var(--p-text-muted-color);
}
.login__field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.login__field label {
  font-size: 0.875rem;
  font-weight: 500;
}
.login__remember {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
}
.login__submit {
  margin-top: 0.5rem;
}
</style>
