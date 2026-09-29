<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import api from '@/services/api'

const props = defineProps<{ articuloId: number; nombre: string }>()
interface Nodo { name: string; requiere_auditoria?: boolean; tipo?: string }
interface Enlace { source: string; target: string; value: number }
interface Grafo { nodes: Nodo[]; links: Enlace[] }
const central = 'Almacén Central'
const datos = ref<Grafo>({ nodes: [], links: [] })
const cargando = ref(false)
const error = ref('')
const seleccion = ref('')
let solicitud: AbortController | undefined
const formato = (valor: number) => valor.toLocaleString('es-BO')

async function cargar() {
  solicitud?.abort()
  const actual = new AbortController()
  solicitud = actual
  cargando.value = true
  error.value = ''
  seleccion.value = ''
  datos.value = { nodes: [], links: [] }
  try {
    const { data } = await api.get<Grafo>(`/kardex/grafo/${props.articuloId}`, { signal: actual.signal })
    if (actual.signal.aborted) return
    if (!Array.isArray(data.nodes) || !Array.isArray(data.links)) throw new Error('Datos incompletos')
    const nombres = new Set(data.nodes.map(n => n.name))
    if (nombres.size !== data.nodes.length || data.nodes.some(n => typeof n.name !== 'string') ||
        data.links.some(e => !nombres.has(e.source) || !nombres.has(e.target) ||
          !Number.isFinite(e.value) || e.value < 0 || (e.source !== central && e.target !== central))) {
      throw new Error('Datos de flujo inconsistentes')
    }
    datos.value = data
  } catch {
    if (!actual.signal.aborted) error.value = 'No se pudo mostrar el flujo. Puedes reintentar o continuar en otra pestaña.'
  } finally {
    if (solicitud === actual) cargando.value = false
  }
}
watch(() => props.articuloId, cargar, { immediate: true })
onBeforeUnmount(() => solicitud?.abort())

const areas = computed(() => datos.value.nodes.filter(n => n.name !== central).map(n => ({
  ...n,
  entradas: datos.value.links.filter(e => e.source === n.name && e.target === central).reduce((t, e) => t + e.value, 0),
  salidas: datos.value.links.filter(e => e.source === central && e.target === n.name).reduce((t, e) => t + e.value, 0),
})).filter(n => n.entradas + n.salidas > 0).sort((a, b) =>
  b.entradas + b.salidas - a.entradas - a.salidas || a.name.localeCompare(b.name)))
const totales = computed(() => areas.value.reduce((t, n) => ({
  entradas: t.entradas + n.entradas, salidas: t.salidas + n.salidas,
}), { entradas: 0, salidas: 0 }))
const internos = computed(() => datos.value.links.filter(e => e.source === central && e.target === central).reduce((t, e) => t + e.value, 0))
const alto = computed(() => Math.max(380, Math.ceil(areas.value.length / 2) * 96 + 60))
const centroY = computed(() => alto.value / 2)
const posiciones = computed(() => areas.value.map((n, i) => {
  const izquierda = i % 2 === 0
  const cantidad = Math.ceil((areas.value.length - (izquierda ? 0 : 1)) / 2)
  return { ...n, izquierda, x: izquierda ? 24 : 736, y: centroY.value + (Math.floor(i / 2) - (cantidad - 1) / 2) * 96 }
}))
const trazos = computed(() => posiciones.value.flatMap(n => {
  const bordeArea = n.izquierda ? 264 : 736
  const bordeCentro = n.izquierda ? 405 : 595
  return ([['entrada', n.entradas], ['salida', n.salidas]] as const).filter(([, valor]) => valor > 0).map(([tipo, valor]) => {
    const offset = tipo === 'entrada' ? -12 : 12
    const origen = tipo === 'entrada' ? [bordeArea, n.y + offset] : [bordeCentro, centroY.value + offset]
    const destino = tipo === 'entrada' ? [bordeCentro, centroY.value + offset] : [bordeArea, n.y + offset]
    const medioX = (bordeArea + bordeCentro) / 2
    return { area: n.name, tipo, valor, ancho: Math.min(7, 1.5 + Math.log10(valor + 1)),
      d: `M ${origen[0]} ${origen[1]} C ${medioX} ${origen[1]}, ${medioX} ${destino[1]}, ${destino[0]} ${destino[1]}` }
  })
}))
const filas = computed(() => seleccion.value ? areas.value.filter(n => n.name === seleccion.value) : areas.value)
function seleccionar(nombre: string) { seleccion.value = seleccion.value === nombre ? '' : nombre }
function etiqueta(nombre: string) { return nombre.length > 31 ? `${nombre.slice(0, 30)}…` : nombre }
</script>

<template>
  <section class="flujo" aria-label="Flujo de movimientos del artículo">
    <header class="flujo-cabecera">
      <div><span class="sobre-titulo">RECORRIDO DEL ARTÍCULO</span><h3>{{ nombre }}</h3>
        <p>Las flechas muestran hacia dónde se movieron las unidades. Un área puede recibir y devolver artículos.</p></div>
      <button class="actualizar" @click="cargar" :disabled="cargando">↻ Actualizar</button>
    </header>
    <p v-if="cargando" role="status" class="estado">Cargando movimientos…</p>
    <div v-else-if="error" role="alert" class="estado error"><p>{{ error }}</p><button class="actualizar" @click="cargar">Reintentar</button></div>
    <p v-else-if="!areas.length && !internos" class="estado">Este artículo todavía no tiene entradas o salidas para representar.</p>
    <template v-else>
      <div class="metricas">
        <div class="metrica entrada"><span>Entradas al almacén</span><strong>{{ formato(totales.entradas) }}</strong><small>unidades acumuladas</small></div>
        <div class="metrica salida"><span>Salidas del almacén</span><strong>{{ formato(totales.salidas) }}</strong><small>unidades acumuladas</small></div>
        <div class="metrica"><span>Áreas y destinos</span><strong>{{ areas.length }}</strong><small>con movimientos registrados</small></div>
      </div>
      <div class="leyenda"><span class="entrada">→ Entrada al almacén</span><span class="salida">→ Salida del almacén</span><span>◌ Área por revisar</span></div>
      <p class="ayuda">Selecciona un área para destacar sus movimientos. Los valores son flujos acumulados, no el stock actual.</p>
      <div class="lienzo">
        <svg :viewBox="`0 0 1000 ${alto}`" class="mapa" role="img" :aria-label="`Grafo de ${nombre}: ${areas.length} áreas, ${totales.entradas} entradas y ${totales.salidas} salidas`">
          <defs>
            <marker :id="`entrada-${articuloId}`" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L7,3.5 L0,7 Z" fill="#059669"/></marker>
            <marker :id="`salida-${articuloId}`" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L7,3.5 L0,7 Z" fill="#d97706"/></marker>
          </defs>
          <path v-for="t in trazos" :key="`${t.area}-${t.tipo}`" :d="t.d" fill="none"
            :stroke="t.tipo === 'entrada' ? '#059669' : '#d97706'" :stroke-width="t.ancho"
            :opacity="seleccion && seleccion !== t.area ? 0.1 : 0.72"
            :marker-end="`url(#${t.tipo}-${articuloId})`">
            <title>{{ t.area }} · {{ t.tipo === 'entrada' ? 'Entrada al almacén' : 'Salida del almacén' }}: {{ formato(t.valor) }} unidades</title>
          </path>
          <rect x="405" :y="centroY - 52" width="190" height="104" rx="22" fill="#183c4c"/>
          <text x="500" :y="centroY - 10" text-anchor="middle" fill="white" font-size="18" font-weight="700">Almacén Central</text>
          <text x="500" :y="centroY + 16" text-anchor="middle" fill="#c5e1e8" font-size="12">ENTRADAS Y SALIDAS</text>
          <g v-for="n in posiciones" :key="n.name" role="button" tabindex="0" :aria-label="`${n.name}: ${n.entradas} entradas y ${n.salidas} salidas`"
            :aria-pressed="seleccion === n.name" class="nodo" @click="seleccionar(n.name)" @keydown.enter="seleccionar(n.name)" @keydown.space.prevent="seleccionar(n.name)"
            :opacity="seleccion && seleccion !== n.name ? 0.35 : 1">
            <title>{{ n.name }}</title>
            <rect :x="n.x" :y="n.y - 34" width="240" height="68" rx="12" :fill="seleccion === n.name ? '#e6f3f7' : 'white'"
              :stroke="n.requiere_auditoria ? '#d97706' : seleccion === n.name ? '#24748b' : '#cedce2'" :stroke-dasharray="n.requiere_auditoria ? '5 3' : undefined" stroke-width="1.5"/>
            <text :x="n.x + 14" :y="n.y - 8" fill="#213d4b" font-size="12" font-weight="600">{{ etiqueta(n.name) }}</text>
            <text :x="n.x + 14" :y="n.y + 16" fill="#047857" font-size="12">Entra {{ formato(n.entradas) }}</text>
            <text :x="n.x + 133" :y="n.y + 16" fill="#b45309" font-size="12">Sale {{ formato(n.salidas) }}</text>
          </g>
        </svg>
      </div>
      <p v-if="internos" class="ayuda">Movimientos registrados dentro del Almacén Central: {{ formato(internos) }} unidades.</p>
      <div class="detalle-cabecera"><h4>{{ seleccion || 'Detalle por área o destino' }}</h4><button v-if="seleccion" class="actualizar" @click="seleccion = ''">Mostrar todas</button></div>
      <div class="tabla-scroll"><table><thead><tr><th>Área o destino</th><th>Entró al almacén</th><th>Salió del almacén</th></tr></thead>
        <tbody><tr v-for="n in filas" :key="n.name"><td>{{ n.name }} <small v-if="n.requiere_auditoria">· Por revisar</small></td><td class="entrada">{{ formato(n.entradas) }}</td><td class="salida">{{ formato(n.salidas) }}</td></tr></tbody>
      </table></div>
    </template>
  </section>
</template>

<style scoped>
.flujo { border: 1px solid #dce6ea; border-radius: 18px; background: #f8fbfc; overflow: hidden; color: #213d4b; }
.flujo-cabecera { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; padding: 26px; background: white; }
.sobre-titulo { font-size: 11px; letter-spacing: .14em; color: #527889; font-weight: 700; }
h3 { margin: 8px 0; font-size: 21px; } p { line-height: 1.5; } .flujo-cabecera p { margin: 0; font-size: 14px; color: #627987; }
.actualizar { border: 1px solid #b9cdd7; border-radius: 8px; padding: 9px 14px; background: white; color: #245267; cursor: pointer; white-space: nowrap; } .actualizar:disabled { opacity: .5; cursor: wait; }
.metricas { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; padding: 22px 26px 12px; }
.metrica { display: flex; flex-direction: column; gap: 5px; background: white; border: 1px solid #e1e9ed; border-radius: 12px; padding: 18px; } .metrica span { font-size: 13px; } .metrica strong { font-size: 30px; } .metrica small { font-size: 11px; color: #738592; }
.entrada { color: #047857; } .salida { color: #b45309; }
.leyenda { display: flex; flex-wrap: wrap; gap: 20px; padding: 14px 26px 0; font-size: 12px; font-weight: 600; }
.ayuda { margin: 10px 26px; color: #607684; font-size: 12px; }
.lienzo { overflow-x: auto; background-image: radial-gradient(#dce6eb 1px, transparent 1px); background-size: 18px 18px; }
.mapa { display: block; width: 100%; min-width: 780px; } .nodo { cursor: pointer; } .nodo:focus rect { stroke: #2563eb; stroke-width: 3; }
.detalle-cabecera { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 18px 26px 8px; } h4 { margin: 0; font-size: 15px; }
.tabla-scroll { overflow-x: auto; padding: 0 26px 24px; } table { border-collapse: collapse; width: 100%; font-size: 13px; background: white; } th, td { padding: 12px; text-align: right; border-bottom: 1px solid #e2eaee; } th { color: #617b89; font-size: 12px; } th:first-child, td:first-child { text-align: left; } td small { color: #b45309; }
.estado { text-align: center; padding: 55px 24px; color: #607684; } .error { color: #9f3e32; }
@media (max-width: 650px) { .metricas { grid-template-columns: 1fr; } .flujo-cabecera { flex-direction: column; } .metrica strong { font-size: 25px; } }
</style>
