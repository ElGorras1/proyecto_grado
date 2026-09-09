<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import GrafoTrazabilidad from '@/components/GrafoTrazabilidad.vue'
import type { ElementDefinition } from 'cytoscape'

interface CategoriaActivo {
  id: number
  nombre: string
}

interface Activo {
  id: number
  categoria_id: number
  categoria_nombre: string | null
  codigo: string
  nombre: string
  descripcion: string | null
  unidad_medida: string
  estado: string
  fecha_alta: string | null
  fecha_baja: string | null
}

const auth = useAuthStore()

const puedeEditar = computed(() => {
  return auth.rol === 'Administrador' || auth.rol === 'Operador'
})

const activos = ref<Activo[]>([])
const categorias = ref<CategoriaActivo[]>([])
const cargando = ref(false)
const error = ref('')
const mensajeExito = ref('')

// Filtros
const filtroCategoria = ref<number | ''>('')
const filtroEstado = ref('')
const filtroBusqueda = ref('')

// Modal Crear/Editar
const modalAbierto = ref(false)
const esEdicion = ref(false)
const activoEditandoId = ref<number | null>(null)
const formCategoriaId = ref<number | ''>('')
const formCodigo = ref('')
const formNombre = ref('')
const formDescripcion = ref('')
const formUnidadMedida = ref('unidad')
const formFechaAlta = ref('')
const guardando = ref(false)
const errorModal = ref('')

// Modal / Drawer de Trazabilidad
const modalTrazabilidadAbierto = ref(false)
const activoSeleccionadoTrazabilidad = ref<Activo | null>(null)
const elementosTrazabilidad = ref<ElementDefinition[]>([])

function abrirTrazabilidad(a: Activo) {
  activoSeleccionadoTrazabilidad.value = a
  // Generar grafo de custodia ilustrativo para el activo seleccionado
  elementosTrazabilidad.value = [
    { data: { id: 'alm_central', label: 'Almacén Central (Recepción)', tipo: 'almacen' } },
    { data: { id: 'cedoal', label: 'Centro CEDOAL (Custodia Técnica)', tipo: 'cedoal' } },
    { data: { id: 'area_destino', label: `${a.categoria_nombre ?? 'Área'} - Asignación`, tipo: 'galeria' } },
    { data: { id: 'e1', source: 'alm_central', target: 'cedoal', label: `Ingreso ${a.codigo}` } },
    { data: { id: 'e2', source: 'cedoal', target: 'area_destino', label: 'Transferencia Operativa' } },
  ]
  modalTrazabilidadAbierto.value = true
}

function cerrarTrazabilidad() {
  modalTrazabilidadAbierto.value = false
  activoSeleccionadoTrazabilidad.value = null
}

async function cargarDatos() {
  cargando.value = true
  error.value = ''
  try {
    const [resActivos, resCategorias] = await Promise.all([
      api.get('/activos'),
      api.get('/categorias'),
    ])
    activos.value = resActivos.data
    categorias.value = resCategorias.data
  } catch (err) {
    if (axios.isAxiosError(err)) {
      error.value = err.response?.data?.detail || 'Error al cargar los activos'
    } else {
      error.value = 'Error al cargar los activos'
    }
  } finally {
    cargando.value = false
  }
}

const activosFiltrados = computed(() => {
  return activos.value.filter((a) => {
    if (filtroCategoria.value && a.categoria_id !== Number(filtroCategoria.value)) return false
    if (filtroEstado.value && a.estado !== filtroEstado.value) return false
    if (filtroBusqueda.value.trim()) {
      const q = filtroBusqueda.value.toLowerCase()
      const matchCodigo = a.codigo.toLowerCase().includes(q)
      const matchNombre = a.nombre.toLowerCase().includes(q)
      if (!matchCodigo && !matchNombre) return false
    }
    return true
  })
})

function abrirModalCrear() {
  esEdicion.value = false
  activoEditandoId.value = null
  formCategoriaId.value = categorias.value.length > 0 ? categorias.value[0].id : ''
  formCodigo.value = ''
  formNombre.value = ''
  formDescripcion.value = ''
  formUnidadMedida.value = 'unidad'
  formFechaAlta.value = new Date().toISOString().split('T')[0]
  errorModal.value = ''
  modalAbierto.value = true
}

function abrirModalEditar(a: Activo) {
  esEdicion.value = true
  activoEditandoId.value = a.id
  formCategoriaId.value = a.categoria_id
  formCodigo.value = a.codigo
  formNombre.value = a.nombre
  formDescripcion.value = a.descripcion ?? ''
  formUnidadMedida.value = a.unidad_medida ?? 'unidad'
  formFechaAlta.value = a.fecha_alta ?? ''
  errorModal.value = ''
  modalAbierto.value = true
}

function cerrarModal() {
  modalAbierto.value = false
  activoEditandoId.value = null
}

async function guardarActivo() {
  if (!formCodigo.value.trim()) {
    errorModal.value = 'El código del activo es obligatorio.'
    return
  }
  if (!formNombre.value.trim()) {
    errorModal.value = 'El nombre del activo es obligatorio.'
    return
  }
  if (!formCategoriaId.value) {
    errorModal.value = 'Debe seleccionar una categoría.'
    return
  }

  guardando.value = true
  errorModal.value = ''
  try {
    const payload = {
      categoria_id: Number(formCategoriaId.value),
      codigo: formCodigo.value.trim(),
      nombre: formNombre.value.trim(),
      descripcion: formDescripcion.value.trim() || null,
      unidad_medida: formUnidadMedida.value.trim() || 'unidad',
      fecha_alta: formFechaAlta.value || null,
    }

    if (esEdicion.value && activoEditandoId.value !== null) {
      await api.put(`/activos/${activoEditandoId.value}`, payload)
      mensajeExito.value = 'Activo actualizado con éxito'
    } else {
      await api.post('/activos', payload)
      mensajeExito.value = 'Activo creado con éxito'
    }

    cerrarModal()
    setTimeout(() => {
      mensajeExito.value = ''
    }, 4000)
    await cargarDatos()
  } catch (err) {
    if (axios.isAxiosError(err)) {
      errorModal.value = err.response?.data?.detail || 'Error al guardar el activo'
    } else {
      errorModal.value = 'Error al guardar el activo'
    }
  } finally {
    guardando.value = false
  }
}

async function alternarEstado(a: Activo) {
  error.value = ''
  mensajeExito.value = ''
  try {
    if (a.estado === 'activo') {
      await api.patch(`/activos/${a.id}/desactivar`)
      mensajeExito.value = `Activo "${a.nombre}" desactivado (baja lógica)`
    } else {
      await api.patch(`/activos/${a.id}/reactivar`)
      mensajeExito.value = `Activo "${a.nombre}" reactivado`
    }
    setTimeout(() => {
      mensajeExito.value = ''
    }, 4000)
    await cargarDatos()
  } catch (err) {
    if (axios.isAxiosError(err)) {
      error.value = err.response?.data?.detail || 'Error al cambiar estado del activo'
    } else {
      error.value = 'Error al cambiar estado del activo'
    }
  }
}

onMounted(cargarDatos)
</script>

<template>
  <div class="space-y-6 max-w-7xl mx-auto font-sans">
    <!-- ENCABEZADO DE LA VISTA -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
      <div>
        <h1 class="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
          <i class="pi pi-box text-blue-600"></i>
          <span>Gestión de Activos Operativos</span>
        </h1>
        <p class="text-sm font-medium text-slate-500 mt-1">
          Registro centralizado de bienes patrimoniales, muebles y equipamiento institucional
        </p>
      </div>

      <button
        v-if="puedeEditar"
        class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs hover:shadow transition-all cursor-pointer self-start sm:self-auto"
        @click="abrirModalCrear"
      >
        <i class="pi pi-plus text-xs"></i>
        <span>Registrar Nuevo Activo</span>
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

    <!-- BARRA DE FILTROS Y BÚSQUEDA GLOBAL -->
    <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-4">
      <!-- Input de Búsqueda con Lupa -->
      <div class="relative flex-1 min-w-[240px] max-w-md">
        <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
          <i class="pi pi-search text-xs"></i>
        </span>
        <input
          v-model="filtroBusqueda"
          type="text"
          placeholder="Buscar por código o denominación de activo..."
          class="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
        />
      </div>

      <!-- Filtros desplegables -->
      <div class="flex flex-wrap items-center gap-3">
        <!-- Selector Categoría -->
        <div class="flex items-center gap-1.5">
          <label class="text-xs font-semibold text-slate-500">Categoría:</label>
          <select
            v-model="filtroCategoria"
            class="px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
          >
            <option value="">Todas las categorías</option>
            <option v-for="c in categorias" :key="c.id" :value="c.id">
              {{ c.nombre }}
            </option>
          </select>
        </div>

        <!-- Selector Estado -->
        <div class="flex items-center gap-1.5">
          <label class="text-xs font-semibold text-slate-500">Estado:</label>
          <select
            v-model="filtroEstado"
            class="px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
          >
            <option value="">Todos los estados</option>
            <option value="activo">Activo</option>
            <option value="baja">Baja Lógica</option>
          </select>
        </div>
      </div>
    </div>

    <!-- TABLA DE DATOS (DataTable Estilizado) -->
    <div class="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      <!-- Indicador de Carga -->
      <div v-if="cargando" class="py-16 text-center text-slate-500">
        <i class="pi pi-spin pi-spinner text-2xl text-blue-600 mb-2"></i>
        <p class="text-xs font-medium">Cargando inventario de activos...</p>
      </div>

      <!-- Tabla Principal -->
      <div v-else class="overflow-x-auto">
        <table v-if="activosFiltrados.length > 0" class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-50 text-slate-700 font-semibold uppercase text-xs tracking-wider border-b border-slate-200">
              <th class="py-3.5 px-4">Código</th>
              <th class="py-3.5 px-4">Denominación del Activo</th>
              <th class="py-3.5 px-4">Categoría</th>
              <th class="py-3.5 px-4">Unidad</th>
              <th class="py-3.5 px-4">Alta</th>
              <th class="py-3.5 px-4">Estado</th>
              <th class="py-3.5 px-4 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-xs text-slate-700">
            <tr
              v-for="a in activosFiltrados"
              :key="a.id"
              class="hover:bg-slate-50/80 transition-colors"
            >
              <td class="py-3.5 px-4 whitespace-nowrap">
                <span class="font-mono font-bold text-slate-900 bg-slate-100 px-2 py-1 rounded text-[11px] border border-slate-200">
                  {{ a.codigo }}
                </span>
              </td>
              <td class="py-3.5 px-4 font-semibold text-slate-900 max-w-xs">
                <div class="truncate" :title="a.nombre">{{ a.nombre }}</div>
                <div v-if="a.descripcion" class="text-[11px] text-slate-400 font-normal truncate mt-0.5">
                  {{ a.descripcion }}
                </div>
              </td>
              <td class="py-3.5 px-4 whitespace-nowrap">
                <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700">
                  {{ a.categoria_nombre ?? '—' }}
                </span>
              </td>
              <td class="py-3.5 px-4 capitalize whitespace-nowrap">
                {{ a.unidad_medida }}
              </td>
              <td class="py-3.5 px-4 text-slate-500 whitespace-nowrap">
                {{ a.fecha_alta ?? '—' }}
              </td>
              <td class="py-3.5 px-4 whitespace-nowrap">
                <span :class="a.estado === 'activo' ? 'badge-status-activo' : 'badge-status-baja'">
                  <span
                    :class="[
                      'w-1.5 h-1.5 rounded-full mr-1.5',
                      a.estado === 'activo' ? 'bg-emerald-500' : 'bg-slate-400'
                    ]"
                  ></span>
                  {{ a.estado === 'activo' ? 'Activo' : 'Baja' }}
                </span>
              </td>
              <td class="py-3.5 px-4 text-right whitespace-nowrap">
                <div class="inline-flex items-center gap-1">
                  <!-- Botón Ver Trazabilidad -->
                  <button
                    type="button"
                    class="p-1.5 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors cursor-pointer"
                    title="Ver Grafo de Trazabilidad"
                    @click="abrirTrazabilidad(a)"
                  >
                    <i class="pi pi-sitemap text-xs"></i>
                  </button>

                  <!-- Botón Editar -->
                  <button
                    v-if="puedeEditar"
                    type="button"
                    class="p-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                    title="Editar ficha"
                    @click="abrirModalEditar(a)"
                  >
                    <i class="pi pi-pencil text-xs"></i>
                  </button>

                  <!-- Botón Baja / Reactivación -->
                  <button
                    v-if="puedeEditar"
                    type="button"
                    :class="[
                      'p-1.5 rounded-lg transition-colors cursor-pointer',
                      a.estado === 'activo'
                        ? 'text-red-600 hover:text-red-800 hover:bg-red-50'
                        : 'text-emerald-600 hover:text-emerald-800 hover:bg-emerald-50'
                    ]"
                    :title="a.estado === 'activo' ? 'Dar de Baja Lógica' : 'Reactivar Activo'"
                    @click="alternarEstado(a)"
                  >
                    <i :class="['pi text-xs', a.estado === 'activo' ? 'pi-ban' : 'pi-replay']"></i>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Estado Vacío -->
        <div v-else class="py-16 text-center text-slate-500">
          <i class="pi pi-inbox text-3xl text-slate-300 mb-2"></i>
          <p class="text-xs font-semibold text-slate-700">No se encontraron activos registrados</p>
          <p class="text-[11px] text-slate-400 mt-0.5">Intenta ajustar los filtros de búsqueda o categoría.</p>
        </div>
      </div>

      <!-- Pie de Tabla con Resumen -->
      <div class="px-4 py-3 bg-slate-50 border-t border-slate-200/80 flex items-center justify-between text-xs text-slate-500">
        <span>Mostrando {{ activosFiltrados.length }} de {{ activos.length }} activos registrados</span>
        <span class="font-medium">Fundación Simón I. Patiño</span>
      </div>
    </div>

    <!-- MODAL: CREAR / EDITAR ACTIVO -->
    <div
      v-if="modalAbierto"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto"
    >
      <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden animate-in fade-in">
        <!-- Cabecera del Modal -->
        <div class="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold">
              <i :class="['pi', esEdicion ? 'pi-pencil' : 'pi-plus']"></i>
            </div>
            <div>
              <h2 class="text-sm font-bold text-white">
                {{ esEdicion ? 'Editar Ficha de Activo' : 'Registrar Nuevo Activo Institucional' }}
              </h2>
              <p class="text-[11px] text-slate-400">
                Información técnica y catalogación patrimonial
              </p>
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

        <!-- Formulario -->
        <form class="p-6 space-y-4" @submit.prevent="guardarActivo">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">
                Categoría *
              </label>
              <select
                v-model="formCategoriaId"
                required
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                <option disabled value="">Seleccione una categoría</option>
                <option v-for="c in categorias" :key="c.id" :value="c.id">
                  {{ c.nombre }}
                </option>
              </select>
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">
                Código de Activo *
              </label>
              <input
                v-model="formCodigo"
                type="text"
                required
                placeholder="Ej: ACT-COL-001"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono font-bold text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              Nombre / Denominación del Activo *
            </label>
            <input
              v-model="formNombre"
              type="text"
              required
              placeholder="Ej: Servidor de Base de Datos Dell R640"
              class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              Descripción y Atributos (opcional)
            </label>
            <textarea
              v-model="formDescripcion"
              rows="3"
              placeholder="Especificaciones, marca, serie, valor o estado físico..."
              class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            ></textarea>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">
                Unidad de Medida
              </label>
              <input
                v-model="formUnidadMedida"
                type="text"
                placeholder="unidad, pieza, lote, etc."
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">
                Fecha de Alta
              </label>
              <input
                v-model="formFechaAlta"
                type="date"
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

          <!-- Acciones del Modal -->
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
              <span>{{ guardando ? 'Guardando...' : (esEdicion ? 'Actualizar Ficha' : 'Crear Activo') }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: VISOR DE TRAZABILIDAD DEL ACTIVO -->
    <div
      v-if="modalTrazabilidadAbierto"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 backdrop-blur-xs p-4 overflow-y-auto"
    >
      <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-3xl overflow-hidden animate-in fade-in">
        <!-- Cabecera -->
        <div class="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold">
              <i class="pi pi-sitemap"></i>
            </div>
            <div>
              <h2 class="text-sm font-bold text-white flex items-center gap-2">
                <span>Trazabilidad de Custodia · {{ activoSeleccionadoTrazabilidad?.codigo }}</span>
              </h2>
              <p class="text-[11px] text-slate-400">
                {{ activoSeleccionadoTrazabilidad?.nombre }}
              </p>
            </div>
          </div>
          <button
            type="button"
            class="text-slate-400 hover:text-white transition-colors cursor-pointer"
            @click="cerrarTrazabilidad"
          >
            <i class="pi pi-times text-sm"></i>
          </button>
        </div>

        <!-- Cuerpo del Grafo -->
        <div class="p-6 space-y-4">
          <GrafoTrazabilidad :elementos="elementosTrazabilidad" altura="380px" />

          <div class="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
            <span>Red de transferencias calculada por el motor de Trazabilidad</span>
            <button
              type="button"
              class="px-4 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg text-xs transition-colors cursor-pointer"
              @click="cerrarTrazabilidad"
            >
              Cerrar Vista
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
