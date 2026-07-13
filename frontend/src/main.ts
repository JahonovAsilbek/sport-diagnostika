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

// Dark by default — the premium look is a dark theme (FRNTND-29). The class also drives PrimeVue's
// dark color scheme via darkModeSelector below.
document.documentElement.classList.add('dark')

const app = createApp(App)

app.use(createPinia())
app.use(i18n)
app.use(router)
app.use(PrimeVue, { theme: { preset: SportPreset, options: { darkModeSelector: '.dark' } } })
app.use(ToastService)
app.use(ConfirmationService)

// Validate the stored session (via /me) before mounting so guards see the right auth state
// on first paint. Failure just leaves the user logged out.
const auth = useAuthStore()
auth.restore().finally(() => {
  app.mount('#app')
})
