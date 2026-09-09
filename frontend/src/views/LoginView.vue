<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const email = ref('')
const password = ref('')
const error = ref('')
const cargando = ref(false)
const verPassword = ref(false)

const auth = useAuthStore()
const router = useRouter()

async function onSubmit() {
  error.value = ''
  cargando.value = true
  try {
    await auth.login(email.value, password.value)
    router.push({ name: 'dashboard' })
  } catch (_e) {
    error.value = 'Credenciales incorrectas. Verifique su correo y contraseña.'
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-100 flex flex-col justify-center items-center p-4 sm:p-6 lg:p-8 font-sans">
    <!-- Contenedor Principal de la Tarjeta -->
    <div class="w-full max-w-md bg-white rounded-2xl shadow-xl border border-slate-200/80 overflow-hidden">
      <!-- Cabecera Institucional con Gradiente Ejecutivo -->
      <div class="bg-gradient-to-r from-slate-900 via-slate-800 to-blue-900 p-8 text-center text-white relative overflow-hidden">
        <!-- Detalle de fondo sutil -->
        <div class="absolute -right-8 -bottom-8 w-32 h-32 rounded-full bg-blue-500/10 blur-xl pointer-events-none"></div>
        <div class="absolute -left-8 -top-8 w-32 h-32 rounded-full bg-amber-500/10 blur-xl pointer-events-none"></div>

        <!-- Emblema / Monograma -->
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 text-white font-black text-2xl shadow-inner mb-3">
          P
        </div>

        <h1 class="text-xl font-bold tracking-tight text-white">
          Fundación Simón I. Patiño
        </h1>
        <p class="text-xs text-blue-200 font-medium mt-1">
          Sistema de Gestión y Trazabilidad de Activos
        </p>
        <div class="mt-3">
          <span class="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/20 text-blue-200 border border-blue-400/30">
            Módulo Seguro de Autenticación
          </span>
        </div>
      </div>

      <!-- Formulario de Acceso -->
      <div class="p-6 sm:p-8">
        <form class="space-y-4" @submit.prevent="onSubmit">
          <!-- Campo Correo -->
          <div>
            <label for="email" class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Correo Electrónico
            </label>
            <div class="relative">
              <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <i class="pi pi-envelope text-sm"></i>
              </span>
              <input
                id="email"
                v-model="email"
                type="email"
                required
                placeholder="ejemplo@patino.org"
                class="w-full pl-9 pr-3 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>
          </div>

          <!-- Campo Contraseña -->
          <div>
            <label for="password" class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Contraseña
            </label>
            <div class="relative">
              <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <i class="pi pi-lock text-sm"></i>
              </span>
              <input
                id="password"
                v-model="password"
                :type="verPassword ? 'text' : 'password'"
                required
                placeholder="••••••••"
                class="w-full pl-9 pr-10 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none cursor-pointer"
                @click="verPassword = !verPassword"
              >
                <i :class="['pi text-sm', verPassword ? 'pi-eye-slash' : 'pi-eye']"></i>
              </button>
            </div>
          </div>

          <!-- Mensaje de Error -->
          <div
            v-if="error"
            class="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700 animate-in fade-in"
          >
            <i class="pi pi-exclamation-circle text-red-500 shrink-0"></i>
            <span>{{ error }}</span>
          </div>

          <!-- Botón de Ingreso -->
          <button
            type="submit"
            :disabled="cargando"
            class="w-full mt-2 py-2.5 px-4 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold text-sm rounded-lg shadow-sm hover:shadow transition-all duration-150 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer"
          >
            <i v-if="cargando" class="pi pi-spin pi-spinner text-sm"></i>
            <span>{{ cargando ? 'Iniciando sesión...' : 'Ingresar a la Plataforma' }}</span>
          </button>
        </form>
      </div>
    </div>

    <!-- Pie de página institucional -->
    <p class="mt-6 text-xs text-slate-400 text-center font-medium">
      Fundación Simón I. Patiño &copy; 2026 · Todos los derechos reservados.
    </p>
  </div>
</template>
