<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
const auth = useAuthStore()
const router = useRouter()
const secciones = [
  { ruta: 'kardexDigital', icono: 'pi-book', titulo: 'Kárdex digital', descripcion: 'Consulta el historial, incorpora nuevas hojas y revisa los registros escaneados.', accion: 'Abrir Kárdex' },
  { ruta: 'inventarioVivo', icono: 'pi-box', titulo: 'Inventario actual', descripcion: 'Encuentra tus artículos y registra ingresos, salidas y transferencias.', accion: 'Ver inventario' },
  { ruta: 'reporteInventario', icono: 'pi-chart-bar', titulo: 'Reportes', descripcion: 'Consulta movimientos por gestión, artículo y área, y exporta los resultados.', accion: 'Consultar reportes' },
]
function cerrarSesion() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <main class="dashboard">
    <header class="inicio-encabezado">
      <div><p class="sobre-titulo">INICIO</p><h1>Tu espacio de trabajo</h1><p class="introduccion">Selecciona una sección para continuar.</p></div>
      <div class="sesion">
        <div v-if="auth.usuario"><strong>{{ auth.usuario.nombre }}</strong><span>{{ auth.usuario.rol }}</span></div>
        <button class="btn-outline" @click="cerrarSesion">Cerrar sesión</button>
      </div>
    </header>
    <nav class="accesos-principales" aria-label="Secciones principales">
      <router-link v-for="seccion in secciones" :key="seccion.ruta" :to="{ name: seccion.ruta }" class="acceso">
        <span class="icono-seccion"><i :class="['pi', seccion.icono]" aria-hidden="true"></i></span>
        <h2>{{ seccion.titulo }}</h2><p>{{ seccion.descripcion }}</p>
        <span class="accion">{{ seccion.accion }} <i class="pi pi-arrow-right" aria-hidden="true"></i></span>
      </router-link>
    </nav>
    <p class="herramientas"><router-link :to="{ name: 'analitica' }"><i class="pi pi-search" aria-hidden="true"></i> Analítica y auditoría histórica</router-link></p>
    <p class="herramientas"><router-link :to="{ name: 'analiticaOperativa' }"><i class="pi pi-chart-line" aria-hidden="true"></i> Analítica de operaciones digitales</router-link></p>
    <p class="herramientas"><router-link :to="{ name: 'gestionInstitucional' }"><i class="pi pi-calendar" aria-hidden="true"></i> Informe institucional y cierres anuales</router-link></p>
    <p class="herramientas"><router-link :to="{ name: 'alertasInventario' }"><i class="pi pi-exclamation-triangle" aria-hidden="true"></i> Alertas y seguimiento de inventario</router-link></p>
    <nav v-if="auth.rol === 'Administrador' || auth.rol === 'Auditor'" class="herramientas" aria-label="Herramientas de gestión">
      <span>Herramientas de gestión</span>
      <router-link v-if="auth.rol === 'Administrador'" :to="{ name: 'usuarios' }"><i class="pi pi-users" aria-hidden="true"></i> Gestión de usuarios</router-link>
      <router-link :to="{ name: 'reporteAccesos' }"><i class="pi pi-history" aria-hidden="true"></i> Registro de accesos</router-link>
    </nav>
  </main>
</template>

<style scoped>
.dashboard { max-width: 1200px; margin: auto; padding: clamp(1.5rem, 5vw, 4rem) 1.5rem; }
.inicio-encabezado { display: flex; justify-content: space-between; align-items: center; gap: 1.5rem; margin-bottom: 2.5rem; }
.sobre-titulo { margin: 0 0 .6rem; font-size: .72rem; letter-spacing: .14em; color: var(--text-secondary); }
h1 { margin: 0; font-weight: 600; }
.introduccion { color: var(--text-secondary); margin: .75rem 0 0; font-size: .95rem; }
.sesion { display: flex; align-items: center; gap: 1rem; }
.sesion strong, .sesion span { display: block; font-size: .82rem; }
.sesion strong { font-weight: 500; }
.sesion span { color: var(--text-secondary); margin-top: .2rem; }
.accesos-principales { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.25rem; }
.acceso { display: flex; flex-direction: column; padding: 1.75rem; border: 1px solid var(--border-color); border-radius: 16px; background: white; color: var(--text-primary); text-decoration: none; transition: border-color .18s, box-shadow .18s; }
.acceso:hover { border-color: #99b3c5; box-shadow: var(--shadow); }
.icono-seccion { display: grid; place-items: center; width: 46px; height: 46px; border-radius: 12px; background: var(--bg-subtle); color: var(--primary); font-size: 1.15rem; margin-bottom: 1.5rem; }
.acceso h2 { font-size: 1.2rem; font-weight: 600; margin: 0 0 .65rem; }
.acceso p { font-size: .9rem; color: var(--text-secondary); line-height: 1.65; margin: 0 0 2rem; }
.accion { display: flex; justify-content: space-between; align-items: center; gap: .75rem; margin-top: auto; padding-top: 1rem; border-top: 1px solid var(--border-subtle); color: var(--primary); font-weight: 600; font-size: .85rem; }
.herramientas { display: flex; flex-wrap: wrap; align-items: center; gap: 1rem 1.5rem; margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid var(--border-color); font-size: .83rem; }
.herramientas > span { color: var(--text-secondary); margin-right: auto; }
.herramientas a { display: inline-flex; align-items: center; gap: .5rem; padding: .4rem 0; text-decoration: none; }
.herramientas a:hover { text-decoration: underline; }
@media(max-width: 850px) { .inicio-encabezado { flex-wrap: wrap; } .accesos-principales { gap: .8rem; } .acceso { padding: 1.25rem; } }
@media(max-width: 650px) { .dashboard { padding: 1.5rem 1rem; } .accesos-principales { grid-template-columns: 1fr; } .inicio-encabezado { margin-bottom: 1.5rem; } .acceso p { margin-bottom: 1rem; } .icono-seccion { margin-bottom: 1rem; } .sesion { flex-wrap: wrap; } .herramientas > span { width: 100%; } }
</style>
