<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

interface Area {
  id: number
  nombre: string
}

interface Activo {
  id: number
  codigo: string
  nombre: string
}

interface Existencia {
  id: number
  activo_id: number
  area_id: number
  activo_nombre: string | null
  activo_codigo: string | null
  area_nombre: string | null
  area_codigo: string | null
  cantidad: number
  stock_minimo: number | null
  stock_maximo: number | null
  estado: string
}

const auth = useAuthStore()

const puedeEditar = computed(() => {
  return auth.rol === 'Administrador' || auth.rol === 'Operador'
})

const existencias = ref<Existencia[]>([])
const activos = ref<Activo[]>([])
const areas = ref<Area[]>([])
const cargando = ref(false)
const error = ref('')
const mensajeExito = ref('')

// Filtros
const filtroArea = ref<number | ''>('')
const filtroEstado = ref('')
const filtroBusqueda = ref('')

// Modal Crear/Editar
const modalAbierto = ref(false)
const esEdicion = ref(false)
const existenciaEditandoId = ref<number | null>(null)
const formActivoId = ref<number | ''>('')
const formAreaId = ref<number | ''>('')
const formCantidad = ref<number>(0)
const formStockMinimo = ref<number | null>(null)
const formStockMaximo = ref<number | null>(null)
const guardando = ref(false)
const errorModal = ref('')

async function cargarDatos() {
  cargando.value = true
  error.value = ''
  try {
    const [resExistencias, resActivos, resAreas] = await Promise.all([
      api.get('/existencias'),
      api.get('/activos'),
      api.get('/areas'),
    ])
    existencias.value = resExistencias.data
    activos.value = resActivos.data
    areas.value = resAreas.data
  } catch (err) {
    if (axios.isAxiosError(err)) {
      error.value = err.response?.data?.detail || 'Error al cargar las existencias'
    } else {
      error.value = 'Error al cargar las existencias'
    }
  } finally {
    cargando.value = false
  }
}

const existenciasFiltradas = computed(() => {
  return existencias.value.filter((e) => {
    if (filtroArea.value && e.area_id !== Number(filtroArea.value)) return false
    if (filtroEstado.value && e.estado !== filtroEstado.value) return false
    if (filtroBusqueda.value.trim()) {
      const q = filtroBusqueda.value.toLowerCase()
      const matchActivo = (e.activo_nombre ?? '').toLowerCase().includes(q)
      const matchCodigo = (e.activo_codigo ?? '').toLowerCase().includes(q)
      const matchArea = (e.area_nombre ?? '').toLowerCase().includes(q)
      if (!matchActivo && !matchCodigo && !matchArea) return false
    }
    return true
  })
})

function abrirModalCrear() {
  esEdicion.value = false
  existenciaEditandoId.value = null
  formActivoId.value = activos.value.length > 0 ? activos.value[0].id : ''
  formAreaId.value = areas.value.length > 0 ? areas.value[0].id : ''
  formCantidad.value = 0
  formStockMinimo.value = null
  formStockMaximo.value = null
  errorModal.value = ''
  modalAbierto.value = true
}

function abrirModalEditar(e: Existencia) {
  esEdicion.value = true
  existenciaEditandoId.value = e.id
  formActivoId.value = e.activo_id
  formAreaId.value = e.area_id
  formCantidad.value = e.cantidad
  formStockMinimo.value = e.stock_minimo
  formStockMaximo.value = e.stock_maximo
  errorModal.value = ''
  modalAbierto.value = true
}

function cerrarModal() {
  modalAbierto.value = false
  existenciaEditandoId.value = null
}

async function guardarExistencia() {
  if (formCantidad.value < 0) {
    errorModal.value = 'La cantidad no puede ser negativa.'
    return
  }
  if (
    formStockMinimo.value !== null &&
    formStockMaximo.value !== null &&
    formStockMaximo.value < formStockMinimo.value
  ) {
    errorModal.value = 'El stock máximo debe ser mayor o igual al stock mínimo.'
    return
  }

  guardando.value = true
  errorModal.value = ''
  try {
    if (esEdicion.value && existenciaEditandoId.value !== null) {
      const payload = {
        cantidad: Number(formCantidad.value),
        stock_minimo: formStockMinimo.value !== null && formStockMinimo.value !== undefined ? Number(formStockMinimo.value) : null,
        stock_maximo: formStockMaximo.value !== null && formStockMaximo.value !== undefined ? Number(formStockMaximo.value) : null,
      }
      await api.put(`/existencias/${existenciaEditandoId.value}`, payload)
      mensajeExito.value = 'Existencia actualizada con éxito'
    } else {
      if (!formActivoId.value || !formAreaId.value) {
        errorModal.value = 'Debe seleccionar un activo y un área.'
        guardando.value = false
        return
      }
      const payload = {
        activo_id: Number(formActivoId.value),
        area_id: Number(formAreaId.value),
        cantidad: Number(formCantidad.value),
        stock_minimo: formStockMinimo.value !== null && formStockMinimo.value !== undefined ? Number(formStockMinimo.value) : null,
        stock_maximo: formStockMaximo.value !== null && formStockMaximo.value !== undefined ? Number(formStockMaximo.value) : null,
      }
      await api.post('/existencias', payload)
      mensajeExito.value = 'Existencia registrada con éxito'
    }

    cerrarModal()
    setTimeout(() => {
      mensajeExito.value = ''
    }, 4000)
    await cargarDatos()
  } catch (err) {
    if (axios.isAxiosError(err)) {
      errorModal.value = err.response?.data?.detail || 'Error al guardar la existencia'
    } else {
      errorModal.value = 'Error al guardar la existencia'
    }
  } finally {
    guardando.value = false
  }
}

async function alternarEstado(e: Existencia) {
  error.value = ''
  mensajeExito.value = ''
  try {
    if (e.estado === 'activo') {
      await api.patch(`/existencias/${e.id}/desactivar`)
      mensajeExito.value = 'Existencia desactivada (baja lógica)'
    } else {
      await api.patch(`/existencias/${e.id}/reactivar`)
      mensajeExito.value = 'Existencia reactivada'
    }
    setTimeout(() => {
      mensajeExito.value = ''
    }, 4000)
    await cargarDatos()
  } catch (err) {
    if (axios.isAxiosError(err)) {
      error.value = err.response?.data?.detail || 'Error al cambiar estado de la existencia'
    } else {
      error.value = 'Error al cambiar estado de la existencia'
    }
  }
}

onMounted(cargarDatos)
</script>

<template>
  <div class="space-y-6 max-w-7xl mx-auto font-sans">
    <!-- ENCABEZADO -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
      <div>
        <h1 class="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
          <i class="pi pi-database text-blue-600"></i>
          <span>Existencias de Activos por Área</span>
        </h1>
        <p class="text-sm font-medium text-slate-500 mt-1">
          Inventario físico, niveles de reposición y control de custodia por sede
        </p>
      </div>

      <button
        v-if="puedeEditar"
        class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs hover:shadow transition-all cursor-pointer self-start sm:self-auto"
        @click="abrirModalCrear"
      >
        <i class="pi pi-plus text-xs"></i>
        <span>Registrar Existencia</span>
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

    <div
      v-if="mensajeExito"
      class="p-4 rounded-xl bg-emerald-50 border border-emerald-200/80 text-xs font-medium text-emerald-800 flex items-center gap-3 animate-in fade-in"
    >
      <i class="pi pi-check-circle text-emerald-600 shrink-0 text-base"></i>
      <span>{{ mensajeExito }}</span>
    </div>

    <!-- BARRA DE FILTROS -->
    <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-4">
      <!-- Buscador -->
      <div class="relative flex-1 min-w-[240px] max-w-md">
        <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
          <i class="pi pi-search text-xs"></i>
        </span>
        <input
          v-model="filtroBusqueda"
          type="text"
          placeholder="Buscar por activo, código o área..."
          class="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
        />
      </div>

      <!-- Selectores -->
      <div class="flex flex-wrap items-center gap-3">
        <div class="flex items-center gap-1.5">
          <label class="text-xs font-semibold text-slate-500">Área / Sede:</label>
          <select
            v-model="filtroArea"
            class="px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
          >
            <option value="">Todas las áreas</option>
            <option v-for="ar in areas" :key="ar.id" :value="ar.id">
              {{ ar.nombre }}
            </option>
          </select>
        </div>

        <div class="flex items-center gap-1.5">
          <label class="text-xs font-semibold text-slate-500">Estado:</label>
          <select
            v-model="filtroEstado"
            class="px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
          >
            <option value="">Todos los estados</option>
            <option value="activo">Activo</option>
            <option value="baja">Baja</option>
          </select>
        </div>
      </div>
    </div>

    <!-- TABLA DE EXISTENCIAS -->
    <div class="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      <div v-if="cargando" class="py-16 text-center text-slate-500">
        <i class="pi pi-spin pi-spinner text-2xl text-blue-600 mb-2"></i>
        <p class="text-xs font-medium">Cargando existencias...</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table v-if="existenciasFiltradas.length > 0" class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-50 text-slate-700 font-semibold uppercase text-xs tracking-wider border-b border-slate-200">
              <th class="py-3.5 px-4">ID</th>
              <th class="py-3.5 px-4">Activo / Código</th>
              <th class="py-3.5 px-4">Área / Custodia</th>
              <th class="py-3.5 px-4">Stock Actual</th>
              <th class="py-3.5 px-4">Stock Mínimo</th>
              <th class="py-3.5 px-4">Stock Máximo</th>
              <th class="py-3.5 px-4">Estado</th>
              <th v-if="puedeEditar" class="py-3.5 px-4 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-xs text-slate-700">
            <tr
              v-for="e in existenciasFiltradas"
              :key="e.id"
              class="hover:bg-slate-50/80 transition-colors"
            >
              <td class="py-3.5 px-4 font-mono text-slate-400">#{{ e.id }}</td>
              <td class="py-3.5 px-4">
                <span class="font-bold text-slate-900 block">{{ e.activo_nombre ?? `Activo #${e.activo_id}` }}</span>
                <span v-if="e.activo_codigo" class="font-mono text-[11px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                  {{ e.activo_codigo }}
                </span>
              </td>
              <td class="py-3.5 px-4 font-medium text-slate-800">
                {{ e.area_nombre ?? `Área #${e.area_id}` }}
              </td>
              <td class="py-3.5 px-4">
                <span class="text-sm font-extrabold text-slate-900">{{ e.cantidad }}</span>
                <span
                  v-if="e.stock_minimo !== null && e.cantidad <= e.stock_minimo"
                  class="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800"
                >
                  ⚠️ Mínimo
                </span>
              </td>
              <td class="py-3.5 px-4 text-slate-500">
                {{ e.stock_minimo ?? '—' }}
              </td>
              <td class="py-3.5 px-4 text-slate-500">
                {{ e.stock_maximo ?? '—' }}
              </td>
              <td class="py-3.5 px-4">
                <span :class="e.estado === 'activo' ? 'badge-status-activo' : 'badge-status-baja'">
                  <span
                    :class="[
                      'w-1.5 h-1.5 rounded-full mr-1.5',
                      e.estado === 'activo' ? 'bg-emerald-500' : 'bg-slate-400'
                    ]"
                  ></span>
                  {{ e.estado === 'activo' ? 'Activo' : 'Baja' }}
                </span>
              </td>
              <td v-if="puedeEditar" class="py-3.5 px-4 text-right whitespace-nowrap">
                <div class="inline-flex items-center gap-1">
                  <button
                    type="button"
                    class="p-1.5 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors cursor-pointer"
                    title="Ajustar Stock y Umbrales"
                    @click="abrirModalEditar(e)"
                  >
                    <i class="pi pi-pencil text-xs"></i>
                  </button>
                  <button
                    type="button"
                    :class="[
                      'p-1.5 rounded-lg transition-colors cursor-pointer',
                      e.estado === 'activo'
                        ? 'text-red-600 hover:text-red-800 hover:bg-red-50'
                        : 'text-emerald-600 hover:text-emerald-800 hover:bg-emerald-50'
                    ]"
                    :title="e.estado === 'activo' ? 'Desactivar Existencia' : 'Reactivar Existencia'"
                    @click="alternarEstado(e)"
                  >
                    <i :class="['pi text-xs', e.estado === 'activo' ? 'pi-ban' : 'pi-replay']"></i>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-else class="py-16 text-center text-slate-500">
          <i class="pi pi-inbox text-3xl text-slate-300 mb-2"></i>
          <p class="text-xs font-semibold text-slate-700">No hay existencias registradas con estos filtros</p>
        </div>
      </div>

      <div class="px-4 py-3 bg-slate-50 border-t border-slate-200/80 flex items-center justify-between text-xs text-slate-500">
        <span>Mostrando {{ existenciasFiltradas.length }} registros de existencia</span>
        <span class="font-medium">Fundación Simón I. Patiño</span>
      </div>
    </div>

    <!-- MODAL CREAR / EDITAR -->
    <div
      v-if="modalAbierto"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto"
    >
      <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-md overflow-hidden animate-in fade-in">
        <div class="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold">
              <i :class="['pi', esEdicion ? 'pi-pencil' : 'pi-plus']"></i>
            </div>
            <div>
              <h2 class="text-sm font-bold text-white">
                {{ esEdicion ? 'Ajustar Stock de Existencia' : 'Registrar Existencia en Área' }}
              </h2>
              <p class="text-[11px] text-slate-400">Control de inventario y cantidades físicas</p>
            </div>
          </div>
          <button
            type="button"
            class="text-slate-400 hover:text-white transition-colors cursor-pointer"
            @click="cerrarModal"
          >
            <i class="pi pi-times text-sm"></i>
          </button>
        </div>

        <form class="p-6 space-y-4" @submit.prevent="guardarExistencia">
          <div v-if="!esEdicion" class="space-y-4">
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">
                Activo a Registrar *
              </label>
              <select
                v-model="formActivoId"
                required
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                <option disabled value="">Seleccione un activo</option>
                <option v-for="a in activos" :key="a.id" :value="a.id">
                  {{ a.codigo }} - {{ a.nombre }}
                </option>
              </select>
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">
                Área de Almacenamiento *
              </label>
              <select
                v-model="formAreaId"
                required
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                <option disabled value="">Seleccione un área</option>
                <option v-for="ar in areas" :key="ar.id" :value="ar.id">
                  {{ ar.nombre }}
                </option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              Cantidad Física en Custodia *
            </label>
            <input
              v-model.number="formCantidad"
              type="number"
              min="0"
              step="any"
              required
              class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-bold text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">
                Stock Mínimo
              </label>
              <input
                v-model.number="formStockMinimo"
                type="number"
                min="0"
                step="any"
                placeholder="Ej: 5"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">
                Stock Máximo
              </label>
              <input
                v-model.number="formStockMaximo"
                type="number"
                min="0"
                step="any"
                placeholder="Ej: 50"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
          </div>

          <div
            v-if="errorModal"
            class="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700 flex items-center gap-2"
          >
            <i class="pi pi-exclamation-circle text-red-600"></i>
            <span>{{ errorModal }}</span>
          </div>

          <div class="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              class="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors cursor-pointer"
              @click="cerrarModal"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="guardando"
              class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-xs hover:shadow transition-all disabled:opacity-60 flex items-center gap-2 cursor-pointer"
            >
              <i v-if="guardando" class="pi pi-spin pi-spinner text-xs"></i>
              <span>{{ guardando ? 'Guardando...' : (esEdicion ? 'Actualizar Stock' : 'Registrar') }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
