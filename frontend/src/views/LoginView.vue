<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

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
      <h1>Gestión de Activos Operativos</h1>
      <p class="subtitle">Fundación Simón I. Patiño</p>

      <label for="email">Correo</label>
      <input id="email" v-model="email" type="email" required />

      <label for="password">Contraseña</label>
      <input id="password" v-model="password" type="password" required />

      <p v-if="error" class="error">{{ error }}</p>

      <button type="submit" :disabled="cargando">
        {{ cargando ? 'Ingresando...' : 'Ingresar' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f4f6f8;
}
.login-card {
  background: white;
  padding: 2.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  width: 100%;
  max-width: 360px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
h1 {
  font-size: 1.25rem;
  margin: 0;
}
.subtitle {
  color: #666;
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
  background: #1f6feb;
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
</style>
