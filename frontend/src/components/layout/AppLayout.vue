<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const collapsed = ref(false)
const userMenuOpen = ref(false)
const userMenuRef = ref<HTMLElement | null>(null)

function toggleSidebar() {
  collapsed.value = !collapsed.value
}

function cerrarSesion() {
  userMenuOpen.value = false
  auth.logout()
  router.push({ name: 'login' })
}

// Iniciales del usuario
const userInitials = computed(() => {
  if (!auth.usuario?.nombre) return 'U'
  const partes = auth.usuario.nombre.trim().split(/\s+/)
  if (partes.length >= 2) {
    return (partes[0][0] + partes[1][0]).toUpperCase()
  }
  return partes[0].slice(0, 2).toUpperCase()
})

// Mapeo de rutas para breadcrumbs dinámicos
const routeNameMap: Record<string, string> = {
  dashboard: 'Panel Principal',
  activos: 'Gestión de Activos',
  existencias: 'Existencias por Área',
  categorias: 'Categorías de Activos',
  areas: 'Gestión de Áreas',
  reporteInventario: 'Reporte de Inventario',
  reporteAccesos: 'Reporte de Accesos',
  usuarios: 'Gestión de Usuarios',
  admin: 'Panel Administrativo',
}

const currentBreadcrumb = computed(() => {
  const name = route.name as string
  return routeNameMap[name] || 'Módulo'
})

// Cierre de menú al hacer clic afuera
function handleClickOutside(event: MouseEvent) {
  if (userMenuRef.value && !userMenuRef.value.contains(event.target as Node)) {
    userMenuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="min-h-screen bg-slate-50 flex flex-col font-sans">
    <div class="flex flex-1 overflow-hidden">
      <!-- SIDEBAR -->
      <aside
        :class="[
          'bg-white border-r border-slate-200/80 flex flex-col transition-all duration-300 z-30 shrink-0 select-none shadow-sm',
          collapsed ? 'w-20' : 'w-64'
        ]"
      >
        <!-- Logo e Identidad Institucional -->
        <div class="h-20 border-b border-slate-100 flex items-center px-4 justify-between">
          <div v-if="!collapsed" class="flex items-center gap-3 overflow-hidden">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-slate-900 to-blue-700 flex items-center justify-center text-white font-black text-lg shadow-md shrink-0">
              P
            </div>
            <div class="flex flex-col min-w-0">
              <span class="text-sm font-bold text-slate-900 tracking-tight leading-tight truncate">
                Fundación Simón I. Patiño
              </span>
              <span class="inline-flex items-center px-1.5 py-0.5 mt-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-100 w-max">
                Sistema de Trazabilidad v1.0
              </span>
            </div>
          </div>
          <div v-else class="w-full flex justify-center">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-slate-900 to-blue-700 flex items-center justify-center text-white font-black text-lg shadow-md">
              P
            </div>
          </div>
        </div>

        <!-- Menú de Navegación -->
        <nav class="flex-1 overflow-y-auto py-4 px-3 space-y-1.5">
          <!-- Panel Principal -->
          <router-link
            :to="{ name: 'dashboard' }"
            :class="[
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group relative',
              route.name === 'dashboard'
                ? 'bg-slate-100 text-blue-600 font-semibold border-l-4 border-blue-600'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            ]"
            :title="collapsed ? 'Panel Principal' : ''"
          >
            <i class="pi pi-th-large text-base shrink-0 group-hover:scale-110 transition-transform"></i>
            <span v-if="!collapsed" class="truncate">Panel Principal</span>
          </router-link>

          <!-- Gestión de Activos (Admin / Operador) -->
          <router-link
            v-if="auth.rol === 'Administrador' || auth.rol === 'Operador'"
            :to="{ name: 'activos' }"
            :class="[
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group relative',
              route.name === 'activos'
                ? 'bg-slate-100 text-blue-600 font-semibold border-l-4 border-blue-600'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            ]"
            :title="collapsed ? 'Gestión de Activos' : ''"
          >
            <i class="pi pi-box text-base shrink-0 group-hover:scale-110 transition-transform"></i>
            <span v-if="!collapsed" class="truncate">Gestión de Activos</span>
          </router-link>

          <!-- Existencias por Área (Admin / Operador) -->
          <router-link
            v-if="auth.rol === 'Administrador' || auth.rol === 'Operador'"
            :to="{ name: 'existencias' }"
            :class="[
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group relative',
              route.name === 'existencias'
                ? 'bg-slate-100 text-blue-600 font-semibold border-l-4 border-blue-600'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            ]"
            :title="collapsed ? 'Existencias por Área' : ''"
          >
            <i class="pi pi-database text-base shrink-0 group-hover:scale-110 transition-transform"></i>
            <span v-if="!collapsed" class="truncate">Existencias por Área</span>
          </router-link>

          <!-- Categorías de Activos (Admin / Operador) -->
          <router-link
            v-if="auth.rol === 'Administrador' || auth.rol === 'Operador'"
            :to="{ name: 'categorias' }"
            :class="[
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group relative',
              route.name === 'categorias'
                ? 'bg-slate-100 text-blue-600 font-semibold border-l-4 border-blue-600'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            ]"
            :title="collapsed ? 'Categorías de Activos' : ''"
          >
            <i class="pi pi-tags text-base shrink-0 group-hover:scale-110 transition-transform"></i>
            <span v-if="!collapsed" class="truncate">Categorías de Activos</span>
          </router-link>

          <!-- Gestión de Áreas (Admin) -->
          <router-link
            v-if="auth.rol === 'Administrador'"
            :to="{ name: 'areas' }"
            :class="[
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group relative',
              route.name === 'areas'
                ? 'bg-slate-100 text-blue-600 font-semibold border-l-4 border-blue-600'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            ]"
            :title="collapsed ? 'Gestión de Áreas' : ''"
          >
            <i class="pi pi-sitemap text-base shrink-0 group-hover:scale-110 transition-transform"></i>
            <span v-if="!collapsed" class="truncate">Gestión de Áreas</span>
          </router-link>

          <!-- Separador de Reportes -->
          <div v-if="!collapsed" class="pt-3 pb-1 px-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Informes & Auditoría
          </div>

          <!-- Reporte de Inventario (Todos) -->
          <router-link
            v-if="auth.rol === 'Administrador' || auth.rol === 'Operador' || auth.rol === 'Auditor'"
            :to="{ name: 'reporteInventario' }"
            :class="[
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group relative',
              route.name === 'reporteInventario'
                ? 'bg-slate-100 text-blue-600 font-semibold border-l-4 border-blue-600'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            ]"
            :title="collapsed ? 'Reporte de Inventario' : ''"
          >
            <i class="pi pi-chart-bar text-base shrink-0 group-hover:scale-110 transition-transform"></i>
            <span v-if="!collapsed" class="truncate">Reporte de Inventario</span>
          </router-link>

          <!-- Reporte de Accesos (Admin / Auditor) -->
          <router-link
            v-if="auth.rol === 'Administrador' || auth.rol === 'Auditor'"
            :to="{ name: 'reporteAccesos' }"
            :class="[
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group relative',
              route.name === 'reporteAccesos'
                ? 'bg-slate-100 text-blue-600 font-semibold border-l-4 border-blue-600'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            ]"
            :title="collapsed ? 'Reporte de Accesos' : ''"
          >
            <i class="pi pi-history text-base shrink-0 group-hover:scale-110 transition-transform"></i>
            <span v-if="!collapsed" class="truncate">Reporte de Accesos</span>
          </router-link>

          <!-- Gestión de Usuarios (Admin) -->
          <router-link
            v-if="auth.rol === 'Administrador'"
            :to="{ name: 'usuarios' }"
            :class="[
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group relative',
              route.name === 'usuarios'
                ? 'bg-slate-100 text-blue-600 font-semibold border-l-4 border-blue-600'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            ]"
            :title="collapsed ? 'Gestión de Usuarios' : ''"
          >
            <i class="pi pi-users text-base shrink-0 group-hover:scale-110 transition-transform"></i>
            <span v-if="!collapsed" class="truncate">Gestión de Usuarios</span>
          </router-link>

          <!-- Panel Administrativo (Admin) -->
          <router-link
            v-if="auth.rol === 'Administrador'"
            :to="{ name: 'admin' }"
            :class="[
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group relative',
              route.name === 'admin'
                ? 'bg-slate-100 text-blue-600 font-semibold border-l-4 border-blue-600'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            ]"
            :title="collapsed ? 'Panel de Administración' : ''"
          >
            <i class="pi pi-shield text-base shrink-0 group-hover:scale-110 transition-transform"></i>
            <span v-if="!collapsed" class="truncate">Panel Administrativo</span>
          </router-link>
        </nav>

        <!-- Botón para colapsar/expandir menú -->
        <div class="p-3 border-t border-slate-100 flex items-center justify-between">
          <button
            class="w-full flex items-center justify-center gap-2 p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 text-xs font-medium transition-colors cursor-pointer"
            :title="collapsed ? 'Expandir menú' : 'Colapsar menú'"
            @click="toggleSidebar"
          >
            <i :class="['pi text-sm transition-transform', collapsed ? 'pi-chevron-right' : 'pi-chevron-left']"></i>
            <span v-if="!collapsed">Colapsar menú</span>
          </button>
        </div>
      </aside>

      <!-- CONTENIDO PRINCIPAL Y TOP NAVBAR -->
      <div class="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <!-- TOP NAVBAR -->
        <header class="h-16 bg-white border-b border-slate-200/80 px-6 flex items-center justify-between sticky top-0 z-20 shadow-xs">
          <!-- Breadcrumbs dinámicos -->
          <div class="flex items-center gap-2 text-sm">
            <router-link
              :to="{ name: 'dashboard' }"
              class="text-slate-400 hover:text-slate-600 transition-colors flex items-center gap-1.5"
            >
              <i class="pi pi-home text-xs"></i>
              <span>Inicio</span>
            </router-link>
            <i class="pi pi-angle-right text-xs text-slate-300"></i>
            <span class="text-slate-800 font-medium">
              {{ currentBreadcrumb }}
            </span>
          </div>

          <!-- Lado Derecho: Estado del Servidor & Perfil de Usuario -->
          <div class="flex items-center gap-5">
            <!-- Indicador de estado del sistema -->
            <div class="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200/60 text-[11px] font-medium text-emerald-700">
              <span class="relative flex h-2 w-2">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span>Conectado al Servidor</span>
            </div>

            <!-- Separador sutil -->
            <div class="h-6 w-px bg-slate-200 hidden sm:block"></div>

            <!-- Menú Desplegable de Usuario -->
            <div ref="userMenuRef" class="relative">
              <button
                class="flex items-center gap-3 p-1.5 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer border border-transparent hover:border-slate-200 focus:outline-none"
                @click="userMenuOpen = !userMenuOpen"
              >
                <!-- Avatar con Iniciales -->
                <div class="w-9 h-9 rounded-full bg-slate-900 text-white font-bold text-xs flex items-center justify-center shadow-xs">
                  {{ userInitials }}
                </div>

                <!-- Nombre y Rol -->
                <div class="hidden md:flex flex-col text-left">
                  <span class="text-xs font-bold text-slate-900 leading-tight truncate max-w-[130px]">
                    {{ auth.usuario?.nombre ?? 'Usuario' }}
                  </span>
                  <div class="mt-0.5">
                    <span
                      v-if="auth.rol === 'Administrador'"
                      class="inline-flex items-center px-1.5 py-0.2 rounded text-[10px] font-semibold bg-indigo-100 text-indigo-700"
                    >
                      👑 Administrador
                    </span>
                    <span
                      v-else-if="auth.rol === 'Operador'"
                      class="inline-flex items-center px-1.5 py-0.2 rounded text-[10px] font-semibold bg-blue-100 text-blue-700"
                    >
                      🛠️ Operador
                    </span>
                    <span
                      v-else-if="auth.rol === 'Auditor'"
                      class="inline-flex items-center px-1.5 py-0.2 rounded text-[10px] font-semibold bg-amber-100 text-amber-800"
                    >
                      🔍 Auditor
                    </span>
                    <span
                      v-else
                      class="inline-flex items-center px-1.5 py-0.2 rounded text-[10px] font-semibold bg-slate-100 text-slate-700"
                    >
                      Usuario
                    </span>
                  </div>
                </div>

                <i class="pi pi-chevron-down text-slate-400 text-xs ml-0.5"></i>
              </button>

              <!-- Panel Desplegable de Usuario -->
              <div
                v-if="userMenuOpen"
                class="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-lg border border-slate-200/80 py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150"
              >
                <div class="px-4 py-2.5 border-b border-slate-100">
                  <p class="text-xs text-slate-400 font-medium">Sesión iniciada como</p>
                  <p class="text-sm font-bold text-slate-900 truncate">{{ auth.usuario?.nombre }}</p>
                  <p class="text-xs text-slate-500 truncate">{{ auth.usuario?.email }}</p>
                </div>

                <div class="px-4 py-2 border-b border-slate-100 text-xs text-slate-600 flex items-center justify-between">
                  <span>Rol en el sistema:</span>
                  <span
                    v-if="auth.rol === 'Administrador'"
                    class="font-semibold text-indigo-700"
                  >
                    Administrador
                  </span>
                  <span
                    v-else-if="auth.rol === 'Operador'"
                    class="font-semibold text-blue-700"
                  >
                    Operador
                  </span>
                  <span
                    v-else-if="auth.rol === 'Auditor'"
                    class="font-semibold text-amber-800"
                  >
                    Auditor
                  </span>
                </div>

                <div class="p-1">
                  <button
                    class="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
                    @click="cerrarSesion"
                  >
                    <i class="pi pi-sign-out text-sm"></i>
                    <span>Cerrar Sesión</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </header>

        <!-- CUERPO DE LA VISTA INYECTADA -->
        <main class="flex-1 p-6 md:p-8">
          <slot />
        </main>
      </div>
    </div>
  </div>
</template>
