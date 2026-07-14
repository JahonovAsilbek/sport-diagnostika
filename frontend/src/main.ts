import '@fontsource-variable/inter'
import 'primeicons/primeicons.css'
import './assets/main.css'

import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import ConfirmationService from 'primevue/confirmationservice'
import ToastService from 'primevue/toastservice'
import { createApp } from 'vue'

import App from './App.vue'
import i18n from './i18n'
import router from './router'
import { SportPreset } from './theme/preset'
import { useAuthStore } from './stores/auth'

const app = createApp(App)

app.use(createPinia())
app.use(i18n)
app.use(PrimeVue, { theme: { preset: SportPreset, options: { darkModeSelector: '.app-dark' } } })
app.use(ToastService)
app.use(ConfirmationService)

// Restore the stored session BEFORE installing the router. `app.use(router)` kicks off the initial
// navigation (and its auth guard) asynchronously, so it must run only after /me has populated the
// auth store — otherwise, on refresh, the guard races ahead and sees a logged-out state, bouncing a
// valid session to /login before restore() finishes.
const auth = useAuthStore()
auth.restore().finally(() => {
  app.use(router)
  app.mount('#app')
})
