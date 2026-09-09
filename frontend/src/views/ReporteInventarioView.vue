<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import api from '@/services/api'

interface ItemInventario {
  existencia_id: number
  activo_id: number
  activo_codigo: string
  activo_nombre: string
  categoria_id: number
  categoria_nombre: string
  area_id: number
  area_nombre: string
  cantidad: number
  stock_minimo: number | null
  stock_maximo: number | null
  unidad_medida: string
  stock_bajo: boolean
  estado: string
}

interface Categoria {
  id: number
  nombre: string
}

interface Area {
  id: number
  nombre: string
}

const items = ref<ItemInventario[]>([])
const categorias = ref<Categoria[]>([])
const areas = ref<Area[]>([])
const cargando = ref(false)
const error = ref('')

// Filtros
const filtroCategoria = ref<number | ''>('')
const filtroArea = ref<number | ''>('')
const soloStockBajo = ref(false)
const filtroBusqueda = ref('')

async function cargarFiltros() {
  try {
    const [resCat, resArea] = await Promise.all([
      api.get('/categorias'),
      api.get('/areas'),
    ])
    categorias.value = resCat.data
    areas.value = resArea.data
  } catch {
    // Si falla cargar catálogos auxiliares no detenemos la vista
  }
}

async function cargarReporte() {
  cargando.value = true
  error.value = ''
  try {
    const params: Record<string, unknown> = {}
    if (filtroCategoria.value) params.categoria_id = Number(filtroCategoria.value)
    if (filtroArea.value) params.area_id = Number(filtroArea.value)
    if (soloStockBajo.value) params.solo_stock_bajo = true

    const { data } = await api.get('/inventario/reporte', { params })
    items.value = data
  } catch (err) {
    if (axios.isAxiosError(err)) {
      error.value = err.response?.data?.detail || 'Error al cargar el reporte de inventario'
    } else {
      error.value = 'Error al cargar el reporte de inventario'
    }
  } finally {
    cargando.value = false
  }
}

const itemsFiltrados = computed(() => {
  if (!filtroBusqueda.value.trim()) return items.value
  const q = filtroBusqueda.value.toLowerCase()
  return items.value.filter((i) => {
    return (
      i.activo_nombre.toLowerCase().includes(q) ||
      i.activo_codigo.toLowerCase().includes(q) ||
      i.area_nombre.toLowerCase().includes(q)
    )
  })
})

const conteoStockBajo = computed(() => {
  return items.value.filter((i) => i.stock_bajo).length
})

onMounted(async () => {
  await cargarFiltros()
  await cargarReporte()
})
</script>

<template>
  <div class="space-y-6 max-w-7xl mx-auto font-sans">
    <!-- ENCABEZADO -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
      <div>
        <h1 class="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
          <i class="pi pi-chart-bar text-blue-600"></i>
          <span>Reporte de Inventario Consolidado</span>
        </h1>
        <p class="text-sm font-medium text-slate-500 mt-1">
          Informe de existencias por activo, área y monitoreo de niveles críticos
        </p>
      </div>

      <button
        class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs hover:shadow transition-all disabled:opacity-60 cursor-pointer self-start sm:self-auto"
        :disabled="cargando"
        @click="cargarReporte"
      >
        <i :class="['pi', cargando ? 'pi-spin pi-spinner' : 'pi-refresh', 'text-xs']"></i>
        <span>{{ cargando ? 'Actualizando...' : 'Actualizar Reporte' }}</span>
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

    <!-- BANNER DE AVISO DE STOCK BAJO -->
    <div
      v-if="conteoStockBajo > 0"
      class="p-4 rounded-xl bg-amber-50 border border-amber-200/90 text-xs text-amber-900 flex items-center justify-between gap-4 shadow-xs"
    >
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-700 flex items-center justify-center font-bold text-base shrink-0">
          <i class="pi pi-exclamation-triangle"></i>
        </div>
        <div>
          <span class="font-bold text-amber-950">Atención requerida:</span>
          <span> Se han detectado <strong>{{ conteoStockBajo }} ítem(s) con stock por debajo del umbral mínimo configurado</strong>. Requieren reposición inmediata.</span>
        </div>
      </div>
      <button
        type="button"
        class="px-3 py-1.5 rounded-lg bg-amber-200/80 hover:bg-amber-300/80 text-amber-900 font-semibold text-xs transition-colors shrink-0 cursor-pointer"
        @click="soloStockBajo = !soloStockBajo; cargarReporte()"
      >
        {{ soloStockBajo ? 'Mostrar Todo' : 'Filtrar Críticos' }}
      </button>
    </div>

    <!-- FILTROS DEL REPORTE -->
    <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-4">
      <div class="relative flex-1 min-w-[240px] max-w-md">
        <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
          <i class="pi pi-search text-xs"></i>
        </span>
        <input
          v-model="filtroBusqueda"
          type="text"
          placeholder="Buscar por código, denominación o área..."
          class="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
        />
      </div>

      <div class="flex flex-wrap items-center gap-4">
        <div class="flex items-center gap-1.5">
          <label class="text-xs font-semibold text-slate-500">Categoría:</label>
          <select
            v-model="filtroCategoria"
            class="px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
            @change="cargarReporte"
          >
            <option value="">Todas las categorías</option>
            <option v-for="c in categorias" :key="c.id" :value="c.id">
              {{ c.nombre }}
            </option>
          </select>
        </div>

        <div class="flex items-center gap-1.5">
          <label class="text-xs font-semibold text-slate-500">Área / Sede:</label>
          <select
            v-model="filtroArea"
            class="px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
            @change="cargarReporte"
          >
            <option value="">Todas las áreas</option>
            <option v-for="a in areas" :key="a.id" :value="a.id">
              {{ a.nombre }}
            </option>
          </select>
        </div>

        <!-- Toggle Checkbox Stock Bajo -->
        <label class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 cursor-pointer select-none">
          <input
            v-model="soloStockBajo"
            type="checkbox"
            class="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 cursor-pointer"
            @change="cargarReporte"
          />
          <span class="text-xs font-semibold text-slate-700">Solo stock bajo</span>
        </label>
      </div>
    </div>

    <!-- TABLA DE REPORTE -->
    <div class="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      <div v-if="cargando" class="py-16 text-center text-slate-500">
        <i class="pi pi-spin pi-spinner text-2xl text-blue-600 mb-2"></i>
        <p class="text-xs font-medium">Generando reporte de inventario...</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table v-if="itemsFiltrados.length > 0" class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-50 text-slate-700 font-semibold uppercase text-xs tracking-wider border-b border-slate-200">
              <th class="py-3.5 px-4">Código</th>
              <th class="py-3.5 px-4">Denominación del Activo</th>
              <th class="py-3.5 px-4">Categoría</th>
              <th class="py-3.5 px-4">Área Asignada</th>
              <th class="py-3.5 px-4">Existencia</th>
              <th class="py-3.5 px-4">Unidad</th>
              <th class="py-3.5 px-4">Stock Mín.</th>
              <th class="py-3.5 px-4">Stock Máx.</th>
              <th class="py-3.5 px-4 text-right">Estado de Stock</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-xs text-slate-700">
            <tr
              v-for="item in itemsFiltrados"
              :key="item.existencia_id"
              :class="[
                'transition-colors',
                item.stock_bajo ? 'bg-amber-50/40 hover:bg-amber-50/70' : 'hover:bg-slate-50/80'
              ]"
            >
              <td class="py-3.5 px-4 whitespace-nowrap">
                <span class="font-mono font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded text-[11px] border border-slate-200">
                  {{ item.activo_codigo }}
                </span>
              </td>
              <td class="py-3.5 px-4 font-semibold text-slate-900 max-w-xs truncate">
                {{ item.activo_nombre }}
              </td>
              <td class="py-3.5 px-4 text-slate-600">
                {{ item.categoria_nombre }}
              </td>
              <td class="py-3.5 px-4 text-slate-800 font-medium">
                {{ item.area_nombre }}
              </td>
              <td class="py-3.5 px-4">
                <span
                  :class="[
                    'text-sm font-extrabold',
                    item.stock_bajo ? 'text-amber-700' : 'text-slate-900'
                  ]"
                >
                  {{ item.cantidad }}
                </span>
              </td>
              <td class="py-3.5 px-4 capitalize text-slate-500">
                {{ item.unidad_medida }}
              </td>
              <td class="py-3.5 px-4 text-slate-500">
                {{ item.stock_minimo ?? '—' }}
              </td>
              <td class="py-3.5 px-4 text-slate-500">
                {{ item.stock_maximo ?? '—' }}
              </td>
              <td class="py-3.5 px-4 text-right whitespace-nowrap">
                <span
                  v-if="item.stock_bajo"
                  class="badge-status-warning"
                >
                  <i class="pi pi-exclamation-triangle text-[10px] mr-1 text-amber-700"></i>
                  Stock Bajo
                </span>
                <span
                  v-else
                  class="badge-status-activo"
                >
                  <span class="w-1.5 h-1.5 rounded-full mr-1.5 bg-emerald-500"></span>
                  Normal
                </span>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-else class="py-16 text-center text-slate-500">
          <i class="pi pi-inbox text-3xl text-slate-300 mb-2"></i>
          <p class="text-xs font-semibold text-slate-700">No se encontraron registros de inventario con los criterios seleccionados</p>
        </div>
      </div>

      <div class="px-4 py-3 bg-slate-50 border-t border-slate-200/80 flex items-center justify-between text-xs text-slate-500">
        <span>Total de registros reportados: {{ itemsFiltrados.length }}</span>
        <span class="font-medium">Fundación Simón I. Patiño</span>
      </div>
    </div>
  </div>
</template>
