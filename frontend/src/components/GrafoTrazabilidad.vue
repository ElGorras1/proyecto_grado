<script setup lang="ts">
/** Relaciones explícitas: la posición visual no implica cronología ni recorrido. */
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import cytoscape, { type Core, type ElementDefinition } from 'cytoscape'

const props = defineProps<{
  elementos: ElementDefinition[]
  seleccionado?: string | null
}>()
const emit = defineEmits<{ seleccionar: [clave: string] }>()

const contenedor = ref<HTMLDivElement | null>(null)
let cy: Core | null = null
let observador: ResizeObserver | null = null

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
          'font-size': 10,
          'text-wrap': 'wrap',
          'text-max-width': '100px',
          'text-valign': 'center',
          'text-halign': 'center',
          width: 105,
          height: 60,
          color: '#ffffff',
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
    layout: { name: 'cose', animate: false, numIter: 300, nodeDimensionsIncludeLabels: true, nodeRepulsion: () => 20000 },
  })
  cy.style().selector('node[tipo = "EVENTO"]').style({ shape: 'round-rectangle', width: 115, height: 48, 'background-color': '#0f766e' })
    .selector('node[tipo = "DOCUMENTAL"], node[tipo = "PENDIENTE"]').style({ 'background-color': '#64748b' })
    .selector('node[?contexto]').style({ 'background-color': '#64748b' })
    .selector('edge[certeza = "PENDIENTE"]').style({ 'line-style': 'dashed', 'line-color': '#b45309', 'target-arrow-color': '#b45309' })
    .selector('edge[tipo = "VINCULO"]').style({ 'line-color': '#7c3aed', 'target-arrow-color': '#7c3aed', label: 'data(label)', 'font-size': 8 })
    .selector('node:selected').style({ 'border-width': 3, 'border-color': '#f59e0b' }).update()
  cy.on('tap', 'node[tipo = "EVENTO"]', e => emit('seleccionar', e.target.data('clave')))
  destacar()
  ajustar()
}
function destacar() {
  cy?.nodes().unselect()
  if (props.seleccionado) cy?.getElementById(`evento:${props.seleccionado}`).select()
}

function ajustar() { cy?.resize(); cy?.fit(undefined, 24) }
onMounted(() => {
  render()
  if (typeof ResizeObserver !== 'undefined' && contenedor.value) {
    observador = new ResizeObserver(ajustar)
    observador.observe(contenedor.value)
  }
})
watch(() => props.elementos, render, { deep: true })
watch(() => props.seleccionado, destacar)
onBeforeUnmount(() => { observador?.disconnect(); cy?.destroy() })
</script>

<template>
  <div class="controles"><button type="button" @click="ajustar">Ajustar grafo a la pantalla</button><span>Acerca con la rueda o dos dedos; arrastra para explorar.</span></div>
  <div ref="contenedor" class="grafo-container" role="img" aria-label="Grafo de relaciones documentadas; cada evento también se puede seleccionar en la lista inferior"></div>
</template>

<style scoped>
.grafo-container {
  position: relative;
  overflow: hidden;
  min-width: 0;
  width: 100%;
  height: 420px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}
.controles { display: flex; flex-wrap: wrap; gap: .6rem; align-items: center; margin: .5rem 0; font-size: .85rem; }
.controles button { border: 1px solid #cbd5e1; border-radius: 5px; padding: .5rem; cursor: pointer; background: var(--bg-color, white); color: inherit; }
</style>
