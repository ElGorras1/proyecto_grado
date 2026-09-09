<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '@/services/api'

interface AccesoLog {
  id: number
  usuario_id: number | null
  resultado: string
  fecha_hora: string
  ip_origen: string | null
  detalle: Record<string, unknown> | null
}

const accesos = ref<AccesoLog[]>([])
const fechaDesde = ref('')
const fechaHasta = ref('')
const resultado = ref('')
const filtroBusqueda = ref('')
const cargando = ref(false)
const error = ref('')

async function cargarAccesos() {
  cargando.value = true
  error.value = ''
  try {
    const params: Record<string, string> = {}
    if (fechaDesde.value) params.fecha_desde = fechaDesde.value
    if (fechaHasta.value) params.fecha_hasta = fechaHasta.value
    if (resultado.value) params.resultado = resultado.value

    const { data } = await api.get('/auditoria/accesos', { params })
    accesos.value = data
  } catch {
    error.value = 'Error al cargar los registros de acceso y auditoría'
  } finally {
    cargando.value = false
  }
}

function formatearFecha(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('es-BO', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

const accesosFiltrados = computed(() => {
  if (!filtroBusqueda.value.trim()) return accesos.value
  const q = filtroBusqueda.value.toLowerCase()
  return accesos.value.filter((a) => {
    const usuarioStr = (a.usuario_id?.toString() ?? 'desconocido').toLowerCase()
    const ipStr = (a.ip_origen ?? '').toLowerCase()
    return usuarioStr.includes(q) || ipStr.includes(q)
  })
})

onMounted(cargarAccesos)
</script>

<template>
  <div class="space-y-6 max-w-7xl mx-auto font-sans">
    <!-- ENCABEZADO -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
      <div>
        <h1 class="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
          <i class="pi pi-history text-blue-600"></i>
          <span>Reporte de Accesos y Auditoría de Seguridad</span>
        </h1>
        <p class="text-sm font-medium text-slate-500 mt-1">
          Bitácora inmutable de inicios de sesión, IPs de origen y eventos de autenticación
        </p>
      </div>

      <button
        class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs hover:shadow transition-all disabled:opacity-60 cursor-pointer self-start sm:self-auto"
        :disabled="cargando"
        @click="cargarAccesos"
      >
        <i :class="['pi', cargando ? 'pi-spin pi-spinner' : 'pi-refresh', 'text-xs']"></i>
        <span>{{ cargando ? 'Consultando...' : 'Actualizar Bitácora' }}</span>
      </button>
    </div>

    <!-- ALERTAS -->
    <div
      v-if="error"
      class="p-4 rounded-xl bg-red-50 border border-red-200/80 text-xs font-medium text-red-700 flex items-center gap-3 animate-in fade-in"
    >
      <i class="pi pi-exclamation-circle text-red-600 shrink-0 text-base"></i>
      <span>{{ error }}</span>
    </div>

    <!-- FILTROS DE AUDITORÍA -->
    <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-4">
      <div class="relative flex-1 min-w-[220px] max-w-sm">
        <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
          <i class="pi pi-search text-xs"></i>
        </span>
        <input
          v-model="filtroBusqueda"
          type="text"
          placeholder="Buscar por ID de usuario o dirección IP..."
          class="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
        />
      </div>

      <div class="flex flex-wrap items-center gap-3">
        <div class="flex items-center gap-1.5">
          <label class="text-xs font-semibold text-slate-500">Desde:</label>
          <input
            v-model="fechaDesde"
            type="date"
            class="px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div class="flex items-center gap-1.5">
          <label class="text-xs font-semibold text-slate-500">Hasta:</label>
          <input
            v-model="fechaHasta"
            type="date"
            class="px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div class="flex items-center gap-1.5">
          <label class="text-xs font-semibold text-slate-500">Resultado:</label>
          <select
            v-model="resultado"
            class="px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
          >
            <option value="">Todos los eventos</option>
            <option value="exito">Éxito</option>
            <option value="rechazo">Rechazo / Fallo</option>
          </select>
        </div>

        <button
          type="button"
          :disabled="cargando"
          class="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg transition-colors cursor-pointer"
          @click="cargarAccesos"
        >
          Aplicar Filtros
        </button>
      </div>
    </div>

    <!-- TABLA DE AUDITORÍA -->
    <div class="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      <div v-if="cargando" class="py-16 text-center text-slate-500">
        <i class="pi pi-spin pi-spinner text-2xl text-blue-600 mb-2"></i>
        <p class="text-xs font-medium">Recuperando registros de auditoría...</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table v-if="accesosFiltrados.length > 0" class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-50 text-slate-700 font-semibold uppercase text-xs tracking-wider border-b border-slate-200">
              <th class="py-3.5 px-4">Marca Temporal</th>
              <th class="py-3.5 px-4">Usuario ID</th>
              <th class="py-3.5 px-4">Resultado de Autenticación</th>
              <th class="py-3.5 px-4 font-mono">Dirección IP de Origen</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-xs text-slate-700">
            <tr
              v-for="a in accesosFiltrados"
              :key="a.id"
              class="hover:bg-slate-50/80 transition-colors"
            >
              <td class="py-3.5 px-4 font-medium text-slate-900 whitespace-nowrap">
                <i class="pi pi-clock text-[10px] text-slate-400 mr-1.5"></i>
                {{ formatearFecha(a.fecha_hora) }}
              </td>
              <td class="py-3.5 px-4">
                <span v-if="a.usuario_id" class="font-bold text-slate-800">
                  Usuario #{{ a.usuario_id }}
                </span>
                <span v-else class="text-slate-400 italic">Desconocido / Anónimo</span>
              </td>
              <td class="py-3.5 px-4 whitespace-nowrap">
                <span
                  v-if="a.resultado === 'exito'"
                  class="badge-status-activo"
                >
                  <i class="pi pi-check text-[10px] mr-1 text-emerald-600"></i>
                  Inicio Autorizado
                </span>
                <span
                  v-else
                  class="badge-status-danger"
                >
                  <i class="pi pi-times text-[10px] mr-1 text-red-600"></i>
                  Acceso Rechazado
                </span>
              </td>
              <td class="py-3.5 px-4 font-mono text-slate-600 whitespace-nowrap">
                {{ a.ip_origen ?? '—' }}
              </td>
            </tr>
          </tbody>
        </table>

        <div v-else class="py-16 text-center text-slate-500">
          <i class="pi pi-shield text-3xl text-slate-300 mb-2"></i>
          <p class="text-xs font-semibold text-slate-700">No hay eventos de acceso registrados para el período seleccionado</p>
        </div>
      </div>

      <div class="px-4 py-3 bg-slate-50 border-t border-slate-200/80 flex items-center justify-between text-xs text-slate-500">
        <span>Eventos registrados: {{ accesosFiltrados.length }}</span>
        <span class="font-medium">Fundación Simón I. Patiño · Bitácora de Integridad</span>
      </div>
    </div>
  </div>
</template>
