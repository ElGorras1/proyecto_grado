<script setup lang="ts">
/**
 * Componente para el módulo de Trazabilidad y Análisis de Activos.
 * Renderiza nodos y aristas con Cytoscape.js sobre un lienzo técnico estilo Blueprint.
 */
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import cytoscape, { type Core, type ElementDefinition } from 'cytoscape'

const props = defineProps<{
  elementos: ElementDefinition[]
  altura?: string
}>()

const contenedor = ref<HTMLDivElement | null>(null)
let cy: Core | null = null
const leyendaAbierta = ref(true)

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
          'background-color': '#2563eb',
          label: 'data(label)',
          color: '#f8fafc',
          'font-size': 11,
          'font-weight': 'bold',
          'text-valign': 'bottom',
          'text-margin-y': 6,
          'text-background-color': '#0f172a',
          'text-background-opacity': 0.8,
          'text-background-padding': '3px',
          'text-background-shape': 'roundrectangle',
          width: 38,
          height: 38,
          'border-width': 3,
          'border-color': '#60a5fa',
          'border-opacity': 0.9,
        },
      },
      {
        selector: 'node[tipo = "almacen"]',
        style: {
          'background-color': '#2563eb',
          'border-color': '#93c5fd',
        },
      },
      {
        selector: 'node[tipo = "cedoal"]',
        style: {
          'background-color': '#d97706',
          'border-color': '#fcd34d',
        },
      },
      {
        selector: 'node[tipo = "galeria"]',
        style: {
          'background-color': '#059669',
          'border-color': '#6ee7b7',
        },
      },
      {
        selector: 'edge',
        style: {
          width: 2.5,
          'line-color': '#64748b',
          'target-arrow-color': '#94a3b8',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'arrow-scale': 1.2,
          label: 'data(label)',
          'font-size': 9,
          color: '#94a3b8',
          'text-background-color': '#0f172a',
          'text-background-opacity': 0.7,
          'text-background-padding': '2px',
        },
      },
    ],
    layout: {
      name: 'breadthfirst',
      directed: true,
      padding: 40,
      spacingFactor: 1.2,
    },
  })
}

function zoomIn() {
  if (cy && typeof cy.zoom === 'function') {
    cy.zoom({
      level: cy.zoom() * 1.25,
      renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 },
    })
  }
}

function zoomOut() {
  if (cy && typeof cy.zoom === 'function') {
    cy.zoom({
      level: cy.zoom() * 0.8,
      renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 },
    })
  }
}

function fitView() {
  if (cy && typeof cy.fit === 'function') {
    cy.fit(undefined, 40)
  }
}

function resetView() {
  if (cy && typeof cy.reset === 'function') {
    cy.reset()
    if (typeof cy.fit === 'function') {
      cy.fit(undefined, 40)
    }
  }
}

onMounted(render)
watch(() => props.elementos, render, { deep: true })
onBeforeUnmount(() => cy?.destroy())
</script>

<template>
  <div class="relative w-full rounded-xl overflow-hidden border border-slate-700/60 shadow-lg bg-slate-950">
    <!-- Barra de Cabecera del Lienzo -->
    <div class="flex items-center justify-between px-4 py-2.5 bg-slate-900 border-b border-slate-800 text-slate-300">
      <div class="flex items-center gap-2">
        <span class="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse"></span>
        <span class="text-xs font-semibold tracking-wide text-slate-200">
          Lienzo Digital de Trazabilidad Institucional
        </span>
      </div>
      <div class="flex items-center gap-1.5 text-xs text-slate-400">
        <i class="pi pi-compass text-xs"></i>
        <span>Cytoscape.js Engine</span>
      </div>
    </div>

    <!-- Contenedor del Grafo con Fondo Blueprint -->
    <div
      class="blueprint-grid relative w-full"
      :style="{ height: altura || '460px' }"
    >
      <!-- Canvas de Cytoscape (Debe mantener la clase .grafo-container para los tests) -->
      <div ref="contenedor" class="grafo-container w-full h-full"></div>

      <!-- Controles Flotantes de Navegación del Grafo -->
      <div class="absolute bottom-4 left-4 z-10 flex flex-col gap-1.5 bg-slate-900/90 backdrop-blur-md p-1.5 rounded-xl border border-slate-700/60 shadow-xl">
        <button
          type="button"
          class="w-8 h-8 rounded-lg flex items-center justify-center text-slate-300 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
          title="Acercar (+)"
          @click="zoomIn"
        >
          <i class="pi pi-plus text-xs"></i>
        </button>
        <button
          type="button"
          class="w-8 h-8 rounded-lg flex items-center justify-center text-slate-300 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
          title="Alejar (-)"
          @click="zoomOut"
        >
          <i class="pi pi-minus text-xs"></i>
        </button>
        <button
          type="button"
          class="w-8 h-8 rounded-lg flex items-center justify-center text-slate-300 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
          title="Centrar / Ajustar"
          @click="fitView"
        >
          <i class="pi pi-arrows-alt text-xs"></i>
        </button>
        <button
          type="button"
          class="w-8 h-8 rounded-lg flex items-center justify-center text-slate-300 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
          title="Restablecer Vista"
          @click="resetView"
        >
          <i class="pi pi-refresh text-xs"></i>
        </button>
      </div>

      <!-- Panel Flotante de Leyenda Interactiva -->
      <div class="absolute top-4 right-4 z-10 bg-slate-900/90 backdrop-blur-md rounded-xl border border-slate-700/60 shadow-xl text-xs overflow-hidden max-w-xs transition-all">
        <div
          class="px-3 py-2 bg-slate-800/80 flex items-center justify-between cursor-pointer text-slate-200 font-semibold gap-3"
          @click="leyendaAbierta = !leyendaAbierta"
        >
          <span class="flex items-center gap-1.5">
            <i class="pi pi-info-circle text-xs text-blue-400"></i>
            <span>Leyenda de Nodos</span>
          </span>
          <i :class="['pi text-[10px] text-slate-400', leyendaAbierta ? 'pi-chevron-up' : 'pi-chevron-down']"></i>
        </div>

        <div v-if="leyendaAbierta" class="p-3 space-y-2 text-slate-300">
          <div class="flex items-center gap-2">
            <span class="w-3.5 h-3.5 rounded-full bg-blue-600 border border-blue-400 shrink-0"></span>
            <span>Almacén Central / Depósito</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-3.5 h-3.5 rounded-full bg-amber-600 border border-amber-400 shrink-0"></span>
            <span>Centro Pedagógico CEDOAL</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-3.5 h-3.5 rounded-full bg-emerald-600 border border-emerald-400 shrink-0"></span>
            <span>Galería de Arte Patiño</span>
          </div>
          <div class="pt-1 border-t border-slate-800 flex items-center gap-2 text-slate-400 text-[11px]">
            <span class="w-5 h-0.5 bg-slate-500 shrink-0"></span>
            <span>Arista: Transferencias de Custodia</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grafo-container {
  width: 100%;
  height: 100%;
}
</style>
