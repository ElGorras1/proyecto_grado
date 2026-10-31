<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
</script>
<template>
  <main class="administracion">
    <h1>Administración</h1>
    <p>Configuración institucional y herramientas de uso ocasional.</p>
    <nav aria-label="Administración institucional">
      <router-link v-if="auth.rol === 'Administrador'" :to="{ name: 'usuarios' }"><strong>Usuarios</strong><span>Cuentas, permisos y adscripción.</span></router-link>
      <router-link :to="{ name: 'areasCatalogos' }"><strong>Áreas y equivalencias</strong><span>Ubicaciones y nombres del archivo documental.</span></router-link>
      <router-link :to="{ name: 'reporteAccesos' }"><strong>Registro de accesos</strong><span>Consultar entradas y resultados de acceso.</span></router-link>
      <router-link :to="{ name: 'mantenimientoAnalitico' }"><strong>Mantenimiento del análisis</strong><span>Estado de la automatización y comprobaciones periódicas.</span></router-link>
    </nav>
    <details><summary>Herramientas avanzadas y evaluación del proyecto</summary>
      <p>Se utilizan para evaluación y mantenimiento; el trabajo cotidiano se realiza desde Artículos, Revisiones y Reportes.</p>
      <ul>
        <li><router-link :to="{ name: 'analitica', query: { avanzado: '1' } }">Versiones y configuración del modelo histórico</router-link></li>
        <li><router-link :to="{ name: 'validacionProyecto' }">Estudios de validación independiente</router-link></li>
        <li><router-link :to="{ name: 'muestraValidacion' }">Muestra de revisión documental</router-link></li>
        <li><router-link :to="{ name: 'analiticaOperativa' }">Modelo para operaciones digitales</router-link></li>
      </ul>
    </details>
  </main>
</template>
<style scoped>
.administracion { max-width: 1100px; margin: auto; padding: 2rem 1.25rem; }
nav { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); gap: 1rem; margin: 1.5rem 0; }
nav a { border: 1px solid var(--border-color); padding: 1.3rem; border-radius: var(--radius); text-decoration: none; color: var(--primary); }
nav span { display: block; color: var(--text-secondary); margin-top: .5rem; font-size: .9rem; }
summary { cursor: pointer; padding: 1rem 0; font-weight: 600; } li { margin: .75rem 0; }
</style>
