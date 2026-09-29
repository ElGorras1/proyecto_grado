<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import MarcaInstitucional from '@/components/MarcaInstitucional.vue'

const email = ref('')
const password = ref('')
const error = ref('')
const cargando = ref(false)

const auth = useAuthStore()
const router = useRouter()

async function onSubmit() {
  error.value = ''
  cargando.value = true
  try {
    await auth.login(email.value, password.value)
    router.push({ name: 'dashboard' })
  } catch (e) {
    error.value = 'Credenciales incorrectas'
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <form class="login-card" @submit.prevent="onSubmit">
      <MarcaInstitucional class="login-marca" />
      <h1>Bienvenido</h1>
      <p class="subtitle">Ingresa a la gestión de inventario.</p>

      <label for="email">Correo</label>
      <input id="email" v-model="email" type="email" autocomplete="username" placeholder="tu.correo@ejemplo.com" required />

      <label for="password">Contraseña</label>
      <input id="password" v-model="password" type="password" autocomplete="current-password" required />

      <p v-if="error" class="error" role="alert">{{ error }}</p>

      <button type="submit" :disabled="cargando">
        {{ cargando ? 'Ingresando...' : 'Ingresar al sistema' }}
      </button>
      <p class="pie-login">Fundación Simón I. Patiño · Acceso institucional</p>
    </form>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  min-height: 100dvh;
  padding: 1.5rem;
  background: #f4f6f8;
}
.login-card {
  background: white;
  padding: 2.5rem;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow);
  width: 100%;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.login-marca { align-self: center; margin: 0 0 1.8rem; width: 206px; height: 100px; }
.pie-login { font-size: .72rem; color: var(--text-secondary); text-align: center; margin: 1.4rem 0 0; }
h1 {
  font-size: 1.65rem;
  margin: 0;
}
.subtitle {
  color: var(--text-secondary);
  margin: 0 0 1rem 0;
  font-size: 0.9rem;
}
input {
  padding: 0.6rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  margin-bottom: 0.75rem;
}
button {
  margin-top: 0.5rem;
  padding: 0.7rem;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}
button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.error {
  color: #d33;
  font-size: 0.85rem;
}
@media (max-width: 480px) { .login-card { padding: 1.5rem; } }
</style>
