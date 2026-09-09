<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

function volverAlDashboard() {
  router.push({ name: 'dashboard' })
}
</script>

<template>
  <div class="min-h-screen bg-slate-100 flex items-center justify-center p-6 font-sans">
    <div class="max-w-md w-full bg-white rounded-2xl shadow-xl border border-slate-200 p-8 text-center space-y-5">
      <!-- Ícono de Seguridad -->
      <div class="w-16 h-16 rounded-2xl bg-amber-50 text-amber-600 border border-amber-200/80 mx-auto flex items-center justify-center text-2xl shadow-inner">
        <i class="pi pi-shield"></i>
      </div>

      <div>
        <span class="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 uppercase tracking-wider mb-2">
          Control de Acceso RBAC
        </span>
        <h1 class="text-2xl font-bold text-slate-900 tracking-tight">
          403 · Acceso Denegado
        </h1>
        <p class="text-xs text-slate-500 mt-2 leading-relaxed">
          Tu rol actual (<strong class="text-slate-800">{{ auth.rol ?? 'Usuario' }}</strong>) no cuenta con las autorizaciones necesarias para visualizar este módulo institucional.
        </p>
      </div>

      <div class="pt-2">
        <button
          type="button"
          class="w-full py-2.5 px-4 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs rounded-xl shadow-xs hover:shadow transition-all flex items-center justify-center gap-2 cursor-pointer"
          @click="volverAlDashboard"
        >
          <i class="pi pi-arrow-left text-xs"></i>
          <span>Volver al Panel Principal</span>
        </button>
      </div>

      <p class="text-[11px] text-slate-400">
        Fundación Simón I. Patiño · Seguridad y Trazabilidad de Activos
      </p>
    </div>
  </div>
</template>
