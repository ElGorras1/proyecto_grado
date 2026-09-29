<script setup lang="ts">
const texto = defineModel<string>({ default: '' })
withDefaults(defineProps<{ placeholder?: string }>(), { placeholder: 'Buscar por nombre o código…' })
</script>
<template>
  <div class="buscador-articulos">
    <i class="pi pi-search" aria-hidden="true"></i>
    <input v-model="texto" type="search" aria-label="Buscar artículos por nombre o código" :placeholder="placeholder" />
  </div>
</template>
<style scoped>
.buscador-articulos { display: flex; align-items: center; gap: .75rem; border: 1px solid var(--border-color); border-radius: 10px; background: white; padding: .25rem .9rem; margin-bottom: 1.5rem; }
.buscador-articulos > i { position: static; flex: 0 0 1rem; color: var(--text-muted); pointer-events: none; }
.buscador-articulos input[type="search"] { flex: 1; min-width: 0; width: 100%; padding: .7rem 0 !important; border: 0 !important; background: transparent !important; box-shadow: none !important; font-size: .95rem !important; }
.buscador-articulos:focus-within { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(67, 105, 134, .14); }
</style>
