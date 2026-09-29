import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import { definePreset } from '@primevue/themes'

import App from './App.vue'
import router from './router'

import 'primeicons/primeicons.css'
import './assets/minimalist.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
  theme: {
    preset: definePreset(Aura, {
      semantic: {
        primary: { 50: '#f2f6f9', 100: '#e3ecf3', 200: '#c5d7e4', 300: '#9dbbd0', 400: '#7096b2', 500: '#527c9b', 600: '#436986', 700: '#34556f', 800: '#2b455a', 900: '#263b4d', 950: '#182834' },
      },
    }),
    options: { darkModeSelector: false },
  },
})

app.mount('#app')
