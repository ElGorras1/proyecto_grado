<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import api from '@/services/api'

interface Area {
  id: number
  nombre: string
  codigo: string | null
  descripcion: string | null
  estado: string
}

const areas = ref<Area[]>([])
const cargando = ref(false)
const error = ref('')
const mensajeExito = ref('')

// Filtros
const filtroEstado = ref('')

// Modal Crear/Editar Área
const modalAbierto = ref(false)
const esEdicion = ref(false)
const areaEditandoId = ref<number | null>(null)
const formNombre = ref('')
const formCodigo = ref('')
const formDescripcion = ref('')
const guardando = ref(false)
const errorModal = ref('')

async function cargarAreas() {
  cargando.value = true
  error.value = ''
  try {
    const { data } = await api.get('/areas')
    areas.value = data
  } catch (err) {
    if (axios.isAxiosError(err)) {
      error.value = err.response?.data?.detail || 'Error al cargar las áreas'
    } else {
      error.value = 'Error al cargar las áreas'
    }
  } finally {
    cargando.value = false
  }
}

const areasFiltradas = computed(() => {
  return areas.value.filter((a) => {
    if (filtroEstado.value && a.estado !== filtroEstado.value) return false
    return true
  })
})

function abrirModalCrear() {
  esEdicion.value = false
  areaEditandoId.value = null
  formNombre.value = ''
  formCodigo.value = ''
  formDescripcion.value = ''
  errorModal.value = ''
  modalAbierto.value = true
}

function abrirModalEditar(area: Area) {
  esEdicion.value = true
  areaEditandoId.value = area.id
  formNombre.value = area.nombre
  formCodigo.value = area.codigo ?? ''
  formDescripcion.value = area.descripcion ?? ''
  errorModal.value = ''
  modalAbierto.value = true
}

function cerrarModal() {
  modalAbierto.value = false
  areaEditandoId.value = null
}

async function guardarArea() {
  if (!formNombre.value.trim()) {
    errorModal.value = 'El nombre del área es obligatorio.'
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

    if (esEdicion.value && areaEditandoId.value !== null) {
      await api.put(`/areas/${areaEditandoId.value}`, payload)
      mensajeExito.value = 'Área actualizada con éxito'
    } else {
      await api.post('/areas', payload)
      mensajeExito.value = 'Área creada con éxito'
    }

    cerrarModal()
    setTimeout(() => {
      mensajeExito.value = ''
    }, 4000)
    await cargarAreas()
  } catch (err) {
    if (axios.isAxiosError(err)) {
      errorModal.value = err.response?.data?.detail || 'Error al guardar el área'
    } else {
      errorModal.value = 'Error al guardar el área'
    }
  } finally {
    guardando.value = false
  }
}

async function alternarEstado(area: Area) {
  error.value = ''
  mensajeExito.value = ''
  try {
    if (area.estado === 'activo') {
      await api.patch(`/areas/${area.id}/desactivar`)
      mensajeExito.value = `Área "${area.nombre}" desactivada (baja lógica)`
    } else {
      await api.patch(`/areas/${area.id}/reactivar`)
      mensajeExito.value = `Área "${area.nombre}" reactivada`
    }
    setTimeout(() => {
      mensajeExito.value = ''
    }, 4000)
    await cargarAreas()
  } catch (err) {
    if (axios.isAxiosError(err)) {
      error.value = err.response?.data?.detail || 'Error al cambiar estado del área'
    } else {
      error.value = 'Error al cambiar estado del área'
    }
  }
}

onMounted(cargarAreas)
</script>

<template>
  <div class="areas-view">
    <header class="header">
      <div>
        <div class="breadcrumb">
          <router-link to="/">Panel principal</router-link> &gt; Gestión de áreas
        </div>
        <h1>Gestión de Áreas</h1>
      </div>
      <button class="btn btn-primary" @click="abrirModalCrear">
        + Nueva área
      </button>
    </header>

    <p v-if="error" class="alert alert-error">{{ error }}</p>
    <p v-if="mensajeExito" class="alert alert-success">{{ mensajeExito }}</p>

    <!-- Filtros -->
    <div class="filtros">
      <label>
        Filtrar por estado:
        <select v-model="filtroEstado">
          <option value="">Todos los estados</option>
          <option value="activo">Activo</option>
          <option value="baja">Baja</option>
        </select>
      </label>
    </div>

    <!-- Tabla -->
    <div v-if="cargando" class="cargando">Cargando áreas...</div>
    <div v-else class="table-container">
      <table v-if="areasFiltradas.length > 0">
        <thead>
          <tr>
            <th>ID</th>
            <th>Código</th>
            <th>Nombre</th>
            <th>Descripción</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in areasFiltradas" :key="a.id">
            <td>{{ a.id }}</td>
            <td><code>{{ a.codigo ?? '—' }}</code></td>
            <td class="bold">{{ a.nombre }}</td>
            <td>{{ a.descripcion ?? '—' }}</td>
            <td>
              <span :class="['badge', a.estado === 'activo' ? 'badge-activo' : 'badge-baja']">
                {{ a.estado === 'activo' ? 'Activo' : 'Baja' }}
              </span>
            </td>
            <td class="acciones">
              <button class="btn btn-sm btn-outline" @click="abrirModalEditar(a)">
                Editar
              </button>
              <button
                :class="['btn btn-sm', a.estado === 'activo' ? 'btn-danger' : 'btn-success']"
                @click="alternarEstado(a)"
              >
                {{ a.estado === 'activo' ? 'Desactivar' : 'Reactivar' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="vacio">No se encontraron áreas con los criterios seleccionados.</p>
    </div>

    <!-- Modal Crear / Editar -->
    <div v-if="modalAbierto" class="modal-backdrop">
      <div class="modal">
        <h2>{{ esEdicion ? 'Editar área' : 'Crear nueva área' }}</h2>
        <form @submit.prevent="guardarArea">
          <label>
            Nombre del área *
            <input
              v-model="formNombre"
              type="text"
              required
              placeholder="Ej: Logística y Transporte"
            />
          </label>

          <label>
            Código (opcional)
            <input
              v-model="formCodigo"
              type="text"
              placeholder="Ej: LOG-01"
            />
          </label>

          <label>
            Descripción (opcional)
            <textarea
              v-model="formDescripcion"
              rows="3"
              placeholder="Descripción o propósito del área..."
            ></textarea>
          </label>

          <p v-if="errorModal" class="alert alert-error">{{ errorModal }}</p>

          <div class="modal-actions">
            <button type="button" class="btn btn-outline" @click="cerrarModal">
              Cancelar
            </button>
            <button type="submit" class="btn btn-primary" :disabled="guardando">
              {{ guardando ? 'Guardando...' : (esEdicion ? 'Actualizar área' : 'Crear área') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.areas-view {
  padding: 2rem;
  font-family: system-ui, sans-serif;
  max-width: 1100px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.breadcrumb {
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 0.25rem;
}

.breadcrumb a {
  color: #0969da;
  text-decoration: none;
}

.breadcrumb a:hover {
  text-decoration: underline;
}

h1 {
  margin: 0;
  font-size: 1.6rem;
}

.alert {
  padding: 0.75rem 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.alert-error {
  background: #ffebe9;
  color: #cf222e;
  border: 1px solid #ff8182;
}

.alert-success {
  background: #dafbe1;
  color: #1a7f37;
  border: 1px solid #4ac26b;
}

.filtros {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  background: #f6f8fa;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #d0d7de;
}

.filtros label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: #444;
}

.filtros select {
  padding: 0.4rem 0.6rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  background: white;
  min-width: 160px;
}

.table-container {
  overflow-x: auto;
  border: 1px solid #e1e4e8;
  border-radius: 8px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e1e4e8;
  text-align: left;
  font-size: 0.9rem;
}

th {
  background: #f6f8fa;
  font-weight: 600;
}

.bold {
  font-weight: 600;
}

code {
  background: #f1f3f5;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-size: 0.85rem;
}

.badge {
  display: inline-block;
  padding: 0.2rem 0.55rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-activo {
  background: #dafbe1;
  color: #1a7f37;
  border: 1px solid #4ac26b;
}

.badge-baja {
  background: #f6f8fa;
  color: #656d76;
  border: 1px solid #d0d7de;
}

.acciones {
  display: flex;
  gap: 0.5rem;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  border: 1px solid transparent;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.85rem;
  transition: background 0.15s;
}

.btn-sm {
  padding: 0.35rem 0.65rem;
  font-size: 0.8rem;
}

.btn-primary {
  background: #1f6feb;
  color: white;
}

.btn-primary:hover {
  background: #1158c7;
}

.btn-danger {
  background: #ffebe9;
  color: #cf222e;
  border: 1px solid #ff8182;
}

.btn-danger:hover {
  background: #ff8182;
  color: white;
}

.btn-success {
  background: #dafbe1;
  color: #1a7f37;
  border: 1px solid #4ac26b;
}

.btn-success:hover {
  background: #4ac26b;
  color: white;
}

.btn-outline {
  background: white;
  color: #24292f;
  border: 1px solid #d0d7de;
}

.btn-outline:hover {
  background: #f3f4f6;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  padding: 1.75rem;
  border-radius: 10px;
  width: 100%;
  max-width: 460px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.modal h2 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.3rem;
}

.modal form {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.modal label {
  display: flex;
  flex-direction: column;
  font-size: 0.85rem;
  font-weight: 600;
  gap: 0.3rem;
  color: #333;
}

.modal input,
.modal textarea {
  padding: 0.5rem 0.7rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 0.9rem;
  font-family: inherit;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.75rem;
}

.cargando, .vacio {
  padding: 2rem;
  text-align: center;
  color: #666;
}
</style>
