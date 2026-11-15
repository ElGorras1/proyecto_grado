<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import TrazabilidadArticulo from '@/components/TrazabilidadArticulo.vue'
import RevisionHil from '@/components/RevisionHil.vue'

const AnaliticaView = defineAsyncComponent(() => import('./AnaliticaView.vue'))
const AlertasInventarioView = defineAsyncComponent(() => import('./AlertasInventarioView.vue'))
interface Aviso { tipo: string; origen: string; id: number; articulo_id: number; articulo: string; codigo: string; fecha: string | null; descripcion: string; motivos?: string[]; detecciones?: Deteccion[]; asignado_nombre?: string | null; estado: string; prioridad: string; score: number | null; destino: { path: string; query: Record<string, string | number> } | null }
type Deteccion = 'ISOLATION_FOREST' | 'REGLA_INVENTARIO'
interface Bandeja { total: number; pagina: number; limite: number; conteos: Record<string, number>; conteos_deteccion: Record<Deteccion, number>; gestiones: number[]; filas: Aviso[]; alcance: string }
interface Seguimiento { id: number; articulo_id: number; movimiento_id: number; score: number; umbral: number; estado_revision: string; revision_numero: number; datos_cambiaron: boolean; snapshot: { articulo: string; detalle: string; fecha: string; ingresos: number | null; salidas: number | null; ruta_imagen_respaldo: string | null }; contexto: { indicadores: string[] }; revisiones: { id: number; usuario: string; estado: string; motivo: string }[] }
const auth = useAuthStore(), route = useRoute()
const gestionVigente = new Intl.DateTimeFormat('es-BO', { timeZone: 'America/La_Paz', year: 'numeric' }).format(new Date())
const gestionSolicitada = route.query.gestion
const gestionInicial = route.query.sin_fecha === '1' ? 'SIN_FECHA'
  : typeof gestionSolicitada === 'string' && /^\d{4}$/.test(gestionSolicitada)
      && Number(gestionSolicitada) >= 1900 && Number(gestionSolicitada) <= 9998
    ? gestionSolicitada : gestionVigente
const filtros = ref({ origen: 'TODOS', gestion: gestionInicial, articulo: '', incluir_tratados: false })
const aplicados = ref({ ...filtros.value })
const datos = ref<Bandeja | null>(null), detalle = ref<Seguimiento | null>(null)
const seleccionado = ref<Aviso | null>(null)
const mostrarRecorrido = ref(false)
const encabezadoAviso = ref<HTMLHeadingElement | null>(null)
const movimientoHil = ref<InstanceType<typeof RevisionHil>['$props']['movimiento'] | null>(null)
const cargandoHil = ref(false)
const cargando = ref(false), guardando = ref(false), error = ref(''), mensaje = ref(''), fotoError = ref(false)
const estadoAutomatico = ref<{ configurada: boolean; habilitada: boolean; ultimo_error?: string | null } | null>(null)
const revision = ref({ estado: 'EN_REVISION', etiqueta: 'NO_CONCLUYENTE', motivo: '' })
const puedeRevisar = computed(() => ['Administrador', 'Auditor'].includes(auth.rol ?? ''))
const puedeCorregirHil = computed(() => ['Administrador', 'Operador'].includes(auth.rol ?? ''))
const gestiones = computed(() => [...new Set([
  Number(gestionVigente),
  ...(datos.value?.gestiones ?? []),
  ...[filtros.value.gestion, aplicados.value.gestion].map(Number).filter(g => g > 0),
])].sort((a, b) => b - a))
const detecciones: Record<Deteccion, string> = {
  ISOLATION_FOREST: 'Isolation Forest operativo', REGLA_INVENTARIO: 'Regla de inventario',
}
const nombres: Record<string, string> = { HIL: 'Revisión documental', HISTORICO: 'Aviso del corte histórico', SEGUIMIENTO: 'Análisis automático', OPERATIVO: 'Control de inventario' }
const estados: Record<string, string> = { PENDIENTE: 'Pendiente', EN_REVISION: 'En revisión', REQUIERE_SEGUIMIENTO: 'Requiere seguimiento', SEGUIMIENTO: 'En seguimiento', JUSTIFICADO: 'Justificado', CERRADO: 'Cerrado' }
const cambiosPendientes = computed(() => JSON.stringify(filtros.value) !== JSON.stringify(aplicados.value))
const foto = computed(() => {
  const ruta = detalle.value?.snapshot.ruta_imagen_respaldo?.replace(/\\/g, '/')
  if (!ruta?.startsWith('storage/')) return ''
  return new URL('/' + ruta, new URL(api.defaults.baseURL ?? '/api/v1', window.location.origin).origin).href
})
let consulta = 0, consultaDetalle = 0, desmontado = false
let temporizador: ReturnType<typeof setInterval> | undefined
onUnmounted(() => { desmontado = true; consulta++; consultaDetalle++; clearInterval(temporizador) })
function cerrar() {
  seleccionado.value = null
  detalle.value = null
  mostrarRecorrido.value = false
  movimientoHil.value = null
  cargandoHil.value = false
  consultaDetalle++
}
async function abrirAviso(aviso: Aviso) {
  cerrar()
  seleccionado.value = aviso
  if (aviso.tipo === 'SEGUIMIENTO') await abrir(aviso.id)
  await nextTick()
  if (seleccionado.value === aviso) encabezadoAviso.value?.focus()
}
function actualizarBandeja() { return cargar(datos.value?.pagina ?? 1) }
async function revisarDocumento() {
  const aviso = seleccionado.value
  if (!aviso || aviso.tipo !== 'HIL' || cargandoHil.value) return
  const turno = consultaDetalle
  cargandoHil.value = true
  error.value = ''
  try {
    const { data } = await api.get('/kardex/errores', {
      params: { articulo_id: aviso.articulo_id, movimiento_id: aviso.id },
    })
    if (turno !== consultaDetalle) return
    if (!data[0]) {
      error.value = 'Este movimiento ya no figura entre los avisos documentales.'
      void actualizarBandeja()
      return
    }
    movimientoHil.value = data[0]
  } catch (e) {
    if (turno === consultaDetalle) error.value = fallo(e)
  } finally {
    if (turno === consultaDetalle) cargandoHil.value = false
  }
}
function guardarDocumento() {
  cerrar()
  mensaje.value = 'Revisión documental guardada.'
  void actualizarBandeja()
}
function fallo(e: unknown) { const d = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail; return typeof d === 'string' ? d : 'No se pudo completar la consulta. Puedes volver a intentar.' }
async function cargar(pagina = 1, nuevos = false) {
  const turno = ++consulta
  const f = nuevos ? { ...filtros.value } : { ...aplicados.value }
  if (nuevos) { cerrar(); mensaje.value = '' }
  cargando.value = true; error.value = ''
  try {
    const deteccion = f.origen === 'ISOLATION_FOREST' || f.origen === 'REGLA_INVENTARIO' ? f.origen : undefined
    const { data } = await api.get<Bandeja>('/revisiones/pendientes', { params: {
      origen: deteccion ? 'OPERATIVO' : f.origen, deteccion, gestion: f.gestion && f.gestion !== 'SIN_FECHA' ? Number(f.gestion) : undefined,
      sin_fecha: f.gestion === 'SIN_FECHA', articulo: f.articulo.trim() || undefined, incluir_tratados: f.incluir_tratados, pagina, limite: 30,
    } })
    if (turno !== consulta) return
    datos.value = data; aplicados.value = f
    const ultimaPagina = Math.max(1, Math.ceil(data.total / data.limite))
    if (data.pagina > ultimaPagina) await cargar(ultimaPagina)
  } catch (e) { if (turno === consulta) error.value = fallo(e) }
  finally { if (turno === consulta) cargando.value = false }
}
async function abrir(id: number) {
  const turno = ++consultaDetalle
  detalle.value = null; error.value = ''; mensaje.value = ''; fotoError.value = false
  try {
    const { data } = await api.get<Seguimiento>('/automatizacion/seguimiento/' + id)
    if (turno !== consultaDetalle) return
    detalle.value = data; revision.value = { estado: 'EN_REVISION', etiqueta: 'NO_CONCLUYENTE', motivo: '' }
  } catch (e) { if (turno === consultaDetalle) error.value = fallo(e) }
}
async function guardar() {
  if (!detalle.value || guardando.value || !puedeRevisar.value || detalle.value.datos_cambiaron) return
  const turnoDetalle = consultaDetalle, turnoLista = consulta
  const actual = detalle.value
  guardando.value = true; error.value = ''; mensaje.value = ''
  try {
    const { data } = await api.post<Seguimiento>(`/automatizacion/seguimiento/${actual.id}/revision`, { ...revision.value, motivo: revision.value.motivo.trim(), revision_esperada: actual.revision_numero })
    if (desmontado) return
    if (turnoDetalle === consultaDetalle) {
      detalle.value = data
      mensaje.value = 'Revisión registrada. Las cantidades y el documento original se conservan.'
    }
    if (turnoLista === consulta) await cargar(datos.value?.pagina ?? 1)
  } catch (e) { if (!desmontado && turnoDetalle === consultaDetalle) error.value = fallo(e) }
  finally { if (!desmontado) guardando.value = false }
}
onMounted(async () => {
  temporizador = setInterval(() => {
    if (document.visibilityState === 'visible' && !cargando.value && !guardando.value) {
      void actualizarBandeja()
    }
  }, 60_000)
  await Promise.all([cargar(1, true), api.get('/automatizacion/estado').then(r => { if (!desmontado) estadoAutomatico.value = r.data }).catch(() => {})])
  const id = Number(route.query.seguimiento_id)
  if (!desmontado && Number.isInteger(id) && id > 0) await abrir(id)
})
</script>
<template>
  <main class="revisiones">
    <header><div><h1>Revisiones y alertas</h1><p>Consulta los pendientes y abre la evidencia del artículo para resolverlos.</p></div><button class="btn-outline" :disabled="cargando" @click="cargar()">Actualizar pendientes</button></header>
    <details class="consultas">
      <summary>Consultas de auditoría</summary>
      <p v-if="estadoAutomatico?.configurada && estadoAutomatico.habilitada">El seguimiento histórico revisa automáticamente los cambios del Kárdex.</p>
      <p v-if="estadoAutomatico?.ultimo_error" role="status" class="nota">El último seguimiento histórico necesita atención de mantenimiento.</p>
      <router-link :to="{ name: 'analitica' }">Resultados históricos por gestión</router-link>
      <router-link :to="{ name: 'alertasInventario' }">Historial y filtros de casos operativos</router-link>
      <router-link v-if="puedeRevisar" :to="{ name: 'validacionOperativa' }">Evaluación de operaciones</router-link>
      <router-link v-if="auth.rol === 'Administrador'" :to="{ name: 'analiticaOperativa' }">Estado del modelo para operaciones digitales</router-link>
    </details>
    <form class="filtros" @submit.prevent="cargar(1, true)">
      <label>Origen<select v-model="filtros.origen" aria-label="Origen del aviso">
        <option value="TODOS">Todos</option>
        <option v-for="(nombre, tipo) in detecciones" :key="tipo" :value="tipo">{{ nombre }}</option>
        <option value="HIL">Revisión documental</option>
        <option value="MODELO">Análisis histórico</option>
      </select></label>
      <label>Gestión<select v-model="filtros.gestion" aria-label="Gestión del aviso"><option value="">Todas las gestiones</option><option v-for="g in gestiones" :key="g" :value="String(g)">{{ g }}</option><option value="SIN_FECHA">Sin fecha completa</option></select></label>
      <label>Artículo o código<input v-model="filtros.articulo" aria-label="Artículo de la revisión" type="search" maxlength="150" /></label>
      <label class="check"><input v-model="filtros.incluir_tratados" type="checkbox" /> Incluir avisos documentales ya categorizados</label>
      <button class="btn-primary" :disabled="cargando">Aplicar filtros</button>
    </form>
    <p v-if="cambiosPendientes" role="status">Hay filtros sin aplicar; la lista conserva la consulta anterior.</p>
    <p v-if="cargando" role="status">Consultando pendientes…</p><p v-if="error" role="alert" class="error">{{ error }}</p><p v-if="mensaje" role="status">{{ mensaje }}</p>
    <template v-if="datos">
      <div class="resumen">
        <div v-for="(nombre, tipo) in detecciones" :key="tipo"><strong>{{ datos.conteos_deteccion?.[tipo] ?? 0 }}</strong><span>{{ nombre }}</span></div>
        <div><strong>{{ datos.conteos.HIL ?? 0 }}</strong><span>Documentales</span></div>
        <div><strong>{{ datos.conteos.MODELO ?? 0 }}</strong><span>Del análisis histórico</span></div>
      </div>
      <p>{{ datos.alcance }}</p>
      <div class="tabla" tabindex="0" aria-label="Bandeja de revisiones"><table><thead><tr><th>Origen y prioridad</th><th>Artículo y evidencia</th><th>Fecha</th><th>Estado</th><th>Revisar</th></tr></thead><tbody>
        <tr v-for="f in datos.filas" :key="f.tipo + ':' + f.id">
          <td>
            <strong v-if="!f.detecciones?.length">{{ nombres[f.tipo] }}</strong>
            <strong v-for="tipo in f.detecciones" :key="tipo" class="origen-aviso">{{ detecciones[tipo] }}</strong>
            <small>Prioridad {{ f.prioridad.toLowerCase() }}</small>
          </td>
          <td><strong>{{ f.articulo }}</strong><small>{{ f.codigo }} · {{ f.descripcion }}</small>
            <ul v-if="f.motivos?.length"><li v-for="motivo in f.motivos" :key="motivo">{{ motivo }}</li></ul>
          </td>
          <td>{{ f.fecha || 'Sin fecha completa' }}</td>
          <td>{{ estados[f.estado] ?? f.estado }}<small v-if="f.origen === 'OPERATIVO'">{{ f.asignado_nombre || 'Sin revisor asignado' }}</small></td>
          <td><button type="button" class="btn-outline" :aria-expanded="seleccionado?.tipo === f.tipo && seleccionado.id === f.id" @click="abrirAviso(f)">{{ f.tipo === 'HIL' ? 'Ver documento' : 'Abrir evidencia' }}</button></td>
        </tr>
        <tr v-if="!datos.filas.length && !cargando"><td colspan="5">No hay avisos pendientes para estos filtros.</td></tr>
      </tbody></table></div>
      <div class="paginacion"><button class="btn-outline" :disabled="cargando || datos.pagina <= 1" @click="cargar(datos.pagina - 1)">Anterior</button><span>{{ datos.total }} avisos · Página {{ datos.pagina }} de {{ Math.max(1, Math.ceil(datos.total / datos.limite)) }}</span><button class="btn-outline" :disabled="cargando || datos.pagina * datos.limite >= datos.total" @click="cargar(datos.pagina + 1)">Siguiente</button></div>
    </template>
    <section v-if="seleccionado && seleccionado.tipo !== 'SEGUIMIENTO'" class="detalle" aria-label="Evidencia del aviso seleccionado">
      <header>
        <h2 ref="encabezadoAviso" tabindex="-1">{{ seleccionado.tipo === 'HIL' ? seleccionado.articulo : 'Evidencia del aviso' }}</h2>
        <button type="button" @click="cerrar">Cerrar evidencia</button>
      </header>
      <template v-if="seleccionado.tipo === 'HIL'">
        <button v-if="puedeCorregirHil" type="button" class="btn-outline" :disabled="cargandoHil" @click="revisarDocumento">
          {{ cargandoHil ? 'Abriendo revisión…' : 'Revisar documento' }}
        </button>
        <router-link v-if="seleccionado.destino" :to="seleccionado.destino">Ver revisión documental del artículo</router-link>
        <TrazabilidadArticulo :articulo-id="seleccionado.articulo_id" :evento="`HISTORICO:${seleccionado.id}`" />
      </template>
      <AnaliticaView v-else-if="seleccionado.tipo === 'HISTORICO'" :key="seleccionado.id"
        :resultado-id="seleccionado.id" @revisado="actualizarBandeja" @cerrar="cerrar" />
      <AlertasInventarioView v-else-if="seleccionado.tipo === 'OPERATIVO'" :key="seleccionado.id"
        :caso-id="seleccionado.id" @revisado="actualizarBandeja" />
    </section>
    <RevisionHil v-if="movimientoHil" :key="movimientoHil.id" :movimiento="movimientoHil"
      @cerrar="movimientoHil = null" @guardar="guardarDocumento" />
    <section v-if="detalle" class="detalle" aria-label="Revisión del análisis automático">
      <header><h2 ref="encabezadoAviso" tabindex="-1">{{ detalle.snapshot.articulo }} · movimiento #{{ detalle.movimiento_id }}</h2><button :disabled="guardando" @click="cerrar">Cerrar</button></header>
      <p>Este análisis utiliza el modelo conservado; no modifica sus pesos ni el corte de evaluación.</p>
      <p v-if="detalle.datos_cambiaron" role="alert">La evidencia cambió después del análisis. Revisa el documento y espera al siguiente análisis antes de concluir este aviso.</p>
      <div class="evidencia"><a v-if="foto && !fotoError" :href="foto" target="_blank" rel="noopener"><img :src="foto" alt="Fotografía del documento analizado" @error="fotoError = true" /></a><div><p>{{ detalle.snapshot.fecha }} · {{ detalle.snapshot.detalle }}</p><p>Ingreso: {{ detalle.snapshot.ingresos ?? 'En blanco' }} · Salida: {{ detalle.snapshot.salidas ?? 'En blanco' }}</p><p>Puntuación: {{ detalle.score.toFixed(4) }} · Umbral: {{ detalle.umbral.toFixed(4) }}</p><ul><li v-for="texto in detalle.contexto.indicadores" :key="texto">{{ texto }}</li></ul><router-link :to="{ name: 'kardexDigital', query: { articulo_id: detalle.articulo_id, tab: 'hil' } }">Revisar documento en HIL</router-link> · <button type="button" :aria-expanded="mostrarRecorrido" @click="mostrarRecorrido = !mostrarRecorrido">{{ mostrarRecorrido ? 'Ocultar recorrido' : 'Ver recorrido' }}</button></div></div>
      <TrazabilidadArticulo v-if="mostrarRecorrido" :articulo-id="detalle.articulo_id"
        :evento="`HISTORICO:${detalle.movimiento_id}`" />
      <form v-if="puedeRevisar" class="decision" @submit.prevent="guardar"><label>Estado<select v-model="revision.estado"><option value="EN_REVISION">En revisión</option><option value="JUSTIFICADO">Justificado</option><option value="REQUIERE_SEGUIMIENTO">Requiere seguimiento</option><option value="CERRADO">Cerrado</option></select></label><label>Conclusión<select v-model="revision.etiqueta"><option value="NO_CONCLUYENTE">No concluyente</option><option value="LEGITIMO">Operación legítima</option><option value="INUSUAL_RELEVANTE">Inusual: investigar</option><option value="ERROR_DOCUMENTAL">Error documental: revisar HIL</option></select></label><label>Motivo y evidencia<textarea v-model="revision.motivo" required minlength="10" maxlength="4000" /></label><button class="btn-primary" :disabled="guardando || detalle.datos_cambiaron || revision.motivo.trim().length < 10">Guardar revisión</button></form>
      <h3>Revisiones conservadas</h3><p v-if="!detalle.revisiones.length">Todavía no hay revisiones.</p><article v-for="r in detalle.revisiones" :key="r.id"><strong>{{ r.usuario }} · {{ r.estado }}</strong><p>{{ r.motivo }}</p></article>
    </section>
  </main>
</template>
<style scoped>
.revisiones { max-width: 1250px; margin: auto; padding: 1.5rem 1.25rem; } header,.paginacion { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: .75rem; }
.consultas { margin: 1rem 0; } .consultas summary { cursor: pointer; } .consultas a { display: block; margin: .5rem 0; }
.filtros,.decision { display: flex; flex-wrap: wrap; align-items: end; gap: .85rem; padding: 1rem 0; } label { display: flex; flex-direction: column; gap: .35rem; flex: 1 1 170px; } .check { flex-direction: row; align-items: center; } input,select,textarea { width: 100%; padding: .6rem; border: 1px solid var(--border-color); border-radius: 6px; } .check input { width: auto; }
.resumen { display: flex; flex-wrap: wrap; gap: 1rem; margin: 1rem 0; } .resumen div { padding: 1rem; border: 1px solid var(--border-color); border-radius: 8px; min-width: 130px; } .resumen strong,.resumen span,.origen-aviso,small { display: block; } .resumen strong { font-size: 1.6rem; } small { color: var(--text-secondary); margin-top: .4rem; line-height: 1.5; }
.tabla { overflow-x: auto; } table { width: 100%; border-collapse: collapse; min-width: 700px; } th,td { padding: .8rem; border-bottom: 1px solid var(--border-color); text-align: left; vertical-align: top; } td:nth-child(2) { max-width: 390px; overflow-wrap: anywhere; } .paginacion { margin: 1rem 0; } .error { color: #a12222; } .nota { padding: .8rem; background: #fff5da; }
.detalle { border: 1px solid var(--border-color); border-radius: 8px; padding: 1.25rem; margin-top: 1rem; } .evidencia { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; } img { max-width: 100%; max-height: 600px; object-fit: contain; } .decision textarea { min-height: 100px; }
@media(max-width: 650px) { .evidencia { grid-template-columns: 1fr; } .revisiones { padding: 1rem .75rem; } .resumen div { min-width: 0; flex: 1; padding: .65rem; } }
</style>
