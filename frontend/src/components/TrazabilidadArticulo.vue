<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { ElementDefinition } from 'cytoscape'
import api from '@/services/api'
import GrafoTrazabilidad from './GrafoTrazabilidad.vue'

interface Conexion { ubicacion: string; direccion: string; etiqueta: string; certeza: string }
interface Evento {
  clave: string; id: number; clase: string; descripcion: string; fecha: string | null;
  fecha_registro: string | null; cantidad: number; ingreso: number; salida: number;
  documento: string | null; imagen_url: string | null; estado_relacion: string;
  conexiones: Conexion[]; vinculos: { destino: string; tipo: string }[];
  encargado?: string | null; registrador?: string | null; receptor?: string | null;
  devuelto_por?: string | null; motivo_correccion?: string | null; observaciones?: string | null;
  cantidad_anterior?: number | null; cantidad_corregida?: number | null;
  saldo_institucional?: number; saldo_documental?: number;
  lote_id?: number; tanda?: number; pagina?: number; fila?: number;
  fecha_estado?: string; area_estado?: string; referencia_estado?: string;
  area_documental?: string | null; asignacion_area?: { area: string; motivo: string } | null;
  fecha_documental_texto?: string | null; fecha_precision?: string | null; fecha_consulta_tecnica?: string | null;
  afecta_stock_actual: boolean; estado: string;
  alertas_control?: { codigo: string; mensaje: string }[] | null;
  justificacion_alertas?: string | null;
}
interface Datos {
  eventos: Evento[]; contexto: Evento[]; total: number; pendientes: number;
  nodes: { id: string; label: string; tipo: string; clave?: string; contexto?: boolean }[];
  links: { id: string; source: string; target: string; label: string; certeza: string; tipo: string }[];
  ubicaciones: { id: string; label: string }[]; criterio: string; avisos: string[];
  integridad_libro: boolean | null;
}
const props = withDefaults(defineProps<{ articuloId: number; ambitoInicial?: string }>(), { ambitoInicial: 'TODOS' })
const filtros = ref({ ambito: props.ambitoInicial, desde: '', hasta: '', ubicacion: '', tanda: '', relacion: '', sin_fecha: '' })
watch(() => filtros.value.sin_fecha, valor => {
  if (valor) { filtros.value.desde = ''; filtros.value.hasta = '' }
})
const tandas = ref([1, 2, 3])
onMounted(async () => {
  try {
    const resumen = (await api.get('/kardex/tandas')).data
    if (Array.isArray(resumen.tandas)) tandas.value = resumen.tandas.map((t: { id: number }) => t.id)
  } catch { /* Los filtros disponibles conservan su último valor. */ }
})
const datos = ref<Datos | null>(null)
const cargando = ref(false)
const error = ref('')
const seleccionado = ref<string | null>(null)
const imagen = ref<string | null>(null)
const errorImagen = ref(false)
const offset = ref(0)
const limite = 30
let controlador: AbortController | null = null
const detalle = computed(() => [...(datos.value?.eventos ?? []), ...(datos.value?.contexto ?? [])]
  .find(e => e.clave === seleccionado.value))
const elementos = computed<ElementDefinition[]>(() => datos.value ? [
  ...datos.value.nodes.map(data => ({ data })), ...datos.value.links.map(data => ({ data })),
] : [])
const urlImagen = computed(() => imagen.value ? new URL(imagen.value,
  new URL(api.defaults?.baseURL ?? '/api/v1', window.location.origin).origin).href : '')
function fecha(valor: string | null | undefined) {
  if (!valor) return 'No registrada'
  if (valor.length === 10) return valor
  return new Date(valor).toLocaleString('es-BO', { timeZone: 'America/La_Paz' })
}
function etiqueta(id: string) { return datos.value?.ubicaciones.find(u => u.id === id)?.label ?? id }
function seleccionar(clave: string) { seleccionado.value = clave; imagen.value = null }
async function cargar(reiniciar = false) {
  controlador?.abort()
  const actual = new AbortController()
  controlador = actual
  if (reiniciar) offset.value = 0
  datos.value = null; seleccionado.value = null; imagen.value = null; error.value = ''
  if (filtros.value.desde && filtros.value.hasta && filtros.value.desde > filtros.value.hasta) {
    cargando.value = false; error.value = 'Revisa el intervalo de fechas.'; return
  }
  cargando.value = true
  try {
    const params = Object.fromEntries(Object.entries(filtros.value).filter(([, valor]) => valor !== ''))
    if (params.ambito !== 'HISTORICO') delete params.tanda
    const respuesta = await api.get(`/kardex/articulos/${props.articuloId}/trazabilidad`, {
      params: { ...params, offset: offset.value, limite }, signal: actual.signal,
    })
    if (actual.signal.aborted) return
    const d = respuesta.data as Datos
    if (!Array.isArray(d.eventos) || !Array.isArray(d.nodes) || !Array.isArray(d.links) || !Array.isArray(d.contexto))
      throw new Error('Respuesta incompleta')
    datos.value = d
    seleccionado.value = d.eventos[0]?.clave ?? null
  } catch {
    if (!actual.signal.aborted) error.value = 'No se pudo consultar la trazabilidad. Vuelve a intentar.'
  } finally { if (!actual.signal.aborted) cargando.value = false }
}
function pagina(delta: number) { offset.value = Math.max(0, offset.value + delta * limite); cargar() }
function verImagen(ruta: string) { errorImagen.value = false; imagen.value = ruta }
watch(() => props.articuloId, () => { filtros.value = { ambito: props.ambitoInicial, desde: '', hasta: '', ubicacion: '', tanda: '', relacion: '', sin_fecha: '' }; cargar(true) }, { immediate: true })
onBeforeUnmount(() => controlador?.abort())
</script>

<template>
  <section class="trazabilidad" aria-label="Trazabilidad por artículo">
    <h3>Trazabilidad por artículo</h3>
    <p>Selecciona un evento para consultar sus ubicaciones, vínculos y respaldo. El Kárdex escaneado conserva el registro de auditoría.</p>
    <form class="filtros" @submit.prevent="cargar(true)">
      <label>Fechas<select v-model="filtros.sin_fecha" aria-label="Fechas de trazabilidad"><option value="">Todas</option><option value="true">Sin fecha confirmada</option></select></label>
      <label>Registros<select v-model="filtros.ambito" aria-label="Ámbito de trazabilidad"><option value="TODOS">Histórico y operativo</option><option value="HISTORICO">Kárdex escaneado</option><option value="OPERATIVO">Inventario vivo y antecedentes</option></select></label>
      <label>Desde<input v-model="filtros.desde" aria-label="Fecha desde" type="date" :disabled="!!filtros.sin_fecha" /></label>
      <label>Hasta<input v-model="filtros.hasta" aria-label="Fecha hasta" type="date" :disabled="!!filtros.sin_fecha" /></label>
      <label>Área o referencia<select v-model="filtros.ubicacion" aria-label="Ubicación de trazabilidad"><option value="">Todas</option><option v-for="u in datos?.ubicaciones ?? []" :key="u.id" :value="u.id">{{ u.label }}</option></select></label>
      <label v-if="filtros.ambito === 'HISTORICO'">Tanda<select v-model="filtros.tanda" aria-label="Tanda de trazabilidad"><option value="">Todas</option><option v-for="n in tandas" :key="n" :value="String(n)">Tanda {{ n }}</option></select></label>
      <label>Ubicación del evento<select v-model="filtros.relacion" aria-label="Confirmación de relación"><option value="">Todos</option><option value="CONFIRMADA">Confirmada en el registro</option><option value="PENDIENTE">Con datos por confirmar</option></select></label>
      <button type="submit" :disabled="cargando">Consultar</button>
    </form>
    <p v-if="cargando" role="status">Consultando trazabilidad…</p>
    <p v-else-if="error" role="alert">{{ error }} <button @click="cargar()">Reintentar</button></p>
    <template v-else-if="datos">
      <p>{{ datos.total }} eventos en esta consulta · {{ datos.pendientes }} con datos de ubicación por confirmar.</p>
      <p v-if="datos.integridad_libro === false" role="alert">El libro operativo no coincide con el saldo vigente. Solicita revisión.</p>
      <p class="criterio">{{ datos.criterio }}</p>
      <p class="leyenda">Línea continua: relación explícita registrada o revisada. Línea discontinua: dato pendiente o clasificación automática. Línea violeta: devolución, rectificación o respaldo de origen. El saldo documental no representa un almacén físico.</p>
      <p v-for="aviso in datos.avisos" :key="aviso" role="alert">{{ aviso }}</p>
      <p v-if="!datos.eventos.length">No hay eventos que coincidan con estos filtros.</p>
      <template v-else>
        <GrafoTrazabilidad :elementos="elementos" :seleccionado="seleccionado" @seleccionar="seleccionar" />
        <p v-if="datos.contexto.length" class="criterio">{{ datos.contexto.length }} respaldo(s) de origen fuera de esta página o filtro se muestran en gris para conservar el vínculo.</p>
        <div class="navegacion"><button :disabled="offset === 0" @click="pagina(-1)">Anterior</button><span>{{ offset + 1 }}–{{ offset + datos.eventos.length }} de {{ datos.total }}</span><button :disabled="offset + limite >= datos.total" @click="pagina(1)">Siguiente</button></div>
        <div class="paneles">
          <div class="lista" aria-label="Eventos de trazabilidad">
            <button v-for="e in datos.eventos" :key="e.clave" :class="{ activo: seleccionado === e.clave }" @click="seleccionar(e.clave)">
              <strong>{{ e.clase }} #{{ e.id }} · {{ e.cantidad }} u.</strong><span>{{ fecha(e.fecha) }} · {{ e.descripcion }}</span>
            </button>
          </div>
          <article v-if="detalle" class="detalle" aria-label="Detalle de trazabilidad">
            <h4>{{ detalle.clase }} #{{ detalle.id }}</h4>
            <p>{{ detalle.descripcion }}</p>
            <p v-if="detalle.asignacion_area"><strong>Área inferida: {{ detalle.asignacion_area.area }}.</strong>
              Lectura conservada: {{ detalle.area_documental || 'Sin texto' }}. {{ detalle.asignacion_area.motivo }}</p>
            <p>Fecha del evento: {{ fecha(detalle.fecha) }}<span v-if="detalle.fecha_estado"> · {{ detalle.fecha_estado }}</span></p>
            <p v-if="detalle.fecha_documental_texto">Fecha escrita: {{ detalle.fecha_documental_texto }}</p>
            <p v-if="detalle.fecha_consulta_tecnica">Fecha técnica conservada: {{ detalle.fecha_consulta_tecnica }}. No acredita la fecha del hecho.</p>
            <p>Registro: {{ fecha(detalle.fecha_registro) }} · Estado: {{ detalle.estado }}</p>
            <p>Cantidad registrada: {{ detalle.cantidad }} u. · Ingreso: {{ detalle.ingreso }} · Salida: {{ detalle.salida }}</p>
            <p v-if="detalle.clase === 'BASE'">Base fijada para el inventario vivo.</p>
            <p v-else-if="!detalle.afecta_stock_actual">Este evento no modifica el total institucional vigente.</p>
            <p v-if="detalle.saldo_documental !== undefined">Saldo documental: {{ detalle.saldo_documental }} u.</p>
            <p v-if="detalle.saldo_institucional !== undefined">Saldo institucional después del registro: {{ detalle.saldo_institucional }} u. (libro completo)</p>
            <ul><li v-for="c in detalle.conexiones" :key="`${c.ubicacion}-${c.direccion}`">{{ c.etiqueta }}: {{ etiqueta(c.ubicacion) }} · {{ c.certeza === 'CONFIRMADA' ? 'Registrado o revisado' : 'Pendiente de confirmar' }}</li></ul>
            <p v-if="detalle.encargado">Encargado: {{ detalle.encargado }}</p><p v-if="detalle.registrador">Registrado por: {{ detalle.registrador }}</p>
            <p v-if="detalle.receptor">Receptor: {{ detalle.receptor }}</p><p v-if="detalle.devuelto_por">Devuelve: {{ detalle.devuelto_por }}</p>
            <p v-if="detalle.cantidad_corregida !== undefined && detalle.cantidad_corregida !== null">Cantidad rectificada: {{ detalle.cantidad_anterior }} → {{ detalle.cantidad_corregida }} u.</p>
            <p v-if="detalle.motivo_correccion">Motivo: {{ detalle.motivo_correccion }}</p><p v-if="detalle.observaciones">{{ detalle.observaciones }}</p>
            <p>Documento: {{ detalle.documento || 'Sin referencia registrada' }}<span v-if="detalle.referencia_estado"> · {{ detalle.referencia_estado }}</span></p>
            <p v-for="a in detalle.alertas_control || []" :key="a.codigo">Aviso registrado: {{ a.mensaje }}</p>
            <p v-if="detalle.justificacion_alertas">Justificación de los avisos: {{ detalle.justificacion_alertas }}</p>
            <p v-if="detalle.lote_id">Tanda {{ detalle.tanda }} · Lote #{{ detalle.lote_id }} · Página {{ detalle.pagina ?? 'sin indicar' }} · Fila {{ detalle.fila ?? 'sin indicar' }}</p>
            <button v-if="detalle.imagen_url" @click="verImagen(detalle.imagen_url)">Abrir foto del Kárdex</button>
            <p v-else class="criterio">Sin imagen adjunta a este registro. La referencia permite localizar el documento físico.</p>
            <div v-for="v in detalle.vinculos" :key="`${v.tipo}-${v.destino}`" class="vinculo">
              <button v-if="[...datos.eventos, ...datos.contexto].some(e => e.clave === v.destino)" @click="seleccionar(v.destino)">{{ v.tipo }} · {{ v.destino }}</button>
              <span v-else>{{ v.tipo }} · {{ v.destino }} (no disponible)</span>
            </div>
          </article>
        </div>
      </template>
    </template>
    <div v-if="imagen" class="visor" role="dialog" aria-modal="true" aria-label="Evidencia del Kárdex" @keydown.esc="imagen = null" @click.self="imagen = null">
      <div><button autofocus @click="imagen = null">Cerrar foto</button><p v-if="errorImagen" role="alert">No se pudo abrir la imagen de respaldo.</p><img v-else :src="urlImagen" alt="Página escaneada del Kárdex del evento seleccionado" @error="errorImagen = true" /></div>
    </div>
  </section>
</template>

<style scoped>
.trazabilidad { margin-top: 1rem; padding: 1rem; border: 1px solid #cbd5e1; border-radius: 10px; background: var(--bg-color, white); }
.filtros { display: flex; gap: .7rem; flex-wrap: wrap; align-items: end; margin: 1rem 0; }
label { display: grid; gap: .3rem; font-size: .85rem; }
input, select, button { padding: .5rem; border: 1px solid #cbd5e1; border-radius: 5px; background: var(--bg-color, white); color: inherit; }
select { max-width: 250px; }
button { cursor: pointer; } button:disabled { opacity: .5; cursor: default; }
.criterio, .leyenda { color: var(--text-secondary, #475569); font-size: .85rem; }
.paneles { display: grid; grid-template-columns: minmax(180px, 1fr) minmax(240px, 2fr); gap: 1rem; }
.lista { max-height: 580px; overflow-y: auto; display: flex; flex-direction: column; gap: .4rem; }
.lista button { display: block !important; text-align: left; width: 100%; border: 1px solid #cbd5e1 !important; } .lista strong, .lista span { display: block; } .lista span { margin-top: .3rem; font-size: .85rem; }
.lista button.activo { border: 2px solid #0f766e !important; }
.detalle { border: 1px solid #cbd5e1; border-radius: 7px; padding: 1rem; overflow-wrap: anywhere; }
.detalle p { margin: .6rem 0; } .vinculo { margin-top: .5rem; }
.navegacion { display: flex; gap: 1rem; justify-content: center; align-items: center; margin: 1rem 0; }
.visor { position: fixed; inset: 0; z-index: 1000; background: #000b; display: grid; place-items: center; padding: 1rem; }
.visor > div { max-height: 94vh; max-width: 95vw; overflow: auto; background: white; padding: 1rem; border-radius: 8px; }
.visor button { display: block; position: sticky; top: 0; }.visor img { max-width: 100%; }
@media (max-width: 700px) { .paneles { grid-template-columns: 1fr; }.lista { max-height: 220px; } }
</style>
