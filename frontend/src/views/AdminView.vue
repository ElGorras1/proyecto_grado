<script setup lang="ts">
import { ref } from 'vue'
import api from '@/services/api'

const resultado = ref('')
const probando = ref(false)

async function probarEndpointAdmin() {
  probando.value = true
  resultado.value = ''
  try {
    const { data } = await api.get('/auth/admin/ping')
    resultado.value = data.mensaje
  } catch {
    resultado.value = 'Error al llamar al endpoint administrativo'
  } finally {
    probando.value = false
  }
}
</script>

<template>
  <div class="space-y-6 max-w-4xl mx-auto font-sans">
    <!-- ENCABEZADO -->
    <div class="pb-2 border-b border-slate-200/80">
      <h1 class="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
        <i class="pi pi-shield text-indigo-600"></i>
        <span>Panel de Administración Global</span>
      </h1>
      <p class="text-sm font-medium text-slate-500 mt-1">
        Módulo exclusivo para usuarios con rol de Administrador. Configuración de parámetros y seguridad.
      </p>
    </div>

    <!-- TARJETA DE VERIFICACIÓN DE PRIVILEGIOS -->
    <div class="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200/80 shadow-xs space-y-5">
      <div class="flex items-start gap-4">
        <div class="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center text-xl shrink-0">
          <i class="pi pi-lock"></i>
        </div>
        <div>
          <h3 class="text-base font-bold text-slate-900">
            Comprobación de Integridad y Permisos RBAC
          </h3>
          <p class="text-xs text-slate-500 mt-1 leading-relaxed">
            Verifica la comunicación autenticada contra el endpoint protegido de FastAPI (`/api/v1/auth/admin/ping`).
            Solo las solicitudes con token de un usuario con rol de Administrador son autorizadas por el backend.
          </p>
        </div>
      </div>

      <div class="pt-2">
        <button
          type="button"
          :disabled="probando"
          class="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-xs hover:shadow transition-all disabled:opacity-60 cursor-pointer"
          @click="probarEndpointAdmin"
        >
          <i :class="['pi', probando ? 'pi-spin pi-spinner' : 'pi-check-circle', 'text-xs']"></i>
          <span>{{ probando ? 'Validando con el Servidor...' : 'Probar endpoint protegido (Administrador)' }}</span>
        </button>
      </div>

      <!-- Resultado de la Prueba -->
      <div
        v-if="resultado"
        :class="[
          'p-4 rounded-xl text-xs font-medium flex items-center gap-3 animate-in fade-in',
          resultado.includes('Error')
            ? 'bg-red-50 text-red-700 border border-red-200'
            : 'bg-emerald-50 text-emerald-800 border border-emerald-200'
        ]"
      >
        <i :class="['pi', resultado.includes('Error') ? 'pi-times-circle text-red-500' : 'pi-check-circle text-emerald-600', 'text-base shrink-0']"></i>
        <span>Respuesta del servidor: <strong>{{ resultado }}</strong></span>
      </div>
    </div>
  </div>
</template>
