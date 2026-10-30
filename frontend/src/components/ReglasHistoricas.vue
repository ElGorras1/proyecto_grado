<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api from '@/services/api'
import MarcaDocumental from '@/components/MarcaDocumental.vue'

const props = withDefaults(defineProps<{ gestionInicial?: string }>(), { gestionInicial: '' })
interface Aviso { codigo: string; nombre: string; nivel: string; mensaje: string; datos: Record<string, unknown> }
interface RevisionDocumental {
  motivo?: string; criterios?: string[]; hallazgos?: string[]; origen_fecha?: string; origen_saldo?: string;
  saldo_documental?: number | null; diferencia_saldo_documental?: number; diferencia_con_cadena_previa?: number;
  tipo_fila?: string; fecha_documental?: string | null
}
interface Fila {
  id: number; articulo_id: number; articulo: string; codigo: string; fecha: string | null; fecha_estimada: boolean;
  fecha_documental_texto?: string | null; fecha_precision?: string | null
  ingresos: number | null; salidas: number | null; saldo_previo: number | null; base_utilizable: boolean;
  saldo_vigente: number; saldo_esperado_reglas: number | null; movimiento_previo_id: number | null;
  detalle: string; lote_id: number; tanda: number; numero_pagina: number; orden_fila: number;
  ruta_imagen_respaldo: string | null; revision_documental: RevisionDocumental | null;
  avisos: Aviso[]; no_evaluables: { reglas: string[]; motivo: string }[]; observado: boolean
}
interface Politica { version: string; limites: string[]; reglas: {codigo: string; nombre: string}[];
  cantidad_extrema: number; porcentaje_mayoritario: number; factor_atipico: number; min_comparables: number }
interface Resultado { total: number; filas: Fila[]; politica: Politica; resumen: {
  con_avisos: number; evaluacion_parcial: number; consultado_en: string } }
interface Detalle { fila: Fila; vecinos: Fila[]; datos_originales: Record<string, unknown> | null }
interface Filtros { gestion: string; articulo: string; regla: string; seleccion: string }
const filtros = ref<Filtros>({gestion: props.gestionInicial, articulo: '', regla: '', seleccion: 'avisos'})
const aplicados = ref<Filtros | null>(null)
const gestiones = ref<number[]>([])
const politica = ref<Politica | null>(null)
const resultado = ref<Resultado | null>(null)
const pagina = ref(1)
const cargando = ref(false)
const cargandoOpciones = ref(false)
const exportando = ref(false)
const error = ref('')
const detalle = ref<Detalle | null>(null)
const cargandoDetalle = ref(false)
const errorDetalle = ref('')
const fotoError = ref(false)
let solicitudDetalle = 0
const pendientes = computed(() => aplicados.value !== null && JSON.stringify({...filtros.value,
  articulo: filtros.value.articulo.trim()}) !== JSON.stringify(aplicados.value))
const foto = computed(() => {
  const ruta = detalle.value?.fila.ruta_imagen_respaldo?.replace(/\\/g, '/')
  if (!ruta?.startsWith('storage/')) return ''
  return new URL('/' + ruta, new URL(api.defaults.baseURL ?? '/api/v1', window.location.origin).origin).href
})
function parametros(f: Filtros) {
  return {gestion: f.gestion ? Number(f.gestion) : undefined, articulo: f.articulo.trim() || undefined,
    regla: f.regla || undefined, seleccion: f.seleccion}
}
async function consultar(nueva = true, numero = 1) {
  if (cargando.value) return
  const f = nueva || !aplicados.value ? {...filtros.value, articulo: filtros.value.articulo.trim()} : {...aplicados.value}
  cargando.value = true; error.value = ''
  try {
    const {data} = await api.get<Resultado>('/analitica/reglas-historicas', {params: {...parametros(f), pagina: numero, limite: 30}})
    resultado.value = data; politica.value = data.politica; aplicados.value = f; pagina.value = numero
    cerrarDetalle()
  } catch { error.value = 'No se pudieron consultar las reglas históricas. Revisa la conexión y vuelve a consultar.' }
  finally { cargando.value = false }
}
async function inicializar() {
  cargandoOpciones.value = true; error.value = ''
  try {
    const {data} = await api.get<{gestiones: number[]; politica: Politica}>('/analitica/reglas-historicas/opciones')
    gestiones.value = data.gestiones; politica.value = data.politica
    await consultar()
  } catch { error.value = 'No se pudieron cargar las opciones de revisión histórica.' }
  finally { cargandoOpciones.value = false }
}
function limpiar() { filtros.value = {gestion: '', articulo: '', regla: '', seleccion: 'avisos'}; consultar() }
function cerrarDetalle() { solicitudDetalle++; detalle.value = null; cargandoDetalle.value = false; errorDetalle.value = '' }
async function abrir(id: number) {
  const solicitud = ++solicitudDetalle
  detalle.value = null; errorDetalle.value = ''; cargandoDetalle.value = true; fotoError.value = false
  try {
    const {data} = await api.get<Detalle>(`/analitica/reglas-historicas/${id}`)
    if (solicitud === solicitudDetalle) detalle.value = data
  } catch { if (solicitud === solicitudDetalle) errorDetalle.value = 'No se pudo consultar la evidencia de esta fila.' }
  finally { if (solicitud === solicitudDetalle) cargandoDetalle.value = false }
}
async function descargar() {
  if (!aplicados.value || exportando.value) return
  exportando.value = true; error.value = ''
  try {
    const {data} = await api.get('/analitica/reglas-historicas.csv', {params: parametros(aplicados.value), responseType: 'blob'})
    const url = URL.createObjectURL(new Blob([data], {type: 'text/csv;charset=utf-8'}))
    const a = document.createElement('a'); a.href = url
    a.download = `reglas_historicas_${aplicados.value.gestion || 'todas'}.csv`
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url)
  } catch { error.value = 'No se pudo descargar el resultado de las reglas históricas.' }
  finally { exportando.value = false }
}
onMounted(inicializar)
</script>

<template>
  <section class="reglas-panel" aria-label="Reglas sobre gestiones antiguas">
    <header class="reglas-header">
      <div><h2>Reglas sobre gestiones antiguas</h2>
        <p>Consulta el Kárdex histórico por reglas explicables, sin necesitar entrenamiento del modelo.</p></div>
      <button :disabled="!aplicados || cargando || exportando" @click="descargar">{{ exportando ? 'Preparando archivo…' : 'Descargar reglas históricas (CSV)' }}</button>
    </header>
    <form class="reglas-filtros" @submit.prevent="consultar()">
      <label>Gestión para consulta<select v-model="filtros.gestion" aria-label="Gestión de reglas históricas">
        <option value="">Todas las gestiones</option><option v-for="g in gestiones" :key="g" :value="String(g)">{{ g }}</option>
      </select></label>
      <label>Artículo o código<input v-model="filtros.articulo" aria-label="Artículo de reglas históricas" maxlength="150" /></label>
      <label>Regla<select v-model="filtros.regla" aria-label="Regla histórica"><option value="">Todas las reglas</option>
        <option v-for="r in politica?.reglas || []" :key="r.codigo" :value="r.codigo">{{ r.nombre }}</option>
      </select></label>
      <label>Mostrar<select v-model="filtros.seleccion" aria-label="Selección de reglas históricas">
        <option value="avisos">Con avisos</option><option value="todos">Todos los movimientos históricos</option>
        <option value="sin_avisos">Sin avisos de estas reglas</option><option value="insuficiente">Con evaluaciones no disponibles</option>
      </select></label>
      <button :disabled="cargando || cargandoOpciones">{{ cargando ? 'Consultando reglas…' : 'Consultar reglas' }}</button>
      <button type="button" :disabled="cargando || cargandoOpciones" @click="limpiar">Limpiar filtros de reglas</button>
    </form>
    <p v-if="pendientes" role="status">Hay cambios en los filtros de reglas sin aplicar. Pulsa «Consultar reglas»; la descarga usa la última consulta aplicada.</p>
    <p class="reglas-nota">Se usa el saldo de la fila previa del artículo, incluyendo antecedentes de años anteriores. Una base dudosa se indica como no evaluable. Las fechas estimadas no confirman la gestión del hecho. Los avisos necesitan cotejo y no modifican inventario ni fotografías.</p>
    <details v-if="politica"><summary>Reglas y alcance de la evaluación</summary>
      <p>Política {{ politica.version }} · umbrales provisionales: cantidad {{ politica.cantidad_extrema }} u.; salida mayoritaria {{ politica.porcentaje_mayoritario }} %; comparación {{ politica.factor_atipico }} veces la mediana con al menos {{ politica.min_comparables }} antecedentes.</p>
      <ul><li v-for="limite in politica.limites" :key="limite">{{ limite }}</li></ul>
    </details>
    <p v-if="error" role="alert" class="reglas-error">{{ error }}</p>
    <button v-if="error && !resultado" @click="inicializar">Reintentar revisión histórica</button>
    <p v-if="cargando || cargandoOpciones" role="status">Evaluando el histórico disponible…</p>
    <template v-else-if="resultado && !error">
      <p><strong>{{ resultado.total }} movimientos en la consulta</strong> · {{ resultado.resumen.con_avisos }} con avisos · {{ resultado.resumen.evaluacion_parcial }} con alguna evaluación no disponible.</p>
      <p v-if="!resultado.filas.length">No hay movimientos para los filtros de reglas seleccionados.</p>
      <div v-else class="reglas-tabla"><table>
        <thead><tr><th>Fecha para consulta</th><th>Artículo</th><th>Ingreso / salida</th><th>Saldo previo → vigente</th><th>Avisos de reglas</th><th>Evidencia</th></tr></thead>
        <tbody><tr v-for="f in resultado.filas" :key="f.id">
          <td>{{ f.fecha || 'Sin fecha completa' }}<small v-if="f.fecha_documental_texto">Escrito: {{ f.fecha_documental_texto }}</small><small v-if="f.fecha_estimada">Fecha no confirmada</small></td>
          <td>{{ f.articulo }}<small>{{ f.codigo }} · #{{ f.id }} · Tanda {{ f.tanda }}</small></td>
          <td>{{ f.ingresos || 0 }} / {{ f.salidas || 0 }}</td>
          <td>{{ f.saldo_previo ?? 'Desconocido' }} → {{ f.saldo_vigente }}<small v-if="!f.base_utilizable">Base no utilizable para esta evaluación</small></td>
          <td><span v-for="a in f.avisos" :key="a.codigo" class="reglas-aviso" :class="a.nivel">{{ a.nombre }}</span>
            <span v-if="!f.avisos.length">Sin avisos de estas reglas</span><small v-if="f.no_evaluables.length">Evaluación parcial; revisa el detalle</small></td>
          <td><button @click="abrir(f.id)">Ver detalle de reglas</button></td>
        </tr></tbody>
      </table></div>
      <nav v-if="resultado.total" class="reglas-paginacion" aria-label="Páginas de reglas históricas">
        <button :disabled="pagina <= 1 || cargando" @click="consultar(false, pagina-1)">Reglas anteriores</button>
        <span>Página {{ pagina }} de {{ Math.max(1, Math.ceil(resultado.total/30)) }}</span>
        <button :disabled="pagina*30 >= resultado.total || cargando" @click="consultar(false, pagina+1)">Reglas siguientes</button>
      </nav>
    </template>
    <p v-if="cargandoDetalle" role="status">Consultando evidencia documental…</p>
    <p v-if="errorDetalle" role="alert" class="reglas-error">{{ errorDetalle }}</p>
    <section v-if="detalle" class="reglas-detalle" aria-label="Evidencia de reglas históricas">
      <header class="reglas-header"><h3>Movimiento #{{ detalle.fila.id }} · {{ detalle.fila.articulo }}</h3>
        <button @click="cerrarDetalle">Cerrar revisión de reglas</button></header>
      <div class="reglas-evidencia">
        <div><a v-if="foto && !fotoError" :href="foto" target="_blank" rel="noopener"><img :src="foto" alt="Fotografía de la regla histórica" @error="fotoError = true" /></a>
          <p v-else>Fotografía no disponible; se necesita la fuente para confirmar el aviso.</p></div>
        <div>
          <p>{{ detalle.fila.detalle }}</p><p>Tanda {{ detalle.fila.tanda }} · lote {{ detalle.fila.lote_id }} · foto {{ detalle.fila.numero_pagina }} · fila {{ detalle.fila.orden_fila }}</p>
          <p>Saldo previo: {{ detalle.fila.saldo_previo ?? 'desconocido' }} · vigente: {{ detalle.fila.saldo_vigente }} · esperado por reglas: {{ detalle.fila.saldo_esperado_reglas ?? 'no evaluable' }}.</p>
          <p v-if="detalle.fila.observado">El artículo tiene una observación documental.</p>
          <ul><li v-for="a in detalle.fila.avisos" :key="a.codigo"><strong>{{ a.nombre }}:</strong> {{ a.mensaje }}<small>{{ JSON.stringify(a.datos) }}</small></li></ul>
          <p v-if="!detalle.fila.avisos.length">No se dispararon las reglas evaluables. Esto no certifica la calidad integral del movimiento.</p>
          <ul><li v-for="(n, i) in detalle.fila.no_evaluables" :key="i"><strong>Evaluación no disponible:</strong> {{ n.motivo }}</li></ul>
          <MarcaDocumental :revision="detalle.fila.revision_documental" />
          <router-link :to="{path:'/kardex-digital', query:{articulo_id: detalle.fila.articulo_id, tab:'hil'}}">Abrir revisión humana del artículo</router-link>
          <p>Las correcciones se realizan en la revisión HIL y conservan su historial. Esta consulta de reglas no corrige ni borra filas automáticamente.</p>
        </div>
      </div>
      <h4>Filas anteriores y siguientes del documento disponible</h4>
      <div class="reglas-tabla"><table><thead><tr><th>Movimiento</th><th>Fecha</th><th>Lote / foto / fila</th><th>Detalle</th><th>Ingreso / salida</th><th>Saldo vigente</th></tr></thead>
        <tbody><tr v-for="v in detalle.vecinos" :key="v.id" :class="{'regla-seleccionada': v.id === detalle.fila.id}">
          <td>#{{ v.id }}</td><td>{{ v.fecha || 'Sin fecha completa' }}<small v-if="v.fecha_documental_texto">{{ v.fecha_documental_texto }}</small><small v-if="v.fecha_estimada">No confirmada</small></td><td>{{ v.lote_id }} / {{ v.numero_pagina }} / {{ v.orden_fila }}</td>
          <td>{{ v.detalle }}</td><td>{{ v.ingresos || 0 }} / {{ v.salidas || 0 }}</td><td>{{ v.saldo_vigente }}</td>
        </tr></tbody></table></div>
      <details v-if="detalle.datos_originales"><summary>Extracción original conservada</summary><pre>{{ JSON.stringify(detalle.datos_originales, null, 2) }}</pre></details>
    </section>
  </section>
</template>

<style scoped>
.reglas-panel{background:white;border:1px solid #dce6ef;border-radius:14px;padding:1.4rem;margin:1.2rem 0;color:#244967}
.reglas-header{display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;flex-wrap:wrap}.reglas-header h2,.reglas-header h3{margin:.1rem 0}.reglas-header p{margin:.5rem 0}
.reglas-filtros{display:flex;flex-wrap:wrap;align-items:end;gap:.8rem;margin:1rem 0}.reglas-filtros label{display:grid;gap:.4rem;flex:1 1 170px;min-width:0}
input,select{min-width:0;width:100%;padding:.6rem;border:1px solid #cbd9e7;border-radius:7px;box-sizing:border-box}button{background:#416784;color:white;border:0;border-radius:7px;padding:.6rem .85rem;cursor:pointer}button:disabled{opacity:.55;cursor:default}
.reglas-nota{background:#fff7e5;border-left:3px solid #cda14c;padding:.8rem;line-height:1.6}.reglas-error{color:#a93732}.reglas-tabla{overflow:auto;margin:.8rem 0}table{border-collapse:collapse;width:100%;font-size:.86rem}th,td{text-align:left;padding:.8rem;border-bottom:1px solid #e2e9f1;vertical-align:top}th{background:#f4f7fb}small{display:block;font-size:.76rem;margin-top:.3rem;overflow-wrap:anywhere}
.reglas-aviso{display:block;margin:.2rem 0;padding:.25rem .4rem;background:#fff4d9;border-radius:4px}.reglas-aviso.alto{color:#aa3835;background:#ffeded}.reglas-paginacion{display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:1rem;margin-top:1rem}
.reglas-detalle{border-top:2px solid #dbe5ef;padding-top:1rem;margin-top:1rem}.reglas-evidencia{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:1rem;margin:1rem 0}.reglas-evidencia img{max-width:100%;height:auto;border:1px solid #dce6ef}.regla-seleccionada{background:#fff4d9}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.8rem}summary{cursor:pointer;padding:.5rem 0}li{margin:.5rem 0;line-height:1.5}
@media(max-width:750px){.reglas-panel{padding:.85rem}.reglas-evidencia{grid-template-columns:minmax(0,1fr)}.reglas-header button{width:100%}.reglas-filtros label{flex-basis:100%}}
</style>
