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

interface Area {
  id: number
  nombre: string
  codigo?: string | null
  estado: string
}

const usuarios = ref<Usuario[]>([])
const roles = ref<Rol[]>([])
const areas = ref<Area[]>([])
const cargando = ref(false)
const error = ref('')
const mensajeExito = ref('')

// Filtros
const filtroRol = ref('')
const filtroEstado = ref('')
const filtroBusqueda = ref('')

// Modal Nuevo Usuario
const modalCrearAbierto = ref(false)
const nuevoNombre = ref('')
const nuevoEmail = ref('')
const nuevoPassword = ref('')
const nuevoRolId = ref<number | ''>('')
const nuevoAreaId = ref<number | ''>('')
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
    const [respUsuarios, respRoles, respAreas] = await Promise.all([
      api.get('/usuarios'),
      api.get('/usuarios/roles'),
      api.get('/areas'),
    ])
    usuarios.value = respUsuarios.data
    roles.value = respRoles.data
    areas.value = respAreas.data
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

function nombreArea(areaId: number | null): string {
  if (!areaId) return '—'
  const area = areas.value.find((a) => a.id === areaId)
  return area ? area.nombre : `Área #${areaId}`
}

const usuariosFiltrados = computed(() => {
  return usuarios.value.filter((u) => {
    if (filtroRol.value && u.rol !== filtroRol.value) return false
    if (filtroEstado.value && u.estado !== filtroEstado.value) return false
    if (filtroBusqueda.value.trim()) {
      const q = filtroBusqueda.value.toLowerCase()
      const matchNombre = u.nombre.toLowerCase().includes(q)
      const matchEmail = u.email.toLowerCase().includes(q)
      if (!matchNombre && !matchEmail) return false
    }
    return true
  })
})

function abrirModalCrear() {
  nuevoNombre.value = ''
  nuevoEmail.value = ''
  nuevoPassword.value = ''
  nuevoRolId.value = roles.value.length > 0 ? roles.value[0].id : ''
  nuevoAreaId.value = ''
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
      area_id: nuevoAreaId.value === '' ? null : Number(nuevoAreaId.value),
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
    mensajeExito.value = `Contraseña actualizada con éxito para ${nombre}`
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
  <div class="space-y-6 max-w-7xl mx-auto font-sans">
    <!-- ENCABEZADO -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
      <div>
        <h1 class="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
          <i class="pi pi-users text-blue-600"></i>
          <span>Gestión de Usuarios y Accesos</span>
        </h1>
        <p class="text-sm font-medium text-slate-500 mt-1">
          Control de credenciales, roles RBAC y asignación de custodia por área
        </p>
      </div>

      <button
        class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs hover:shadow transition-all cursor-pointer self-start sm:self-auto"
        @click="abrirModalCrear"
      >
        <i class="pi pi-user-plus text-xs"></i>
        <span>Nuevo Usuario</span>
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
          placeholder="Buscar por nombre o correo electrónico..."
          class="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
        />
      </div>

      <div class="flex flex-wrap items-center gap-3">
        <div class="flex items-center gap-1.5">
          <label class="text-xs font-semibold text-slate-500">Rol:</label>
          <select
            v-model="filtroRol"
            class="px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
          >
            <option value="">Todos los roles</option>
            <option v-for="r in roles" :key="r.id" :value="r.nombre">
              {{ r.nombre }}
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

    <!-- TABLA DE USUARIOS -->
    <div class="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      <div v-if="cargando" class="py-16 text-center text-slate-500">
        <i class="pi pi-spin pi-spinner text-2xl text-blue-600 mb-2"></i>
        <p class="text-xs font-medium">Cargando nómina de usuarios...</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table v-if="usuariosFiltrados.length > 0" class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-50 text-slate-700 font-semibold uppercase text-xs tracking-wider border-b border-slate-200">
              <th class="py-3.5 px-4">ID</th>
              <th class="py-3.5 px-4">Usuario</th>
              <th class="py-3.5 px-4">Correo Electrónico</th>
              <th class="py-3.5 px-4">Rol Asignado</th>
              <th class="py-3.5 px-4">Área de Custodia</th>
              <th class="py-3.5 px-4">Estado</th>
              <th class="py-3.5 px-4 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-xs text-slate-700">
            <tr
              v-for="u in usuariosFiltrados"
              :key="u.id"
              class="hover:bg-slate-50/80 transition-colors"
            >
              <td class="py-3.5 px-4 font-mono text-slate-400">#{{ u.id }}</td>
              <td class="py-3.5 px-4">
                <div class="flex items-center gap-2.5">
                  <div class="w-7 h-7 rounded-full bg-slate-800 text-white font-bold text-[10px] flex items-center justify-center">
                    {{ u.nombre.slice(0, 2).toUpperCase() }}
                  </div>
                  <span class="font-bold text-slate-900">{{ u.nombre }}</span>
                </div>
              </td>
              <td class="py-3.5 px-4 text-slate-600 font-mono text-[11px]">
                {{ u.email }}
              </td>
              <td class="py-3.5 px-4 whitespace-nowrap">
                <span
                  v-if="u.rol === 'Administrador'"
                  class="badge-role-admin"
                >
                  👑 Administrador
                </span>
                <span
                  v-else-if="u.rol === 'Operador'"
                  class="badge-role-operador"
                >
                  🛠️ Operador
                </span>
                <span
                  v-else-if="u.rol === 'Auditor'"
                  class="badge-role-auditor"
                >
                  🔍 Auditor
                </span>
                <span
                  v-else
                  class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700"
                >
                  {{ u.rol }}
                </span>
              </td>
              <td class="py-3.5 px-4 text-slate-600">
                {{ nombreArea(u.area_id) }}
              </td>
              <td class="py-3.5 px-4">
                <span :class="u.estado === 'activo' ? 'badge-status-activo' : 'badge-status-baja'">
                  <span
                    :class="[
                      'w-1.5 h-1.5 rounded-full mr-1.5',
                      u.estado === 'activo' ? 'bg-emerald-500' : 'bg-slate-400'
                    ]"
                  ></span>
                  {{ u.estado === 'activo' ? 'Activo' : 'Baja' }}
                </span>
              </td>
              <td class="py-3.5 px-4 text-right whitespace-nowrap">
                <div class="inline-flex items-center gap-1">
                  <button
                    type="button"
                    class="p-1.5 text-amber-600 hover:text-amber-800 hover:bg-amber-50 rounded-lg transition-colors cursor-pointer"
                    title="Resetear Contraseña"
                    @click="abrirModalReset(u)"
                  >
                    <i class="pi pi-key text-xs"></i>
                  </button>
                  <button
                    type="button"
                    :class="[
                      'p-1.5 rounded-lg transition-colors cursor-pointer',
                      u.estado === 'activo'
                        ? 'text-red-600 hover:text-red-800 hover:bg-red-50'
                        : 'text-emerald-600 hover:text-emerald-800 hover:bg-emerald-50'
                    ]"
                    :title="u.estado === 'activo' ? 'Desactivar Cuenta' : 'Reactivar Cuenta'"
                    @click="alternarEstado(u)"
                  >
                    <i :class="['pi text-xs', u.estado === 'activo' ? 'pi-user-minus' : 'pi-user-plus']"></i>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-else class="py-16 text-center text-slate-500">
          <i class="pi pi-inbox text-3xl text-slate-300 mb-2"></i>
          <p class="text-xs font-semibold text-slate-700">No se encontraron usuarios registrados</p>
        </div>
      </div>

      <div class="px-4 py-3 bg-slate-50 border-t border-slate-200/80 flex items-center justify-between text-xs text-slate-500">
        <span>Mostrando {{ usuariosFiltrados.length }} usuarios en plantilla</span>
        <span class="font-medium">Fundación Simón I. Patiño</span>
      </div>
    </div>

    <!-- MODAL CREAR USUARIO -->
    <div
      v-if="modalCrearAbierto"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto"
    >
      <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-md overflow-hidden animate-in fade-in">
        <div class="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold">
              <i class="pi pi-user-plus"></i>
            </div>
            <div>
              <h2 class="text-sm font-bold text-white">Crear Nuevo Usuario</h2>
              <p class="text-[11px] text-slate-400">Credenciales y privilegios institucionales</p>
            </div>
          </div>
          <button
            type="button"
            class="text-slate-400 hover:text-white transition-colors cursor-pointer"
            @click="cerrarModalCrear"
          >
            <i class="pi pi-times text-sm"></i>
          </button>
        </div>

        <form class="p-6 space-y-4" @submit.prevent="crearUsuario">
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              Nombre Completo *
            </label>
            <input
              v-model="nuevoNombre"
              type="text"
              required
              placeholder="Ej: Lic. Marcelo Quiroga"
              class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              Correo Electrónico *
            </label>
            <input
              v-model="nuevoEmail"
              type="email"
              required
              placeholder="mquiroga@simonpatino.com"
              class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              Contraseña Inicial (mínimo 8 caracteres) *
            </label>
            <input
              v-model="nuevoPassword"
              type="password"
              required
              minlength="8"
              placeholder="••••••••"
              class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">
                Rol Asignado *
              </label>
              <select
                v-model="nuevoRolId"
                required
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                <option v-for="r in roles" :key="r.id" :value="r.id">
                  {{ r.nombre }}
                </option>
              </select>
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">
                Área Asignada
              </label>
              <select
                v-model="nuevoAreaId"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                <option value="">Sin área específica</option>
                <option v-for="a in areas" :key="a.id" :value="a.id">
                  {{ a.nombre }}
                </option>
              </select>
            </div>
          </div>

          <div
            v-if="errorCrear"
            class="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700 flex items-center gap-2"
          >
            <i class="pi pi-exclamation-circle text-red-600"></i>
            <span>{{ errorCrear }}</span>
          </div>

          <div class="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              class="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors cursor-pointer"
              @click="cerrarModalCrear"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="guardandoUsuario"
              class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-xs hover:shadow transition-all disabled:opacity-60 flex items-center gap-2 cursor-pointer"
            >
              <i v-if="guardandoUsuario" class="pi pi-spin pi-spinner text-xs"></i>
              <span>{{ guardandoUsuario ? 'Registrando...' : 'Crear Usuario' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL RESETEAR CONTRASEÑA -->
    <div
      v-if="modalResetAbierto"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto"
    >
      <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-md overflow-hidden animate-in fade-in">
        <div class="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold">
              <i class="pi pi-key"></i>
            </div>
            <div>
              <h2 class="text-sm font-bold text-white">Resetear Contraseña</h2>
              <p class="text-[11px] text-slate-400">Actualizar clave de acceso de usuario</p>
            </div>
          </div>
          <button
            type="button"
            class="text-slate-400 hover:text-white transition-colors cursor-pointer"
            @click="cerrarModalReset"
          >
            <i class="pi pi-times text-sm"></i>
          </button>
        </div>

        <form class="p-6 space-y-4" @submit.prevent="confirmarResetPassword">
          <div v-if="usuarioSeleccionado" class="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-700">
            <span>Usuario a restablecer: </span>
            <strong class="font-bold text-slate-900">{{ usuarioSeleccionado.nombre }}</strong>
            <span class="block text-slate-500 mt-0.5">({{ usuarioSeleccionado.email }})</span>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              Nueva Contraseña (mínimo 8 caracteres) *
            </label>
            <input
              v-model="nuevoPasswordReset"
              type="password"
              required
              minlength="8"
              placeholder="Nueva clave segura"
              class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div
            v-if="errorReset"
            class="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700 flex items-center gap-2"
          >
            <i class="pi pi-exclamation-circle text-red-600"></i>
            <span>{{ errorReset }}</span>
          </div>

          <div class="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              class="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors cursor-pointer"
              @click="cerrarModalReset"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="reseteandoPassword"
              class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-xs hover:shadow transition-all disabled:opacity-60 flex items-center gap-2 cursor-pointer"
            >
              <i v-if="reseteandoPassword" class="pi pi-spin pi-spinner text-xs"></i>
              <span>{{ reseteandoPassword ? 'Actualizando...' : 'Restablecer Clave' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
