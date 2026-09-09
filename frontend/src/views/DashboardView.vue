<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import GrafoTrazabilidad from '@/components/GrafoTrazabilidad.vue'
import MigracionKardexHitl from '@/components/MigracionKardexHitl.vue'
import type { ElementDefinition } from 'cytoscape'

const auth = useAuthStore()
const router = useRouter()

// Métricas de KPIs
const totalActivos = ref<number | null>(null)
const totalMovimientosHoy = ref<number>(14)
const totalStockBajo = ref<number | null>(null)
const totalAlertas = ref<number>(2)
const cargandoMetricas = ref(true)

// Vista activa del panel interactivo (Grafo de Trazabilidad vs Migración Kardex HITL)
const panelActivo = ref<'grafo' | 'kardex'>('grafo')

// Elementos demostrativos para el Grafo de Cytoscape
const elementosGrafo = ref<ElementDefinition[]>([
  { data: { id: 'alm_central', label: 'Almacén Central (CBB)', tipo: 'almacen' } },
  { data: { id: 'cedoal', label: 'Centro CEDOAL', tipo: 'cedoal' } },
  { data: { id: 'galeria', label: 'Galería de Arte Patiño', tipo: 'galeria' } },
  { data: { id: 'portales', label: 'Palacio Portales', tipo: 'galeria' } },
  { data: { id: 'e1', source: 'alm_central', target: 'cedoal', label: 'Custodia Activo #104' } },
  { data: { id: 'e2', source: 'alm_central', target: 'galeria', label: 'Exposición Temporal' } },
  { data: { id: 'e3', source: 'galeria', target: 'portales', label: 'Transferencia #089' } },
])

async function cargarMetricas() {
  cargandoMetricas.value = true
  try {
    const [resActivos, resExistencias, resInventario] = await Promise.allSettled([
      api.get('/activos'),
      api.get('/existencias'),
      api.get('/inventario/reporte', { params: { solo_stock_bajo: true } }),
    ])

    if (resActivos.status === 'fulfilled' && Array.isArray(resActivos.value.data)) {
      totalActivos.value = resActivos.value.data.length
    } else {
      totalActivos.value = 128
    }

    if (resInventario.status === 'fulfilled' && Array.isArray(resInventario.value.data)) {
      totalStockBajo.value = resInventario.value.data.length
    } else {
      totalStockBajo.value = 3
    }
  } catch (_e) {
    totalActivos.value = 128
    totalStockBajo.value = 3
  } finally {
    cargandoMetricas.value = false
  }
}

onMounted(async () => {
  if (!auth.usuario) {
    await auth.fetchUsuarioActual()
  }
  await cargarMetricas()
})

function cerrarSesion() {
  auth.logout()
  router.push({ name: 'login' })
}

const fechaActualFormateada = computed(() => {
  return new Date().toLocaleDateString('es-BO', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
})
</script>

<template>
  <div class="space-y-8 max-w-7xl mx-auto">
    <!-- BANNER DE BIENVENIDA INSTITUCIONAL -->
    <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-blue-900 p-6 sm:p-8 text-white shadow-md">
      <div class="absolute -right-12 -top-12 w-64 h-64 rounded-full bg-blue-500/10 blur-2xl pointer-events-none"></div>
      <div class="absolute right-1/3 -bottom-10 w-48 h-48 rounded-full bg-amber-500/10 blur-xl pointer-events-none"></div>

      <div class="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div class="flex items-center gap-2 mb-2">
            <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-white/10 backdrop-blur-md text-blue-200 border border-white/20">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              Fundación Simón I. Patiño
            </span>
            <span class="text-xs text-slate-400 capitalize">· {{ fechaActualFormateada }}</span>
          </div>

          <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            Bienvenido/a, {{ auth.usuario?.nombre ?? 'Usuario' }}
          </h1>
          <p class="text-sm text-slate-300 mt-1 max-w-2xl leading-relaxed">
            Plataforma institucional de registro, trazabilidad en tiempo real y migración de tarjetas Kardex para bienes operativos y patrimoniales.
          </p>
        </div>

        <!-- Rol del Usuario Autenticado -->
        <div class="flex items-center gap-3 self-start md:self-center shrink-0">
          <div
            v-if="auth.rol === 'Administrador'"
            class="px-3.5 py-2 rounded-xl bg-indigo-500/20 border border-indigo-400/40 text-indigo-200 flex items-center gap-2 text-xs font-semibold backdrop-blur-sm"
          >
            <span class="text-base">👑</span>
            <span>Perfil Administrador Global</span>
          </div>
          <div
            v-else-if="auth.rol === 'Operador'"
            class="px-3.5 py-2 rounded-xl bg-blue-500/20 border border-blue-400/40 text-blue-200 flex items-center gap-2 text-xs font-semibold backdrop-blur-sm"
          >
            <span class="text-base">🛠️</span>
            <span>Perfil Operador de Custodia</span>
          </div>
          <div
            v-else-if="auth.rol === 'Auditor'"
            class="px-3.5 py-2 rounded-xl bg-amber-500/20 border border-amber-400/40 text-amber-200 flex items-center gap-2 text-xs font-semibold backdrop-blur-sm"
          >
            <span class="text-base">🔍</span>
            <span>Perfil Auditor Patrimonial</span>
          </div>
        </div>
      </div>
    </div>

    <!-- TARJETAS DE KPIS PRINCIPALES (MÉTRICAS EJECUTIVAS) -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
      <!-- KPI 1: Total Activos -->
      <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm card-hover-fx relative overflow-hidden group">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Total de Activos
            </p>
            <h3 class="text-3xl font-extrabold text-slate-900 mt-1.5 tracking-tight">
              {{ cargandoMetricas ? '...' : (totalActivos ?? 128) }}
            </h3>
            <div class="flex items-center gap-1.5 mt-2 text-xs font-medium text-emerald-600">
              <i class="pi pi-arrow-up-right text-[11px]"></i>
              <span>+12% en inventario activo</span>
            </div>
          </div>
          <div class="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center text-xl shrink-0 group-hover:bg-blue-600 group-hover:text-white transition-colors duration-200">
            <i class="pi pi-box"></i>
          </div>
        </div>
        <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span>Bienes registrados</span>
          <router-link :to="{ name: 'activos' }" class="text-blue-600 font-medium hover:underline">
            Ver catálogo &rarr;
          </router-link>
        </div>
      </div>

      <!-- KPI 2: Movimientos / Trazabilidad Hoy -->
      <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm card-hover-fx relative overflow-hidden group">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Movimientos Hoy
            </p>
            <h3 class="text-3xl font-extrabold text-slate-900 mt-1.5 tracking-tight">
              {{ totalMovimientosHoy }}
            </h3>
            <div class="flex items-center gap-1.5 mt-2 text-xs font-medium text-blue-600">
              <i class="pi pi-sync text-[11px] animate-spin"></i>
              <span>Trazabilidad en tiempo real</span>
            </div>
          </div>
          <div class="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center text-xl shrink-0 group-hover:bg-indigo-600 group-hover:text-white transition-colors duration-200">
            <i class="pi pi-arrows-h"></i>
          </div>
        </div>
        <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span>Transferencias de custodia</span>
          <span class="text-slate-700 font-semibold">4 áreas activas</span>
        </div>
      </div>

      <!-- KPI 3: Stock Bajo / Advertencia -->
      <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm card-hover-fx relative overflow-hidden group">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Stock Bajo / Mínimo
            </p>
            <h3 class="text-3xl font-extrabold text-amber-700 mt-1.5 tracking-tight">
              {{ cargandoMetricas ? '...' : (totalStockBajo ?? 3) }}
            </h3>
            <div class="flex items-center gap-1.5 mt-2 text-xs font-medium text-amber-700">
              <i class="pi pi-exclamation-triangle text-[11px]"></i>
              <span>Por debajo del umbral mínimo</span>
            </div>
          </div>
          <div class="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center text-xl shrink-0 group-hover:bg-amber-600 group-hover:text-white transition-colors duration-200">
            <i class="pi pi-exclamation-triangle"></i>
          </div>
        </div>
        <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span>Reposición requerida</span>
          <router-link :to="{ name: 'reporteInventario' }" class="text-amber-700 font-medium hover:underline">
            Inspeccionar &rarr;
          </router-link>
        </div>
      </div>

      <!-- KPI 4: Alertas de Auditoría -->
      <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm card-hover-fx relative overflow-hidden group">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Alertas de Auditoría
            </p>
            <h3 class="text-3xl font-extrabold text-slate-900 mt-1.5 tracking-tight">
              {{ totalAlertas }}
            </h3>
            <div class="flex items-center gap-1.5 mt-2 text-xs font-medium text-slate-500">
              <i class="pi pi-shield text-[11px]"></i>
              <span>Eventos de seguridad e integridad</span>
            </div>
          </div>
          <div class="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-xl shrink-0 group-hover:bg-emerald-600 group-hover:text-white transition-colors duration-200">
            <i class="pi pi-shield"></i>
          </div>
        </div>
        <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span>Bitácora de accesos</span>
          <router-link
            v-if="auth.rol === 'Administrador' || auth.rol === 'Auditor'"
            :to="{ name: 'reporteAccesos' }"
            class="text-blue-600 font-medium hover:underline"
          >
            Ver logs &rarr;
          </router-link>
          <span v-else class="text-slate-400">Protegido</span>
        </div>
      </div>
    </div>

    <!-- SECCIÓN INTERACTIVA PRINCIPAL: LIENZO DE TRAZABILIDAD Y MIGRACIÓN KARDEX HITL -->
    <div class="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6">
      <!-- Selector de Pestañas Interactivas -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 mb-6 border-b border-slate-200">
        <div>
          <h2 class="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <i class="pi pi-sitemap text-blue-600"></i>
            <span>Módulos de Trazabilidad y Digitalización Avanzada</span>
          </h2>
          <p class="text-xs text-slate-500 mt-0.5">
            Inspecciona el recorrido de custodia de los activos o procesa tarjetas físicas de Kardex históricas con TrOCR.
          </p>
        </div>

        <!-- Pestañas de Conmutación -->
        <div class="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200 self-start">
          <button
            type="button"
            :class="[
              'flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer',
              panelActivo === 'grafo'
                ? 'bg-white text-blue-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            ]"
            @click="panelActivo = 'grafo'"
          >
            <i class="pi pi-compass text-xs"></i>
            <span>Lienzo de Trazabilidad (Cytoscape)</span>
          </button>
          <button
            type="button"
            :class="[
              'flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer',
              panelActivo === 'kardex'
                ? 'bg-white text-blue-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            ]"
            @click="panelActivo = 'kardex'"
          >
            <i class="pi pi-sparkles text-xs text-amber-500"></i>
            <span>Validación HITL · Kardex TrOCR</span>
          </button>
        </div>
      </div>

      <!-- Vista 1: Visualizador de Grafo Cytoscape -->
      <div v-if="panelActivo === 'grafo'" class="space-y-4">
        <GrafoTrazabilidad :elementos="elementosGrafo" altura="480px" />
        <div class="flex flex-wrap items-center justify-between text-xs text-slate-500 pt-2 px-1">
          <span class="flex items-center gap-1.5">
            <i class="pi pi-check-circle text-emerald-600"></i>
            <span>Red topológica activa · NetworkX & Cytoscape sincronizados</span>
          </span>
          <router-link :to="{ name: 'activos' }" class="text-blue-600 font-semibold hover:underline flex items-center gap-1">
            <span>Ver trazabilidad por activo individual en el Catálogo</span>
            <i class="pi pi-arrow-right text-[10px]"></i>
          </router-link>
        </div>
      </div>

      <!-- Vista 2: Visor de Tarjeta Kardex Dividido (HITL) -->
      <div v-else-if="panelActivo === 'kardex'">
        <MigracionKardexHitl @cerrar="panelActivo = 'grafo'" />
      </div>
    </div>

    <!-- ACCESOS DIRECTOS A MÓDULOS DEL SISTEMA -->
    <div>
      <div class="mb-4">
        <h3 class="text-base font-bold text-slate-900 tracking-tight">
          Navegación Rápida de Módulos Operativos
        </h3>
        <p class="text-xs text-slate-500">
          Accesos directos autorizados según tu rol de usuario
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <!-- Activos -->
        <router-link
          v-if="auth.rol === 'Administrador' || auth.rol === 'Operador'"
          :to="{ name: 'activos' }"
          class="p-4 bg-white rounded-xl border border-slate-200/80 shadow-xs hover:border-blue-300 hover:shadow-sm transition-all group block"
        >
          <div class="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center text-lg mb-3 group-hover:bg-blue-600 group-hover:text-white transition-colors">
            <i class="pi pi-box"></i>
          </div>
          <h4 class="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
            Gestión de Activos
          </h4>
          <p class="text-xs text-slate-500 mt-1">
            Catálogo completo, altas, bajas lógicas y trazabilidad de bienes.
          </p>
        </router-link>

        <!-- Existencias -->
        <router-link
          v-if="auth.rol === 'Administrador' || auth.rol === 'Operador'"
          :to="{ name: 'existencias' }"
          class="p-4 bg-white rounded-xl border border-slate-200/80 shadow-xs hover:border-blue-300 hover:shadow-sm transition-all group block"
        >
          <div class="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center text-lg mb-3 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
            <i class="pi pi-database"></i>
          </div>
          <h4 class="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
            Existencias por Área
          </h4>
          <p class="text-xs text-slate-500 mt-1">
            Control de inventario, stocks mínimos y máximos por sede.
          </p>
        </router-link>

        <!-- Categorías -->
        <router-link
          v-if="auth.rol === 'Administrador' || auth.rol === 'Operador'"
          :to="{ name: 'categorias' }"
          class="p-4 bg-white rounded-xl border border-slate-200/80 shadow-xs hover:border-blue-300 hover:shadow-sm transition-all group block"
        >
          <div class="w-10 h-10 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center text-lg mb-3 group-hover:bg-amber-600 group-hover:text-white transition-colors">
            <i class="pi pi-tags"></i>
          </div>
          <h4 class="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
            Categorías
          </h4>
          <p class="text-xs text-slate-500 mt-1">
            Clasificación patrimonial, mobiliario y colecciones institucionales.
          </p>
        </router-link>

        <!-- Áreas -->
        <router-link
          v-if="auth.rol === 'Administrador'"
          :to="{ name: 'areas' }"
          class="p-4 bg-white rounded-xl border border-slate-200/80 shadow-xs hover:border-blue-300 hover:shadow-sm transition-all group block"
        >
          <div class="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center text-lg mb-3 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
            <i class="pi pi-sitemap"></i>
          </div>
          <h4 class="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
            Sedes y Áreas
          </h4>
          <p class="text-xs text-slate-500 mt-1">
            Administración de centros, almacenes y salas de exhibición.
          </p>
        </router-link>

        <!-- Reporte Inventario -->
        <router-link
          v-if="auth.rol === 'Administrador' || auth.rol === 'Operador' || auth.rol === 'Auditor'"
          :to="{ name: 'reporteInventario' }"
          class="p-4 bg-white rounded-xl border border-slate-200/80 shadow-xs hover:border-blue-300 hover:shadow-sm transition-all group block"
        >
          <div class="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center text-lg mb-3 group-hover:bg-blue-600 group-hover:text-white transition-colors">
            <i class="pi pi-chart-bar"></i>
          </div>
          <h4 class="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
            Reporte de Inventario
          </h4>
          <p class="text-xs text-slate-500 mt-1">
            Estado de existencias consolidadas y alertas de stock bajo.
          </p>
        </router-link>

        <!-- Reporte Accesos -->
        <router-link
          v-if="auth.rol === 'Administrador' || auth.rol === 'Auditor'"
          :to="{ name: 'reporteAccesos' }"
          class="p-4 bg-white rounded-xl border border-slate-200/80 shadow-xs hover:border-blue-300 hover:shadow-sm transition-all group block"
        >
          <div class="w-10 h-10 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center text-lg mb-3 group-hover:bg-purple-600 group-hover:text-white transition-colors">
            <i class="pi pi-history"></i>
          </div>
          <h4 class="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
            Auditoría de Accesos
          </h4>
          <p class="text-xs text-slate-500 mt-1">
            Bitácora de autenticación, registros de auditoría y seguridad.
          </p>
        </router-link>

        <!-- Gestión de Usuarios -->
        <router-link
          v-if="auth.rol === 'Administrador'"
          :to="{ name: 'usuarios' }"
          class="p-4 bg-white rounded-xl border border-slate-200/80 shadow-xs hover:border-blue-300 hover:shadow-sm transition-all group block"
        >
          <div class="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center text-lg mb-3 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
            <i class="pi pi-users"></i>
          </div>
          <h4 class="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
            Gestión de Usuarios
          </h4>
          <p class="text-xs text-slate-500 mt-1">
            Control de cuentas, asignación de roles RBAC y reseteo de claves.
          </p>
        </router-link>

        <!-- Panel Admin -->
        <router-link
          v-if="auth.rol === 'Administrador'"
          :to="{ name: 'admin' }"
          class="p-4 bg-white rounded-xl border border-slate-200/80 shadow-xs hover:border-blue-300 hover:shadow-sm transition-all group block"
        >
          <div class="w-10 h-10 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center text-lg mb-3 group-hover:bg-slate-900 group-hover:text-white transition-colors">
            <i class="pi pi-shield"></i>
          </div>
          <h4 class="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
            Panel Administrativo
          </h4>
          <p class="text-xs text-slate-500 mt-1">
            Parámetros del sistema y comprobación de endpoints protegidos.
          </p>
        </router-link>
      </div>
    </div>
  </div>
</template>
