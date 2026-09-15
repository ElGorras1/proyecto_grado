import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { roles: ['Administrador', 'Operador', 'Auditor'] },
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('@/views/AdminView.vue'),
      meta: { roles: ['Administrador'] },
    },
    {
      path: '/usuarios',
      name: 'usuarios',
      component: () => import('@/views/UsuariosView.vue'),
      meta: { roles: ['Administrador'] },
    },
    {
      path: '/reportes/accesos',
      name: 'reporteAccesos',
      component: () => import('@/views/ReporteAccesosView.vue'),
      meta: { roles: ['Administrador', 'Auditor'] },
    },
    {
      path: '/kardex-digital',
      name: 'kardexDigital',
      component: () => import('@/views/KardexContinuoView.vue'),
      meta: { roles: ['Administrador', 'Operador', 'Auditor'] },
    },
    {
      path: '/inventario-vivo',
      name: 'inventarioVivo',
      component: () => import('@/views/InventarioActualView.vue'),
      meta: { roles: ['Administrador', 'Operador', 'Auditor'] },
    },
    {
      path: '/403',
      name: 'forbidden',
      component: () => import('@/views/ForbiddenView.vue'),
      meta: { public: true },
    },
  ],
})

// Guard global: exige autenticación y valida el rol contra meta.roles.
// Esto es solo la capa de UX (ocultar navegación); el backend SIEMPRE
// vuelve a validar rol en cada endpoint (ver require_roles en FastAPI).
router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (to.meta.public) return true

  if (!auth.isAuthenticated) {
    return { name: 'login' }
  }

  // Si hay token pero el perfil del usuario todavía no está en memoria
  // (por ejemplo, tras escribir una URL directamente en el navegador,
  // lo cual recarga la página completa y reinicia el store), lo
  // recuperamos ANTES de decidir si el rol tiene permiso. Sin este paso,
  // auth.rol quedaría en null momentáneamente y el guard "fallaría
  // abierto" (dejaría pasar), aunque el backend seguiría rechazando la
  // acción real - ver el caso reportado con un Operador forzando /admin.
  if (!auth.usuario) {
    try {
      await auth.fetchUsuarioActual()
    } catch {
      auth.logout()
      return { name: 'login' }
    }
  }

  const rolesPermitidos = to.meta.roles as string[] | undefined
  if (rolesPermitidos && auth.rol && !rolesPermitidos.includes(auth.rol)) {
    return { name: 'forbidden' }
  }

  return true
})

export default router