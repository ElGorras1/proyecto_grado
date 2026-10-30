<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
const auth = useAuthStore()
const router = useRouter()
const secciones = [
  { ruta: 'kardexDigital', icono: 'pi-book', titulo: 'Kárdex digital', descripcion: 'Historial, fotografías, revisión HIL y cobertura documental.', categoria: 'Documentar y validar' },
  { ruta: 'inventarioVivo', icono: 'pi-box', titulo: 'Inventario actual', descripcion: 'Existencias, operaciones, transferencias y custodia.', categoria: 'Operar y conciliar' },
  { ruta: 'reporteInventario', icono: 'pi-chart-bar', titulo: 'Reportes', descripcion: 'Filtros por gestión, movimientos y descarga del detalle.', categoria: 'Revisar y analizar' },
  { ruta: 'analitica', icono: 'pi-search', titulo: 'Analítica y auditoría histórica', descripcion: 'Reglas, entrenamiento, versiones y resultados del modelo.', categoria: 'Revisar y analizar' },
  { ruta: 'analiticaOperativa', icono: 'pi-chart-line', titulo: 'Analítica de operaciones digitales', descripcion: 'Controles y preparación del modelo para eventos reales.', categoria: 'Revisar y analizar' },
  { ruta: 'gestionInstitucional', icono: 'pi-calendar', titulo: 'Informe institucional y cierres anuales', descripcion: 'Balances, consulta por gestión, cierre y reapertura.', categoria: 'Operar y conciliar' },
  { ruta: 'alertasInventario', icono: 'pi-exclamation-triangle', titulo: 'Alertas y seguimiento de inventario', descripcion: 'Casos, responsables, evidencia y conclusiones.', categoria: 'Revisar y analizar' },
  { ruta: 'preparacionInventario', icono: 'pi-check-square', titulo: 'Preparación del inventario', descripcion: 'Pendientes de fuente, conteo y ubicación; fichas imprimibles.', categoria: 'Operar y conciliar' },
  { ruta: 'validacionProyecto', icono: 'pi-check-circle', titulo: 'Validación del proyecto', descripcion: 'Muestras, cotejos independientes y métricas respaldadas.', categoria: 'Documentar y validar' },
  { ruta: 'usuarios', icono: 'pi-users', titulo: 'Gestión de usuarios', descripcion: 'Cuentas, roles, estado y adscripción.', categoria: 'Administrar', roles: ['Administrador'] },
  { ruta: 'areasCatalogos', icono: 'pi-sitemap', titulo: 'Áreas y catálogos', descripcion: 'Ubicaciones operativas, catálogo histórico y equivalencias.', categoria: 'Administrar', roles: ['Administrador', 'Auditor'] },
  { ruta: 'reporteAccesos', icono: 'pi-history', titulo: 'Registro de accesos', descripcion: 'Fechas, cuentas y resultados de acceso.', categoria: 'Administrar', roles: ['Administrador', 'Auditor'] },
]
const seccionesVisibles = computed(() => secciones.filter(s => !s.roles || s.roles.includes(auth.rol ?? '')))
function cerrarSesion() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <main class="dashboard">
    <header class="inicio-encabezado">
      <div><p class="sobre-titulo">INICIO</p><h1>Tu espacio de trabajo</h1><p class="introduccion">Todas las herramientas, organizadas para encontrarlas mejor.</p></div>
      <div class="sesion">
        <div v-if="auth.usuario"><strong>{{ auth.usuario.nombre }}</strong><span>{{ auth.usuario.rol }}</span></div>
        <button class="btn-outline" @click="cerrarSesion">Cerrar sesión</button>
      </div>
    </header>
    <nav class="mosaico-secciones" aria-label="Herramientas del sistema">
      <router-link v-for="seccion in seccionesVisibles" :key="seccion.ruta" :to="{ name: seccion.ruta }" class="acceso">
        <span class="icono-seccion"><i :class="['pi', seccion.icono]" aria-hidden="true"></i></span>
        <div class="acceso-contenido">
          <h2>{{ seccion.titulo }}</h2><p>{{ seccion.descripcion }}</p>
          <span class="categoria">{{ seccion.categoria }}</span>
        </div>
        <i class="pi pi-arrow-up-right acceso-flecha" aria-hidden="true"></i>
      </router-link>
    </nav>
    <footer class="inicio-pie"><span>{{ seccionesVisibles.length }} accesos disponibles</span><span>Archivo histórico · Operaciones · Auditoría · Administración</span></footer>
  </main>
</template>

<style scoped>
.dashboard { max-width: 1200px; margin: auto; padding: clamp(1.5rem, 4vw, 3rem) 1.5rem; }
.inicio-encabezado { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1.5rem; margin-bottom: 2rem; }
.sobre-titulo { margin: 0 0 .6rem; font-size: .72rem; letter-spacing: .14em; color: var(--text-secondary); }
h1 { margin: 0; font-weight: 600; }
.introduccion { color: var(--text-secondary); margin: .75rem 0 0; font-size: .95rem; }
.sesion { display: flex; flex-wrap: wrap; align-items: center; gap: 1rem; }
.sesion strong, .sesion span { display: block; font-size: .82rem; }
.sesion strong { font-weight: 500; }
.sesion span { color: var(--text-secondary); margin-top: .2rem; }
.mosaico-secciones { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.125rem; }
.acceso { position: relative; display: flex; align-items: flex-start; gap: .9rem; min-width: 0; padding: 1.25rem; border: 1px solid var(--border-color); border-radius: var(--radius); background: var(--bg-color); color: var(--text-primary); text-decoration: none; transition: border-color .18s, box-shadow .18s; }
.acceso:hover { border-color: #99b3c5; box-shadow: var(--shadow); }
.icono-seccion { display: grid; place-items: center; flex-shrink: 0; width: 36px; height: 36px; border-radius: 9px; background: var(--bg-subtle); color: var(--primary); font-size: 1rem; }
.acceso-contenido { display: flex; flex-direction: column; align-self: stretch; min-width: 0; flex: 1; }
.acceso h2 { font-size: .98rem; font-weight: 500; line-height: 1.4; margin: 0 1rem .5rem 0; overflow-wrap: anywhere; }
.acceso p { font-size: .82rem; color: var(--text-secondary); line-height: 1.6; margin: 0 0 1rem; }
.categoria { margin-top: auto; color: var(--primary); font-size: .73rem; }
.acceso-flecha { position: absolute; top: 1.35rem; right: 1rem; color: var(--text-muted); font-size: .7rem; }
.inicio-pie { display: flex; flex-wrap: wrap; gap: .5rem 1.5rem; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border-color); color: var(--text-secondary); font-size: .75rem; }
@media (max-width: 950px) { .mosaico-secciones { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 600px) { .dashboard { padding: 1.5rem 1rem; } .mosaico-secciones { grid-template-columns: minmax(0, 1fr); gap: .9rem; } .inicio-encabezado { margin-bottom: 1.5rem; } }
</style>
