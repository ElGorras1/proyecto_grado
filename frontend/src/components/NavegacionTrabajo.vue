<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { espacios, espacioDe, secciones } from '@/services/navegacion'
const ruta = useRoute()
const auth = useAuthStore()
const disponibles = computed(() => espacios.filter(e => !e.roles || e.roles.includes(auth.rol ?? '')))
const area = computed(() => espacioDe(ruta.name))
</script>

<template>
  <div class="navegacion-trabajo">
    <nav aria-label="Navegación principal">
      <router-link :to="{ name: 'dashboard' }" :class="{ actual: ruta.name === 'dashboard' }">Inicio</router-link>
      <router-link v-for="e in disponibles" :key="e.ruta" :to="{ name: e.ruta }" :class="{ actual: area === e.ruta }">{{ e.titulo }}</router-link>
    </nav>
    <nav v-if="area && secciones[area]" class="secundaria" aria-label="Opciones de la sección">
      <router-link v-for="s in secciones[area]" :key="s.ruta" :to="{ name: s.ruta, query: area === 'reportes' ? { gestion: ruta.query.gestion, origen: ruta.query.origen } : area === 'articulosInventario' ? { articulo_id: ruta.query.articulo_id } : undefined }" :class="{ actual: ruta.name === s.ruta }">{{ s.titulo }}</router-link>
      <details v-if="area === 'articulosInventario'"><summary>Más herramientas</summary><router-link :to="{ name: 'preparacionInventario' }">Preparar conteo y ubicación</router-link></details>
    </nav>
  </div>
</template>

<style scoped>
.navegacion-trabajo { max-width: 1360px; margin: auto; padding: .5rem 1.5rem; }
nav { display: flex; flex-wrap: wrap; gap: .35rem .6rem; align-items: center; }
a, summary { display: inline-block; padding: .5rem .65rem; color: var(--text-secondary); border-radius: 6px; font-size: .85rem; text-decoration: none; cursor: pointer; }
a.actual { color: var(--primary); background: var(--bg-subtle); font-weight: 600; }
.secundaria { border-top: 1px solid var(--border-color); padding-top: .35rem; margin-top: .35rem; }
.secundaria a, summary { font-size: .8rem; }
@media(max-width: 600px) { .navegacion-trabajo { padding: .5rem; } a { padding: .4rem; } }
@media print { .navegacion-trabajo { display: none; } }
</style>
