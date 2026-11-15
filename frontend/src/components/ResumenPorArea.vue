<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { ElementDefinition } from 'cytoscape'
import GrafoTrazabilidad from './GrafoTrazabilidad.vue'
import TrazabilidadArticulo from './TrazabilidadArticulo.vue'

interface Area {
  id: number
  nombre: string
  entradas: number
  salidas: number
  custodia_actual: number
  alertas_abiertas: number
}
interface Movimiento {
  id: number
  clase: string
  articulo: string
  articulo_id: number
  fecha_registro: string
  cantidad_transferida: number
  area_origen_id?: number | null
  area_destino_id?: number | null
  documento?: string | null
  estado?: string
}
interface Flujo {
  id: string
  origen: number
  destino: number
  cantidad: number
  movimientos: Movimiento[]
}

const props = defineProps<{ areas: Area[]; movimientos: Movimiento[] }>()
const mapa = computed(() => new Map(props.areas.map(a => [a.id, a])))
const actividad = computed(() => props.areas.filter(a =>
  a.entradas || a.salidas || a.custodia_actual || a.alertas_abiertas))
const areaId = ref<number | ''>('')
const flujoId = ref('')
const detalle = ref<Movimiento | null>(null)
const encabezadoFlujo = ref<HTMLHeadingElement | null>(null)
const pagina = ref(1)
const seleccionada = computed(() => mapa.value.get(Number(areaId.value)))
const flujos = computed(() => {
  const agrupados = new Map<string, Flujo>()
  for (const m of props.movimientos) {
    const origen = m.area_origen_id
    const destino = m.area_destino_id
    if (m.clase !== 'TRANSFERENCIA' || m.estado !== 'ACTIVO' || !origen || !destino
        || !mapa.value.has(origen) || !mapa.value.has(destino)
        || (origen !== areaId.value && destino !== areaId.value)) continue
    const id = `${origen}:${destino}`
    let flujo = agrupados.get(id)
    if (!flujo) {
      flujo = { id, origen, destino, cantidad: 0, movimientos: [] }
      agrupados.set(id, flujo)
    }
    flujo.cantidad += m.cantidad_transferida
    flujo.movimientos.push(m)
  }
  return [...agrupados.values()].sort((a, b) => b.cantidad - a.cantidad || a.id.localeCompare(b.id))
})
const flujo = computed(() => flujos.value.find(f => f.id === flujoId.value))
const elementos = computed<ElementDefinition[]>(() => {
  if (!flujos.value.length) return []
  const nodos = new Set(flujos.value.flatMap(f => [f.origen, f.destino]))
  const maximo = Math.max(1, ...flujos.value.map(f => f.cantidad))
  return [
    ...[...nodos].map(id => ({ data: { id: String(id), label: nombre(id), tipo: 'AREA' } })),
    ...flujos.value.map(f => ({ data: {
      id: f.id, source: String(f.origen), target: String(f.destino), tipo: 'FLUJO',
      label: `${f.cantidad} u.`, grosor: 2 + 5 * f.cantidad / maximo,
    } })),
  ]
})
const numero = new Intl.NumberFormat('es-BO')
function nombre(id: number) { return mapa.value.get(id)?.nombre ?? 'Área no identificada' }
async function abrirFlujo(id: string) {
  flujoId.value = id
  detalle.value = null
  pagina.value = 1
  if (id) {
    await nextTick()
    encabezadoFlujo.value?.focus()
  }
}
watch(areaId, () => abrirFlujo(''))
watch(actividad, areas => {
  if (!areas.some(a => a.id === areaId.value)) areaId.value = areas[0]?.id ?? ''
}, { immediate: true })
</script>

<template>
  <section class="por-area" aria-label="Resumen por área">
    <h2>Por área</h2>
    <p v-if="!seleccionada">La gestión consultada no tiene actividad digital por área ni custodias abiertas.</p>
    <template v-else>
      <label for="area-resumen">Área</label>
      <select id="area-resumen" v-model="areaId">
        <option v-for="a in areas" :key="a.id" :value="a.id">{{ a.nombre }}</option>
      </select>
      <dl class="cifras">
        <div><dt>Unidades recibidas en la gestión</dt><dd>{{ numero.format(seleccionada.entradas) }}</dd></div>
        <div><dt>Unidades enviadas en la gestión</dt><dd>{{ numero.format(seleccionada.salidas) }}</dd></div>
        <div><dt>Unidades actualmente en custodia externa</dt><dd>{{ numero.format(seleccionada.custodia_actual) }}</dd></div>
        <div><dt>Alertas abiertas de la gestión</dt><dd>{{ numero.format(seleccionada.alertas_abiertas) }}</dd></div>
      </dl>
      <p class="nota">Entradas, salidas y traslados muestran el volumen registrado. Las rectificaciones se consultan en el recorrido. La custodia corresponde al estado actual.</p>
      <h3>Traslados entre áreas</h3>
      <p v-if="!flujos.length">No hay traslados internos registrados para esta área en la gestión.</p>
      <template v-else>
        <p>Selecciona una flecha o un flujo de la tabla para consultar los movimientos que lo componen.</p>
        <GrafoTrazabilidad :elementos="elementos" :seleccionado="flujoId" flujos
          @seleccionar-flujo="abrirFlujo" />
        <div class="tabla">
          <table><thead><tr><th>Origen</th><th>Destino</th><th>Unidades</th><th>Traslados</th></tr></thead>
            <tbody><tr v-for="f in flujos" :key="f.id">
              <td>{{ nombre(f.origen) }}</td><td>{{ nombre(f.destino) }}</td><td>{{ numero.format(f.cantidad) }}</td>
              <td><button type="button" :aria-expanded="flujoId === f.id" @click="abrirFlujo(f.id)">{{ f.movimientos.length }} · Ver movimientos</button></td>
            </tr></tbody>
          </table>
        </div>
        <div v-if="flujo" class="movimientos">
          <h4 ref="encabezadoFlujo" tabindex="-1">{{ nombre(flujo.origen) }} → {{ nombre(flujo.destino) }}</h4>
          <div class="tabla"><table><thead><tr><th>Artículo</th><th>Referencia</th><th>Unidades</th><th>Recorrido</th></tr></thead>
            <tbody><tr v-for="m in flujo.movimientos.slice((pagina - 1) * 15, pagina * 15)" :key="m.id">
              <td>{{ m.articulo }}</td><td>{{ m.documento || 'Sin referencia' }}</td><td>{{ m.cantidad_transferida }}</td>
              <td><button type="button" :aria-expanded="detalle?.id === m.id"
                @click="detalle = detalle?.id === m.id ? null : m">{{ detalle?.id === m.id ? 'Ocultar recorrido' : 'Ver recorrido' }}</button></td>
            </tr></tbody>
          </table></div>
          <nav v-if="flujo.movimientos.length > 15" aria-label="Páginas de traslados">
            <button type="button" :disabled="pagina === 1" @click="pagina--; detalle = null">Anterior</button>
            <span>Página {{ pagina }} de {{ Math.ceil(flujo.movimientos.length / 15) }}</span>
            <button type="button" :disabled="pagina * 15 >= flujo.movimientos.length" @click="pagina++; detalle = null">Siguiente</button>
          </nav>
          <TrazabilidadArticulo v-if="detalle" :articulo-id="detalle.articulo_id" :evento="`TRANSFERENCIA:${detalle.id}`" />
        </div>
      </template>
    </template>
  </section>
</template>

<style scoped>
.por-area { background: var(--bg-color, white); margin: 1.5rem 0; padding: 1rem; border: 1px solid var(--border-color); border-radius: 8px; }
select { margin-left: .75rem; }
.cifras { display: grid; gap: .75rem; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }
.cifras div { border: 1px solid var(--border-color); border-radius: 8px; padding: .75rem; }
dd { margin: 0; font-size: 1.4rem; font-weight: 600; }
.nota { color: var(--text-secondary); }
.tabla { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: .5rem; text-align: left; border-bottom: 1px solid var(--border-color); }
button, select { padding: .45rem; color: inherit; background: var(--bg-color, white); border: 1px solid var(--border-color); border-radius: 5px; }
button:not(:disabled) { cursor: pointer; }
nav { display: flex; flex-wrap: wrap; align-items: center; gap: .5rem; margin: .75rem 0; }
@media print { select, button, nav { display: none; } }
</style>
