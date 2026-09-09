<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  (e: 'validado', datos: Record<string, unknown>): void
  (e: 'cerrar'): void
}>()

// Controles del Visor de Tarjeta
const nivelZoom = ref(1)
const invertirContraste = ref(false)
const altoContraste = ref(false)
const mensajeAlerta = ref('')
const aprobadoExitoso = ref(false)

// Campos extraídos por el modelo TrOCR
const docCodigo = ref('DOC-KDX-1984-042')
const activoCodigo = ref('PAT-ART-089')
const activoNombre = ref('Escultura Bronce "Minero en Reposo"')
const categoria = ref('Colecciones y Patrimonio Cultural')
const area = ref('Galería de Arte Simón I. Patiño')
const unidadMedida = ref('pieza')
const cantidad = ref(1)
const fechaDocumento = ref('1984-05-12')
const observaciones = ref('Firma original de recepción: M. Salamanca. Buen estado de conservación general.')
const revisado = ref(true)

function aumentarZoom() {
  if (nivelZoom.value < 2.5) nivelZoom.value += 0.25
}

function disminuirZoom() {
  if (nivelZoom.value > 0.5) nivelZoom.value -= 0.25
}

function resetZoom() {
  nivelZoom.value = 1
}

function aprobarValidacion() {
  if (!revisado.value) {
    mensajeAlerta.value = 'Debe marcar la casilla de verificación visual antes de aprobar.'
    return
  }
  mensajeAlerta.value = ''
  aprobadoExitoso.value = true
  emit('validado', {
    docCodigo: docCodigo.value,
    activoCodigo: activoCodigo.value,
    activoNombre: activoNombre.value,
    categoria: categoria.value,
    area: area.value,
    cantidad: cantidad.value,
  })
}
</script>

<template>
  <div class="bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden flex flex-col">
    <!-- Barra Superior del Módulo HITL -->
    <div class="px-6 py-4 bg-slate-900 text-white flex flex-wrap items-center justify-between gap-4 border-b border-slate-800">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center font-bold text-base">
          <i class="pi pi-sparkles"></i>
        </div>
        <div>
          <h2 class="text-base font-bold text-white tracking-tight flex items-center gap-2">
            Módulo HITL · Digitalización & Validación de Kardex Histórico
          </h2>
          <p class="text-xs text-slate-400">
            Revisión Humana Asistida para Extracción TrOCR (Vision Transformer & HTR)
          </p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-900/60 text-blue-300 border border-blue-700/50">
          <i class="pi pi-microchip-ai text-xs"></i>
          TrOCR-Patrimonio v2.1
        </span>
        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-300 border border-emerald-700/50">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          96.4% Confianza Global
        </span>
      </div>
    </div>

    <!-- Layout Dividido (Split Panel) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 min-h-[620px] bg-slate-100">
      <!-- PANEL IZQUIERDO: VISOR INTERACTIVO DE TARJETA KARDEX -->
      <div class="lg:col-span-6 bg-slate-950 flex flex-col border-r border-slate-800 relative select-none">
        <!-- Barra de Herramientas del Visor -->
        <div class="px-4 py-2.5 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 flex items-center justify-between text-xs text-slate-300 z-10">
          <div class="flex items-center gap-2">
            <i class="pi pi-image text-amber-400"></i>
            <span class="font-medium">Tarjeta Digitalizada #1984-042</span>
          </div>

          <div class="flex items-center gap-1">
            <button
              type="button"
              class="p-1.5 hover:bg-slate-800 rounded text-slate-300 hover:text-white transition-colors cursor-pointer"
              title="Acercar"
              @click="aumentarZoom"
            >
              <i class="pi pi-search-plus text-xs"></i>
            </button>
            <button
              type="button"
              class="p-1.5 hover:bg-slate-800 rounded text-slate-300 hover:text-white transition-colors cursor-pointer"
              title="Alejar"
              @click="disminuirZoom"
            >
              <i class="pi pi-search-minus text-xs"></i>
            </button>
            <button
              type="button"
              class="p-1.5 hover:bg-slate-800 rounded text-slate-300 hover:text-white transition-colors cursor-pointer"
              title="Restablecer Escala (100%)"
              @click="resetZoom"
            >
              <i class="pi pi-undo text-xs"></i>
            </button>

            <div class="h-4 w-px bg-slate-700 mx-1"></div>

            <!-- Conmutador de Inversión de Contraste -->
            <button
              type="button"
              :class="[
                'flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium transition-colors cursor-pointer',
                invertirContraste
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              ]"
              title="Invertir Contraste para facilitar lectura de tinta tenue"
              @click="invertirContraste = !invertirContraste"
            >
              <i class="pi pi-circle text-xs"></i>
              <span>Invertir Contraste</span>
            </button>

            <!-- Modo Alto Contraste -->
            <button
              type="button"
              :class="[
                'p-1.5 rounded transition-colors cursor-pointer',
                altoContraste ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800'
              ]"
              title="Realzar Nitidez de Tinta"
              @click="altoContraste = !altoContraste"
            >
              <i class="pi pi-sliders-h text-xs"></i>
            </button>
          </div>
        </div>

        <!-- Área del Lienzo de la Tarjeta Kardex Histórica -->
        <div class="flex-1 overflow-auto p-6 flex items-center justify-center relative bg-slate-900/50">
          <div
            :class="[
              'transition-transform duration-150 origin-center max-w-lg w-full',
              invertirContraste ? 'filter invert brightness-110 contrast-125' : '',
              altoContraste ? 'filter contrast-150 brightness-95' : ''
            ]"
            :style="{ transform: `scale(${nivelZoom})` }"
          >
            <!-- TARJETA KARDEX FÍSICA AUTÉNTICA (Estilo Histórico Fundación Patiño) -->
            <div class="bg-[#faf5eb] text-[#342416] p-6 rounded-md shadow-2xl border-2 border-[#d3c2a3] font-serif relative">
              <!-- Sello Histórico Sutil -->
              <div class="absolute right-6 top-6 w-20 h-20 rounded-full border-2 border-red-800/40 text-red-800/40 flex flex-col items-center justify-center rotate-12 pointer-events-none text-[8px] font-mono leading-none">
                <span>FUNDACIÓN</span>
                <span class="font-bold my-0.5">PATIÑO</span>
                <span>INSPECCIÓN</span>
              </div>

              <!-- Encabezado de la Tarjeta Física -->
              <div class="border-b-2 border-[#78593a] pb-3 mb-4">
                <div class="text-[10px] uppercase tracking-widest text-[#78593a] font-sans font-bold">
                  FUNDACIÓN SIMÓN I. PATIÑO · DEPARTAMENTO DE PATRIMONIO
                </div>
                <div class="text-base font-black tracking-wide text-[#2b1d0c] mt-0.5 uppercase">
                  Ficha de Control y Movimiento de Bienes Históricos
                </div>
                <div class="flex justify-between items-center text-xs mt-1 font-mono text-[#5c442e]">
                  <span>DOC. REF: <strong class="underline">DOC-KDX-1984-042</strong></span>
                  <span>FECHA ALTA: <strong>12 / MAYO / 1984</strong></span>
                </div>
              </div>

              <!-- Contenido Manuscrito Simulado -->
              <div class="space-y-3 text-xs leading-relaxed">
                <div class="flex border-b border-[#e6d8c0] pb-1">
                  <span class="w-32 font-bold font-sans text-[11px] text-[#78593a]">CÓDIGO BIEN:</span>
                  <span class="font-mono font-bold text-sm tracking-wider text-slate-900">PAT-ART-089</span>
                </div>
                <div class="flex border-b border-[#e6d8c0] pb-1">
                  <span class="w-32 font-bold font-sans text-[11px] text-[#78593a]">DENOMINACIÓN:</span>
                  <span class="italic font-semibold text-slate-900">Escultura Bronce "Minero en Reposo"</span>
                </div>
                <div class="flex border-b border-[#e6d8c0] pb-1">
                  <span class="w-32 font-bold font-sans text-[11px] text-[#78593a]">CLASIFICACIÓN:</span>
                  <span>Colecciones y Patrimonio Cultural / Escultura</span>
                </div>
                <div class="flex border-b border-[#e6d8c0] pb-1">
                  <span class="w-32 font-bold font-sans text-[11px] text-[#78593a]">UBICACIÓN INICIAL:</span>
                  <span>Galería de Arte Simón I. Patiño - Salón A</span>
                </div>
                <div class="grid grid-cols-2 gap-4 border-b border-[#e6d8c0] pb-1">
                  <div>
                    <span class="font-bold font-sans text-[11px] text-[#78593a]">CANTIDAD:</span>
                    <span class="ml-2 font-mono font-bold">1 (una pieza)</span>
                  </div>
                  <div>
                    <span class="font-bold font-sans text-[11px] text-[#78593a]">ESTADO:</span>
                    <span class="ml-2 text-emerald-900 font-bold">Activo / Conservación óptima</span>
                  </div>
                </div>
                <div class="pt-1">
                  <span class="block font-bold font-sans text-[11px] text-[#78593a] mb-0.5">NOTAS / ATESTACIÓN:</span>
                  <p class="italic text-[11px] text-[#4a3520] bg-[#f2e7d3] p-2 rounded border border-[#dfceb3]">
                    "Firma original de recepción: M. Salamanca. Buen estado de conservación general. Transferido temporalmente desde el almacén central de Cochabamba."
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Indicador de Zoom al pie -->
        <div class="px-4 py-1.5 bg-slate-900/80 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
          <span>Escala: {{ Math.round(nivelZoom * 100) }}%</span>
          <span>Tip: Usa Invertir Contraste para lectura de firmas y números en lápiz</span>
        </div>
      </div>

      <!-- PANEL DERECHO: FORMULARIO DE VALIDACIÓN HUMANA (HITL) -->
      <div class="lg:col-span-6 p-6 lg:p-8 flex flex-col justify-between bg-white overflow-y-auto">
        <div>
          <!-- Cabecera del Formulario -->
          <div class="flex items-center justify-between pb-4 mb-5 border-b border-slate-200">
            <div>
              <h3 class="text-base font-bold text-slate-900">
                Campos Extraídos por el Motor OCR
              </h3>
              <p class="text-xs text-slate-500 mt-0.5">
                Valida o corrige la información antes de incorporarla al inventario oficial
              </p>
            </div>
            <div class="text-right">
              <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                OCR Confiable
              </span>
            </div>
          </div>

          <!-- Alerta de Validación -->
          <div
            v-if="aprobadoExitoso"
            class="mb-4 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center gap-3 animate-in fade-in"
          >
            <i class="pi pi-check-circle text-lg text-emerald-600"></i>
            <div>
              <strong class="font-bold">¡Activo validado y migrado con éxito!</strong>
              <p class="mt-0.5">El bien histórico se ha incorporado al catálogo activo y al grafo de trazabilidad.</p>
            </div>
          </div>

          <div
            v-if="mensajeAlerta"
            class="mb-4 p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800 flex items-center gap-2"
          >
            <i class="pi pi-exclamation-triangle text-amber-600"></i>
            <span>{{ mensajeAlerta }}</span>
          </div>

          <!-- Formulario Estructurado de Edición -->
          <div class="space-y-4 text-xs">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block font-semibold text-slate-700 mb-1">
                  Código de Documento Legacy
                </label>
                <input
                  v-model="docCodigo"
                  type="text"
                  class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 font-mono focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label class="block font-semibold text-slate-700 mb-1">
                  Código de Activo Generado
                </label>
                <input
                  v-model="activoCodigo"
                  type="text"
                  class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 font-mono font-bold focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label class="block font-semibold text-slate-700 mb-1">
                Nombre / Denominación del Activo
              </label>
              <input
                v-model="activoNombre"
                type="text"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 font-medium focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block font-semibold text-slate-700 mb-1">
                  Categoría Clasificada
                </label>
                <input
                  v-model="categoria"
                  type="text"
                  class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label class="block font-semibold text-slate-700 mb-1">
                  Área / Sede de Asignación
                </label>
                <input
                  v-model="area"
                  type="text"
                  class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>
            </div>

            <div class="grid grid-cols-3 gap-3">
              <div>
                <label class="block font-semibold text-slate-700 mb-1">
                  Cantidad
                </label>
                <input
                  v-model.number="cantidad"
                  type="number"
                  min="1"
                  class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label class="block font-semibold text-slate-700 mb-1">
                  Unidad
                </label>
                <input
                  v-model="unidadMedida"
                  type="text"
                  class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label class="block font-semibold text-slate-700 mb-1">
                  Fecha Documento
                </label>
                <input
                  v-model="fechaDocumento"
                  type="date"
                  class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label class="block font-semibold text-slate-700 mb-1">
                Observaciones y Texto Transcrito del Kardex
              </label>
              <textarea
                v-model="observaciones"
                rows="3"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              ></textarea>
            </div>

            <!-- Casilla de Verificación Humana Requerida -->
            <label class="flex items-start gap-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200 cursor-pointer">
              <input
                v-model="revisado"
                type="checkbox"
                class="mt-0.5 w-4 h-4 rounded text-blue-600 focus:ring-blue-500 cursor-pointer"
              />
              <span class="text-xs text-slate-700">
                Certifico que he cotejado visualmente la tarjeta de Kardex histórica y valido la fidelidad de los datos transcritos.
              </span>
            </label>
          </div>
        </div>

        <!-- Botones de Acción HITL -->
        <div class="mt-6 pt-4 border-t border-slate-200 flex flex-wrap items-center justify-end gap-3">
          <button
            type="button"
            class="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors cursor-pointer"
            @click="emit('cerrar')"
          >
            Cerrar Visor
          </button>
          <button
            type="button"
            class="px-4 py-2 text-xs font-semibold text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-lg transition-colors cursor-pointer"
            @click="mensajeAlerta = 'Marcado para revisión de catalogador experto.'"
          >
            Revisión Secundaria
          </button>
          <button
            type="button"
            class="px-5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm hover:shadow transition-all flex items-center gap-2 cursor-pointer"
            @click="aprobarValidacion"
          >
            <i class="pi pi-check"></i>
            <span>Aprobar y Registrar Activo</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
