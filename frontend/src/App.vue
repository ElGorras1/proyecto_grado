<script setup lang="ts">
import { useRoute } from 'vue-router'
import MarcaInstitucional from '@/components/MarcaInstitucional.vue'
const route = useRoute()
</script>

<template>
  <header v-if="!route.meta.public" class="cabecera-institucional">
    <div class="cabecera-interior">
      <router-link :to="{ name: 'dashboard' }" aria-label="Fundación Simón I. Patiño · Ir al inicio"><MarcaInstitucional /></router-link>
      <span class="nombre-sistema">Gestión de inventario<span>Archivo histórico y operaciones</span></span>
    </div>
  </header>
  <router-view />
</template>

<style scoped>
.cabecera-institucional { background: white; border-bottom: 1px solid var(--border-color); }
.cabecera-interior { max-width: 1360px; margin: auto; padding: .2rem 1.5rem; display: flex; align-items: center; gap: 1.5rem; }
.nombre-sistema { border-left: 1px solid var(--border-color); padding-left: 1.5rem; font-size: .9rem; font-weight: 600; color: var(--text-primary); }
.nombre-sistema span { display: block; color: var(--text-secondary); font-size: .75rem; font-weight: 400; margin-top: .15rem; }
@media (max-width: 480px) { .cabecera-interior { gap: .5rem; padding: .2rem .5rem; } .nombre-sistema { padding-left: .7rem; font-size: .8rem; } .nombre-sistema span { font-size: .7rem; } }
</style>
