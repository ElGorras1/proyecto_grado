<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import api from '@/services/api'

interface Usuario {
  id: number
  nombre: string
  email: string
  rol: string
  area_id: number | null
  estado: string
  last_login_at: string | null
}

interface Rol {
  id: number
  nombre: string
  descripcion?: string | null
}

const usuarios = ref<Usuario[]>([])
const roles = ref<Rol[]>([])
const cargando = ref(false)
const error = ref('')
const mensajeExito = ref('')

// Filtros
const filtroRol = ref('')
const filtroEstado = ref('')

// Modal Nuevo Usuario
const modalCrearAbierto = ref(false)
const nuevoNombre = ref('')
const nuevoEmail = ref('')
const nuevoPassword = ref('')
const nuevoRolId = ref<number | ''>('')
const guardandoUsuario = ref(false)
const errorCrear = ref('')

// Modal Resetear Contraseña
const modalResetAbierto = ref(false)
const usuarioSeleccionado = ref<Usuario | null>(null)
const nuevoPasswordReset = ref('')
const reseteandoPassword = ref(false)
const errorReset = ref('')

async function cargarDatos() {
  cargando.value = true
  error.value = ''
  try {
    const [respUsuarios, respRoles] = await Promise.all([
      api.get('/usuarios'),
      api.get('/usuarios/roles'),
    ])
    usuarios.value = respUsuarios.data
    roles.value = respRoles.data
  } catch (err) {
    if (axios.isAxiosError(err)) {
      error.value = err.response?.data?.detail || 'Error al cargar los usuarios'
    } else {
      error.value = 'Error de conexión con el servidor'
    }
  } finally {
    cargando.value = false
  }
}

const usuariosFiltrados = computed(() => {
  return usuarios.value.filter((u) => {
    if (filtroRol.value && u.rol !== filtroRol.value) return false
    if (filtroEstado.value && u.estado !== filtroEstado.value) return false
    return true
  })
})

function abrirModalCrear() {
  nuevoNombre.value = ''
  nuevoEmail.value = ''
  nuevoPassword.value = ''
  nuevoRolId.value = roles.value.length > 0 ? roles.value[0].id : ''
  errorCrear.value = ''
  modalCrearAbierto.value = true
}

function cerrarModalCrear() {
  modalCrearAbierto.value = false
}

async function crearUsuario() {
  if (!nuevoNombre.value || !nuevoEmail.value || !nuevoPassword.value || !nuevoRolId.value) {
    errorCrear.value = 'Todos los campos obligatorios deben completarse.'
    return
  }
  if (nuevoPassword.value.length < 8) {
    errorCrear.value = 'La contraseña debe tener al menos 8 caracteres.'
    return
  }

  guardandoUsuario.value = true
  errorCrear.value = ''
  try {
    const payload = {
      nombre: nuevoNombre.value.trim(),
      email: nuevoEmail.value.trim(),
      password: nuevoPassword.value,
      rol_id: Number(nuevoRolId.value),
    }
    await api.post('/usuarios', payload)
    cerrarModalCrear()
    mensajeExito.value = 'Usuario creado con éxito'
    setTimeout(() => {
      mensajeExito.value = ''
    }, 4000)
    await cargarDatos()
  } catch (err) {
    if (axios.isAxiosError(err)) {
      errorCrear.value = err.response?.data?.detail || 'Error al crear el usuario'
    } else {
      errorCrear.value = 'Error al procesar la solicitud'
    }
  } finally {
    guardandoUsuario.value = false
  }
}

async function alternarEstado(u: Usuario) {
  error.value = ''
  mensajeExito.value = ''
  try {
    if (u.estado === 'activo') {
      await api.patch(`/usuarios/${u.id}/desactivar`)
      mensajeExito.value = `Usuario ${u.nombre} desactivado (baja lógica)`
    } else {
      await api.patch(`/usuarios/${u.id}/reactivar`)
      mensajeExito.value = `Usuario ${u.nombre} reactivado`
    }
    setTimeout(() => {
      mensajeExito.value = ''
    }, 4000)
    await cargarDatos()
  } catch (err) {
    if (axios.isAxiosError(err)) {
      error.value = err.response?.data?.detail || 'Error al cambiar estado del usuario'
    } else {
      error.value = 'Error al cambiar estado del usuario'
    }
  }
}

function abrirModalReset(u: Usuario) {
  usuarioSeleccionado.value = u
  nuevoPasswordReset.value = ''
  errorReset.value = ''
  modalResetAbierto.value = true
}

function cerrarModalReset() {
  modalResetAbierto.value = false
  usuarioSeleccionado.value = null
}

async function confirmarResetPassword() {
  if (!usuarioSeleccionado.value) return
  if (!nuevoPasswordReset.value || nuevoPasswordReset.value.length < 8) {
    errorReset.value = 'La nueva contraseña debe tener al menos 8 caracteres.'
    return
  }

  reseteandoPassword.value = true
  errorReset.value = ''
  try {
    await api.post(`/usuarios/${usuarioSeleccionado.value.id}/resetear-password`, {
      password_nuevo: nuevoPasswordReset.value,
    })
    const nombre = usuarioSeleccionado.value.nombre
    cerrarModalReset()
    mensajeExito.value = `Contraseña actualizada para ${nombre}`
    setTimeout(() => {
      mensajeExito.value = ''
    }, 4000)
  } catch (err) {
    if (axios.isAxiosError(err)) {
      errorReset.value = err.response?.data?.detail || 'Error al resetear la contraseña'
    } else {
      errorReset.value = 'Error al resetear la contraseña'
    }
  } finally {
    reseteandoPassword.value = false
  }
}

onMounted(cargarDatos)
</script>

<template>
  <div class="usuarios-view">
    <div class="header-nav">
      <router-link to="/" class="btn-back"><i class="pi pi-arrow-left"></i> Volver</router-link>
      <h1>Gestión de Usuarios</h1>
      <div style="flex-grow: 1"></div>
      <button class="btn btn-primary" @click="abrirModalCrear">
        + Nuevo usuario
      </button>
    </div>

    <p v-if="error" class="alert alert-error">{{ error }}</p>
    <p v-if="mensajeExito" class="alert alert-success">{{ mensajeExito }}</p>

    <!-- Filtros -->
    <div class="filtros">
      <label>
        Rol:
        <select v-model="filtroRol">
          <option value="">Todos los roles</option>
          <option v-for="r in roles" :key="r.id" :value="r.nombre">
            {{ r.nombre }}
          </option>
        </select>
      </label>

      <label>
        Estado:
        <select v-model="filtroEstado">
          <option value="">Todos los estados</option>
          <option value="activo">Activo</option>
          <option value="baja">Baja</option>
        </select>
      </label>
    </div>

    <!-- Tabla -->
    <div v-if="cargando" class="cargando">Cargando usuarios...</div>
    <div v-else class="table-container">
      <table v-if="usuariosFiltrados.length > 0">
        <thead>
          <tr>
            <th>ID</th>
            <th>Nombre</th>
            <th>Correo electrónico</th>
            <th>Rol</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in usuariosFiltrados" :key="u.id">
            <td>{{ u.id }}</td>
            <td class="bold">{{ u.nombre }}</td>
            <td>{{ u.email }}</td>
            <td><span class="badge badge-rol">{{ u.rol }}</span></td>
            <td>
              <span :class="['badge', u.estado === 'activo' ? 'badge-activo' : 'badge-baja']">
                {{ u.estado === 'activo' ? 'Activo' : 'Baja' }}
              </span>
            </td>
            <td class="acciones">
              <button
                :class="['btn btn-sm', u.estado === 'activo' ? 'btn-danger' : 'btn-success']"
                @click="alternarEstado(u)"
              >
                {{ u.estado === 'activo' ? 'Desactivar' : 'Reactivar' }}
              </button>
              <button
                class="btn btn-sm btn-outline"
                @click="abrirModalReset(u)"
              >
                Resetear contraseña
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="vacio">No se encontraron usuarios con los criterios especificados.</p>
    </div>

    <!-- Modal Crear Usuario -->
    <div v-if="modalCrearAbierto" class="modal-backdrop">
      <div class="modal">
        <h2>Crear nuevo usuario</h2>
        <form @submit.prevent="crearUsuario">
          <label>
            Nombre completo *
            <input v-model="nuevoNombre" type="text" required placeholder="Ej: Juan Pérez" />
          </label>

          <label>
            Correo electrónico *
            <input v-model="nuevoEmail" type="email" required placeholder="ejemplo@simonpatino.com" />
          </label>

          <label>
            Contraseña (mínimo 8 caracteres) *
            <input
              v-model="nuevoPassword"
              type="password"
              required
              minlength="8"
              placeholder="••••••••"
            />
          </label>

          <label>
            Rol *
            <select v-model="nuevoRolId" required>
              <option v-for="r in roles" :key="r.id" :value="r.id">
                {{ r.nombre }}
              </option>
            </select>
          </label>

          <p v-if="errorCrear" class="alert alert-error">{{ errorCrear }}</p>

          <div class="modal-actions">
            <button type="button" class="btn btn-outline" @click="cerrarModalCrear">
              Cancelar
            </button>
            <button type="submit" class="btn btn-primary" :disabled="guardandoUsuario">
              {{ guardandoUsuario ? 'Guardando...' : 'Crear usuario' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Resetear Contraseña -->
    <div v-if="modalResetAbierto" class="modal-backdrop">
      <div class="modal">
        <h2>Resetear contraseña</h2>
        <p v-if="usuarioSeleccionado" class="modal-desc">
          Restablecer contraseña para <strong>{{ usuarioSeleccionado.nombre }}</strong> ({{ usuarioSeleccionado.email }}).
        </p>

        <form @submit.prevent="confirmarResetPassword">
          <label>
            Nueva contraseña (mínimo 8 caracteres) *
            <input
              v-model="nuevoPasswordReset"
              type="password"
              required
              minlength="8"
              placeholder="Nueva contraseña segura"
            />
          </label>

          <p v-if="errorReset" class="alert alert-error">{{ errorReset }}</p>

          <div class="modal-actions">
            <button type="button" class="btn btn-outline" @click="cerrarModalReset">
              Cancelar
            </button>
            <button type="submit" class="btn btn-primary" :disabled="reseteandoPassword">
              {{ reseteandoPassword ? 'Restableciendo...' : 'Restablecer contraseña' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.usuarios-view {
  padding: 2rem;
  font-family: system-ui, sans-serif;
  max-width: 1200px;
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

.badge {
  display: inline-block;
  padding: 0.2rem 0.55rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-rol {
  background: #ddf4ff;
  color: #0969da;
  border: 1px solid #54aeff;
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

.modal-desc {
  font-size: 0.9rem;
  color: #555;
  margin-bottom: 1rem;
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
.modal select {
  padding: 0.5rem 0.7rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 0.9rem;
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
