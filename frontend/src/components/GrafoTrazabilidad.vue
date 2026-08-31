<script setup lang="ts">
/**
 * Componente base para el módulo de Trazabilidad y Análisis (Sprint 4).
 * Recibe nodos/aristas ya calculados por NetworkX en el backend
 * (endpoint que aún no existe, ej. GET /trazabilidad/activo/{id}/recorrido)
 * y los renderiza con Cytoscape.js en el navegador.
 */
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import cytoscape, { type Core, type ElementDefinition } from 'cytoscape'

const props = defineProps<{
  elementos: ElementDefinition[]
}>()

const contenedor = ref<HTMLDivElement | null>(null)
let cy: Core | null = null

function render() {
  if (!contenedor.value) return
  cy?.destroy()
  cy = cytoscape({
    container: contenedor.value,
    elements: props.elementos,
    style: [
      {
        selector: 'node',
        style: {
          'background-color': '#1f6feb',
          label: 'data(label)',
          color: '#1a1a1a',
          'font-size': 10,
        },
      },
      {
        selector: 'edge',
        style: {
          width: 2,
          'line-color': '#94a3b8',
          'target-arrow-color': '#94a3b8',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
        },
      },
    ],
    layout: { name: 'breadthfirst' },
  })
}

onMounted(render)
watch(() => props.elementos, render, { deep: true })
onBeforeUnmount(() => cy?.destroy())
</script>

<template>
  <div ref="contenedor" class="grafo-container"></div>
</template>

<style scoped>
.grafo-container {
  width: 100%;
  height: 420px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}
</style>
