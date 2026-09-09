<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

interface CategoriaActivo {
  id: number
  nombre: string
  codigo: string | null
  descripcion: string | null
  estado: string
}

const auth = useAuthStore()

const categorias = ref<CategoriaActivo[]>([])
const cargando = ref(false)
const error = ref('')
const mensajeExito = ref('')

// Filtros
const filtroEstado = ref('')
const filtroBusqueda = ref('')

// Modal Crear/Editar
const modalAbierto = ref(false)
const esEdicion = ref(false)
const categoriaEditandoId = ref<number | null>(null)
const formNombre = ref('')
const formCodigo = ref('')
const formDescripcion = ref('')
const guardando = ref(false)
const errorModal = ref('')

async function cargarCategorias() {
  cargando.value = true
  error.value = ''
  try {
    const { data } = await api.get('/categorias')
    categorias.value = data
  } catch (err) {
    if (axios.isAxiosError(err)) {
      error.value = err.response?.data?.detail || 'Error al cargar las categorías'
    } else {
      error.value = 'Error al cargar las categorías'
    }
  } finally {
    cargando.value = false
  }
}

const categoriasFiltradas = computed(() => {
  return categorias.value.filter((c) => {
    if (filtroEstado.value && c.estado !== filtroEstado.value) return false
    if (filtroBusqueda.value.trim()) {
      const q = filtroBusqueda.value.toLowerCase()
      const matchNombre = c.nombre.toLowerCase().includes(q)
      const matchCodigo = (c.codigo ?? '').toLowerCase().includes(q)
      if (!matchNombre && !matchCodigo) return false
    }
    return true
  })
})

function abrirModalCrear() {
  esEdicion.value = false
  categoriaEditandoId.value = null
  formNombre.value = ''
  formCodigo.value = ''
  formDescripcion.value = ''
  errorModal.value = ''
  modalAbierto.value = true
}

function abrirModalEditar(cat: CategoriaActivo) {
  esEdicion.value = true
  categoriaEditandoId.value = cat.id
  formNombre.value = cat.nombre
  formCodigo.value = cat.codigo ?? ''
  formDescripcion.value = cat.descripcion ?? ''
  errorModal.value = ''
  modalAbierto.value = true
}

function cerrarModal() {
  modalAbierto.value = false
  categoriaEditandoId.value = null
}

async function guardarCategoria() {
  if (!formNombre.value.trim()) {
    errorModal.value = 'El nombre de la categoría es obligatorio.'
    return
  }

  guardando.value = true
  errorModal.value = ''
  try {
    const payload = {
      nombre: formNombre.value.trim(),
      codigo: formCodigo.value.trim() || null,
      descripcion: formDescripcion.value.trim() || null,
    }

    if (esEdicion.value && categoriaEditandoId.value !== null) {
      await api.put(`/categorias/${categoriaEditandoId.value}`, payload)
      mensajeExito.value = 'Categoría actualizada con éxito'
    } else {
      await api.post('/categorias', payload)
      mensajeExito.value = 'Categoría creada con éxito'
    }

    cerrarModal()
    setTimeout(() => {
      mensajeExito.value = ''
    }, 4000)
    await cargarCategorias()
  } catch (err) {
    if (axios.isAxiosError(err)) {
      errorModal.value = err.response?.data?.detail || 'Error al guardar la categoría'
    } else {
      errorModal.value = 'Error al guardar la categoría'
    }
  } finally {
    guardando.value = false
  }
}

async function alternarEstado(cat: CategoriaActivo) {
  error.value = ''
  mensajeExito.value = ''
  try {
    if (cat.estado === 'activo') {
      await api.patch(`/categorias/${cat.id}/desactivar`)
      mensajeExito.value = `Categoría "${cat.nombre}" desactivada (baja lógica)`
    } else {
      await api.patch(`/categorias/${cat.id}/reactivar`)
      mensajeExito.value = `Categoría "${cat.nombre}" reactivada`
    }
    setTimeout(() => {
      mensajeExito.value = ''
    }, 4000)
    await cargarCategorias()
  } catch (err) {
    if (axios.isAxiosError(err)) {
      error.value = err.response?.data?.detail || 'Error al cambiar estado de la categoría'
    } else {
      error.value = 'Error al cambiar estado de la categoría'
    }
  }
}

onMounted(cargarCategorias)
</script>

<template>
  <div class="space-y-6 max-w-7xl mx-auto font-sans">
    <!-- ENCABEZADO -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
      <div>
        <h1 class="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
          <i class="pi pi-tags text-blue-600"></i>
          <span>Categorías de Activos</span>
        </h1>
        <p class="text-sm font-medium text-slate-500 mt-1">
          Estructura de clasificación patrimonial y operativa de la Fundación
        </p>
      </div>

      <button
        v-if="auth.rol === 'Administrador'"
        class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs hover:shadow transition-all cursor-pointer self-start sm:self-auto"
        @click="abrirModalCrear"
      >
        <i class="pi pi-plus text-xs"></i>
        <span>Nueva Categoría</span>
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

    <!-- FILTROS Y BÚSQUEDA -->
    <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-4">
      <div class="relative flex-1 min-w-[240px] max-w-md">
        <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
          <i class="pi pi-search text-xs"></i>
        </span>
        <input
          v-model="filtroBusqueda"
          type="text"
          placeholder="Buscar categoría por nombre o código..."
          class="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
        />
      </div>

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

    <!-- TABLA DE CATEGORÍAS -->
    <div class="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      <div v-if="cargando" class="py-16 text-center text-slate-500">
        <i class="pi pi-spin pi-spinner text-2xl text-blue-600 mb-2"></i>
        <p class="text-xs font-medium">Cargando categorías...</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table v-if="categoriasFiltradas.length > 0" class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-50 text-slate-700 font-semibold uppercase text-xs tracking-wider border-b border-slate-200">
              <th class="py-3.5 px-4">ID</th>
              <th class="py-3.5 px-4">Código</th>
              <th class="py-3.5 px-4">Nombre de la Categoría</th>
              <th class="py-3.5 px-4">Descripción</th>
              <th class="py-3.5 px-4">Estado</th>
              <th v-if="auth.rol === 'Administrador'" class="py-3.5 px-4 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-xs text-slate-700">
            <tr
              v-for="c in categoriasFiltradas"
              :key="c.id"
              class="hover:bg-slate-50/80 transition-colors"
            >
              <td class="py-3.5 px-4 font-mono text-slate-400">#{{ c.id }}</td>
              <td class="py-3.5 px-4 whitespace-nowrap">
                <span class="font-mono font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded text-[11px] border border-slate-200">
                  {{ c.codigo ?? '—' }}
                </span>
              </td>
              <td class="py-3.5 px-4 font-semibold text-slate-900">
                {{ c.nombre }}
              </td>
              <td class="py-3.5 px-4 text-slate-500 max-w-sm truncate">
                {{ c.descripcion ?? 'Sin descripción adicional' }}
              </td>
              <td class="py-3.5 px-4">
                <span :class="c.estado === 'activo' ? 'badge-status-activo' : 'badge-status-baja'">
                  <span
                    :class="[
                      'w-1.5 h-1.5 rounded-full mr-1.5',
                      c.estado === 'activo' ? 'bg-emerald-500' : 'bg-slate-400'
                    ]"
                  ></span>
                  {{ c.estado === 'activo' ? 'Activo' : 'Baja' }}
                </span>
              </td>
              <td v-if="auth.rol === 'Administrador'" class="py-3.5 px-4 text-right whitespace-nowrap">
                <div class="inline-flex items-center gap-1">
                  <button
                    type="button"
                    class="p-1.5 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors cursor-pointer"
                    title="Editar categoría"
                    @click="abrirModalEditar(c)"
                  >
                    <i class="pi pi-pencil text-xs"></i>
                  </button>
                  <button
                    type="button"
                    :class="[
                      'p-1.5 rounded-lg transition-colors cursor-pointer',
                      c.estado === 'activo'
                        ? 'text-red-600 hover:text-red-800 hover:bg-red-50'
                        : 'text-emerald-600 hover:text-emerald-800 hover:bg-emerald-50'
                    ]"
                    :title="c.estado === 'activo' ? 'Desactivar Categoría' : 'Reactivar Categoría'"
                    @click="alternarEstado(c)"
                  >
                    <i :class="['pi text-xs', c.estado === 'activo' ? 'pi-ban' : 'pi-replay']"></i>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-else class="py-16 text-center text-slate-500">
          <i class="pi pi-inbox text-3xl text-slate-300 mb-2"></i>
          <p class="text-xs font-semibold text-slate-700">No se encontraron categorías</p>
        </div>
      </div>

      <div class="px-4 py-3 bg-slate-50 border-t border-slate-200/80 flex items-center justify-between text-xs text-slate-500">
        <span>Mostrando {{ categoriasFiltradas.length }} categorías</span>
        <span class="font-medium">Fundación Simón I. Patiño</span>
      </div>
    </div>

    <!-- MODAL CREAR / EDITAR CATEGORÍA -->
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
                {{ esEdicion ? 'Editar Categoría' : 'Crear Nueva Categoría' }}
              </h2>
              <p class="text-[11px] text-slate-400">Clasificación para el catálogo de activos</p>
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

        <form class="p-6 space-y-4" @submit.prevent="guardarCategoria">
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              Nombre de la Categoría *
            </label>
            <input
              v-model="formNombre"
              type="text"
              required
              placeholder="Ej: Obras de Arte y Esculturas"
              class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              Código / Prefijo (opcional)
            </label>
            <input
              v-model="formCodigo"
              type="text"
              placeholder="Ej: CAT-ART"
              class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              Descripción (opcional)
            </label>
            <textarea
              v-model="formDescripcion"
              rows="3"
              placeholder="Descripción del alcance de esta categoría..."
              class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            ></textarea>
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
              <span>{{ guardando ? 'Guardando...' : (esEdicion ? 'Actualizar Categoría' : 'Crear Categoría') }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
