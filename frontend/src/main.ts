import 'primeicons/primeicons.css'
import './assets/main.css'

import Aura from '@primeuix/themes/aura'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import ConfirmationService from 'primevue/confirmationservice'
import ToastService from 'primevue/toastservice'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(PrimeVue, { theme: { preset: Aura, options: { darkModeSelector: '.dark' } } })
app.use(ToastService)
app.use(ConfirmationService)

// Validate the stored session (via /me) before mounting so guards see the right auth state
// on first paint. Failure just leaves the user logged out.
const auth = useAuthStore()
auth.restore().finally(() => {
  app.mount('#app')
})
