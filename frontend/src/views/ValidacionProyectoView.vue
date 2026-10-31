<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
type Tipo = 'DOCUMENTAL' | 'DETECTOR'
interface Cabecera { id: number; tipo: Tipo; version?: number; creada_en: string; creada_por: number; modelo_id: string | null
  semilla: string; referencia_protocolo: string; huella_estudio: string; poblacion: number; seleccionadas: number; alcance: string }
interface Revision { id: number; usuario_id: number; fecha: string; etiqueta: string; motivo: string; referencia: string; segunda_revision?: boolean }
interface Documento { articulo: string; codigo: string; lote_id: number; numero_pagina: number | null; orden_fila: number | null
  fecha: string | null; fecha_documental_texto: string | null; detalle: string; referencia: string | null; area: string | null
  ingresos: number | null; salidas: number | null; saldo_registrado: number | null; ruta_imagen_respaldo: string | null }
interface Fila { id: number; documento: Documento; evidencia_vigente: boolean; revision: Revision | null }
interface Estudio extends Cabecera { puede_etiquetar: boolean; filas: Fila[] }
interface Informe extends Cabecera { estado: string; progreso: { seleccionadas: number; etiquetadas: number; concluyentes: number
  pendientes: number; evidencias_no_vigentes: number; modelo_consistente: boolean; indeterminados_excluidos?: number; denominador_principal?: number }
  metricas: { concordancia_filas: number | null; precision: number | null; recall: number | null; f1: number | null
    matriz: { tp: number; fp: number; fn: number; tn: number } | null } }
const auth = useAuthStore()
const puedeCrear = computed(() => ['Administrador', 'Auditor'].includes(auth.rol ?? ''))
const lista = ref<Cabecera[]>([]), total = ref(0), pagina = ref(1)
const modelos = ref<{ id: string; estado: string; creado_en: string }[]>([])
const estudio = ref<Estudio | null>(null), reporte = ref<Informe | null>(null)
const tipo = ref<Tipo>('DOCUMENTAL'), modeloId = ref(''), tamano = ref(100)
const semilla = ref('validacion-institucional-2026'), protocolo = ref('')
const marco = ref<{ poblacion: number; tamano_documental_sugerido: number | null; filtros: string } | null>(null)
const maxFilas = computed(() => Math.min(5000, marco.value?.poblacion ?? 5000))
const posicion = ref(0), etiqueta = ref(''), motivo = ref(''), referencia = ref(''), independiente = ref(false)
const segundaRevision = ref(false), criterio = ref('')
const ocupada = ref(false), error = ref(''), aviso = ref(''), fotoError = ref(false)
const fila = computed(() => estudio.value?.filas[posicion.value] ?? null)
const criteriosActuales = computed(() => (estudio.value?.version ?? 1) >= 2)
const labelIndeterminado = computed(() => criteriosActuales.value && estudio.value?.tipo === 'DETECTOR' ? 'INDETERMINADO' : 'NO_CONCLUYENTE')
const opciones = computed(() => estudio.value?.tipo === 'DOCUMENTAL'
  ? [{ valor: 'COINCIDE_DOCUMENTO', texto: 'Coincide con el documento' }, { valor: 'DIFERENCIA_DOCUMENTO', texto: 'Hay una diferencia de transcripción' }, { valor: 'NO_CONCLUYENTE', texto: 'No puedo concluir' }]
  : criteriosActuales.value
    ? [{ valor: 'NORMAL', texto: 'Normal: evidencia suficiente y sin inconsistencia verificada' }, { valor: 'ANOMALO', texto: 'Anómalo: inconsistencia documental verificada' }, { valor: 'INDETERMINADO', texto: 'Indeterminado: evidencia insuficiente' }]
    : [{ valor: 'INUSUAL_RELEVANTE', texto: 'Inusual y relevante para revisión' }, { valor: 'LEGITIMO', texto: 'Legítimo según el respaldo' }, { valor: 'ERROR_DOCUMENTAL', texto: 'Error documental: requiere cotejo' }, { valor: 'NO_CONCLUYENTE', texto: 'No puedo concluir' }])
const foto = computed(() => {
  const ruta = fila.value?.documento.ruta_imagen_respaldo?.replace(/\\/g, '/')
  if (!ruta?.startsWith('storage/')) return ''
  return new URL('/' + ruta, new URL(api.defaults.baseURL ?? '/api/v1', window.location.origin)).href
})
let consulta = 0
onUnmounted(() => { consulta++ })
function mensaje(e: any) { return typeof e.response?.data?.detail === 'string' ? e.response.data.detail : 'No se pudo completar la operación. Revisa la conexión y vuelve a intentar.' }
function reiniciar() { etiqueta.value = ''; motivo.value = ''; referencia.value = ''; independiente.value = false; segundaRevision.value = false; criterio.value = ''; fotoError.value = false }
function mover(n: number) { posicion.value = n; reiniciar() }
function porcentaje(n: number | null) { return n === null ? 'Pendiente / no definida' : (n * 100).toFixed(1) + '%' }
function fecha(f: string) { return new Date(f).toLocaleString('es-BO', { timeZone: 'America/La_Paz' }) }
function valor(v: unknown) { return v === null || v === undefined ? 'Sin dato' : String(v) }
async function cargarLista() {
  const r = await api.get('/validacion/estudios', { params: { pagina: pagina.value } })
  lista.value = r.data.filas; total.value = r.data.total
}
let turnoMarco = 0
async function cargarMarco() {
  const turno = ++turnoMarco
  marco.value = null
  if (!puedeCrear.value || (tipo.value === 'DETECTOR' && !modeloId.value)) return
  try {
    const r = await api.get('/validacion/marco', { params: { tipo: tipo.value, modelo_id: tipo.value === 'DETECTOR' ? modeloId.value : undefined } })
    if (turno !== turnoMarco) return
    marco.value = r.data
    if (tipo.value === 'DOCUMENTAL' && r.data.tamano_documental_sugerido) tamano.value = r.data.tamano_documental_sugerido
  } catch (e) { if (turno === turnoMarco) error.value = mensaje(e) }
}
watch([tipo, modeloId], cargarMarco)
async function cargar() {
  ocupada.value = true; error.value = ''
  try {
    await cargarLista()
    if (puedeCrear.value) modelos.value = (await api.get('/analitica/modelos')).data.filas.filter((m: { estado: string }) => m.estado === 'COMPLETADO')
    await cargarMarco()
  } catch (e) { error.value = mensaje(e) }
  finally { ocupada.value = false }
}
async function abrir(id: number) {
  const turno = ++consulta
  ocupada.value = true; error.value = ''; aviso.value = ''; reporte.value = null
  try {
    const r = await api.get('/validacion/estudios/' + id)
    if (turno === consulta) { estudio.value = r.data; posicion.value = 0; reiniciar() }
  } catch (e) { if (turno === consulta) { estudio.value = null; error.value = mensaje(e) } }
  finally { if (turno === consulta) ocupada.value = false }
}
async function crear() {
  if (ocupada.value || !puedeCrear.value) return
  ocupada.value = true; error.value = ''; aviso.value = ''
  try {
    const r = await api.post('/validacion/estudios', { tipo: tipo.value, modelo_id: tipo.value === 'DETECTOR' ? modeloId.value : null,
      tamano: tamano.value, semilla: semilla.value.trim(), referencia_protocolo: protocolo.value.trim() })
    pagina.value = 1; await cargarLista(); await abrir(r.data.id)
    aviso.value = 'Estudio preparado. Las etiquetas están pendientes; otra persona debe realizar el cotejo.'
  } catch (e) { error.value = mensaje(e) }
  finally { ocupada.value = false }
}
async function guardar() {
  if (ocupada.value || !estudio.value?.puede_etiquetar || !fila.value) return
  const id = estudio.value.id, mid = fila.value.id, version = fila.value.revision?.id ?? 0
  ocupada.value = true; error.value = ''; aviso.value = ''
  try {
    const r = await api.post(`/validacion/estudios/${id}/filas/${mid}/etiqueta`, {
      huella_estudio: estudio.value.huella_estudio, revision_esperada: version, etiqueta: etiqueta.value,
      motivo: motivo.value.trim(), referencia: referencia.value.trim(), independiente: independiente.value,
      segunda_revision: segundaRevision.value, criterio: etiqueta.value === 'ANOMALO' ? criterio.value : null })
    fila.value.revision = r.data; reporte.value = null; reiniciar()
    aviso.value = 'Decisión registrada con tu cuenta. Se conserva el historial anterior.'
  } catch (e) { error.value = mensaje(e) }
  finally { ocupada.value = false }
}
async function informar(descargar = false) {
  if (!estudio.value || ocupada.value) return
  ocupada.value = true; error.value = ''
  try {
    const r = await api.get(`/validacion/estudios/${estudio.value.id}/informe.json`)
    reporte.value = r.data
    if (descargar) {
      const url = URL.createObjectURL(new Blob([JSON.stringify(r.data, null, 2)], { type: 'application/json' }))
      const a = document.createElement('a'); a.href = url; a.download = `Validacion_${estudio.value.id}.json`; a.click(); URL.revokeObjectURL(url)
    }
  } catch (e) { error.value = mensaje(e) }
  finally { ocupada.value = false }
}
async function paginar(cambio: number) { pagina.value += cambio; await cargar() }
onMounted(cargar)
</script>

<template>
  <main class="validacion">
    <router-link :to="{ name: 'dashboard' }">← Inicio</router-link>
    <h1>Validación del proyecto</h1>
    <p>Prepara una muestra, coteja la evidencia con otra persona y consulta las métricas de esa muestra.</p>
    <p class="aviso">La transcripción documental y la conclusión del auditor son evaluaciones distintas. Las decisiones HIL anteriores no se incorporan como etiquetas de este estudio.</p>
    <p v-if="error" role="alert" class="error">{{ error }}</p><p v-if="aviso" role="status">{{ aviso }}</p>
    <form v-if="puedeCrear" class="panel" aria-label="Preparar estudio" @submit.prevent="crear">
      <h2>Preparar estudio</h2>
      <div class="controles">
        <label>Qué evaluar<select v-model="tipo"><option value="DOCUMENTAL">Transcripción documental vigente</option><option value="DETECTOR">Detector histórico</option></select></label>
        <label v-if="tipo === 'DETECTOR'">Versión del modelo<select v-model="modeloId" required><option value="" disabled>Seleccionar versión</option><option v-for="m in modelos" :key="m.id" :value="m.id">{{ fecha(m.creado_en) }} · {{ m.id.slice(0,8) }}</option></select></label>
        <label>Filas solicitadas<input v-model.number="tamano" type="number" min="1" :max="maxFilas" required /></label>
        <label>Semilla de selección<input v-model="semilla" maxlength="80" required /></label>
      </div>
      <label>Protocolo y criterios acordados antes de revisar<textarea v-model="protocolo" minlength="10" maxlength="500" required placeholder="Referencia del protocolo, criterios para concluir y responsables del cotejo." /></label>
      <p>Selección aleatoria simple, sin reemplazo y reproducible con la semilla, sin elegir por puntuación. Para el detector solo se utilizan filas reservadas de evaluación. La cantidad solicitada debe caber en la población disponible.</p>
      <p v-if="marco">Marco técnico: {{ marco.poblacion }} movimientos. {{ marco.filtros }} <template v-if="marco.tamano_documental_sugerido">Tamaño documental orientativo: {{ marco.tamano_documental_sugerido }}, con Z = 1,96, p = q = 0,50 y error = 0,05. Confirma el marco y el protocolo con la institución; esta recomendación no fija el tamaño de evaluación del detector.</template></p>
      <button class="btn-primary" :disabled="ocupada">Crear estudio sin etiquetas</button>
    </form>
    <section class="panel" aria-label="Estudios guardados">
      <h2>Estudios guardados</h2><button class="btn-outline" :disabled="ocupada" @click="cargar">Actualizar lista</button>
      <p v-if="!lista.length">Todavía no hay estudios independientes.</p>
      <div class="estudios"><button v-for="e in lista" :key="e.id" class="btn-outline" :disabled="ocupada" @click="abrir(e.id)">#{{ e.id }} · {{ e.tipo === 'DOCUMENTAL' ? 'Documental' : 'Detector' }} · {{ e.seleccionadas }} filas · {{ fecha(e.creada_en) }}</button></div>
      <div v-if="total > 20" class="controles"><button :disabled="ocupada || pagina <= 1" @click="paginar(-1)">Anterior</button><span>Página {{ pagina }}</span><button :disabled="ocupada || pagina * 20 >= total" @click="paginar(1)">Siguiente</button></div>
    </section>
    <template v-if="estudio">
      <section class="panel">
        <h2>Estudio #{{ estudio.id }} · {{ estudio.tipo === 'DOCUMENTAL' ? 'Concordancia documental' : 'Evaluación del detector' }}</h2>
        <p>{{ estudio.seleccionadas }} filas de una población de {{ estudio.poblacion }}. Corte preparado el {{ fecha(estudio.creada_en) }}.</p>
        <p>Protocolo: {{ estudio.referencia_protocolo }}</p>
        <p>{{ estudio.alcance }}</p>
        <p v-if="!criteriosActuales" class="aviso">Este estudio conserva los criterios anteriores. No se reinterpretan sus etiquetas como la evaluación definida en el capítulo I; prepara un estudio nuevo para aplicar ese protocolo.</p>
        <p v-if="!estudio.puede_etiquetar" class="aviso">Puedes consultar este estudio. Las etiquetas corresponden a otra cuenta de Administrador o Auditor, distinta de quien lo preparó y de quien entrenó el modelo.</p>
        <div class="controles"><button class="btn-outline" :disabled="ocupada" @click="informar()">Consultar métricas</button><button class="btn-outline" :disabled="ocupada" @click="informar(true)">Descargar informe</button><button class="btn-outline" :disabled="ocupada" @click="abrir(estudio.id)">Actualizar estudio</button></div>
      </section>
      <section v-if="reporte" class="panel" aria-label="Métricas de la muestra">
        <h2>Métricas de la muestra</h2>
        <p>Conclusiones: {{ reporte.progreso.concluyentes }} / {{ reporte.progreso.seleccionadas }} · Pendientes: {{ reporte.progreso.pendientes }}</p>
        <p v-if="criteriosActuales">Denominador principal: {{ reporte.progreso.denominador_principal ?? 0 }} · Indeterminados excluidos tras segunda revisión: {{ reporte.progreso.indeterminados_excluidos ?? 0 }}.</p>
        <p v-if="reporte.estado === 'SIN_CASOS_EVALUABLES'" class="aviso">La muestra fue revisada, pero no quedaron casos evaluables. Las métricas permanecen no definidas.</p>
        <p v-else-if="reporte.estado !== 'MUESTRA_COMPLETA'" class="aviso">Métricas pendientes hasta revisar toda la muestra, completar la segunda revisión de indeterminados y verificar la evidencia.</p>
        <p v-if="reporte.progreso.evidencias_no_vigentes" role="alert">Hay {{ reporte.progreso.evidencias_no_vigentes }} fotografías ausentes o modificadas respecto al corte.</p>
        <p v-if="!reporte.progreso.modelo_consistente" role="alert">El modelo no coincide con la versión congelada. Revisa su integridad antes de publicar resultados.</p>
        <dl v-if="estudio.tipo === 'DOCUMENTAL'"><dt>Concordancia por fila</dt><dd>{{ porcentaje(reporte.metricas.concordancia_filas) }}</dd></dl>
        <dl v-else class="metricas"><div><dt>Precisión</dt><dd>{{ porcentaje(reporte.metricas.precision) }}</dd></div><div><dt>Recall</dt><dd>{{ porcentaje(reporte.metricas.recall) }}</dd></div><div><dt>F1</dt><dd>{{ porcentaje(reporte.metricas.f1) }}</dd></div></dl>
        <div v-if="reporte.metricas.matriz" class="tabla"><table><caption>Conteos de la muestra · positivo = {{ criteriosActuales ? 'anomalía documental verificada' : 'inusual relevante (criterio anterior)' }}</caption><thead><tr><th>Referencia humana</th><th>Modelo señala</th><th>Modelo no señala</th></tr></thead><tbody><tr><th>{{ criteriosActuales ? 'Anómalo' : 'Inusual relevante' }}</th><td>{{ reporte.metricas.matriz.tp }}</td><td>{{ reporte.metricas.matriz.fn }}</td></tr><tr><th>{{ criteriosActuales ? 'Normal' : 'Legítimo' }}</th><td>{{ reporte.metricas.matriz.fp }}</td><td>{{ reporte.metricas.matriz.tn }}</td></tr></tbody></table></div>
        <p>En los estudios nuevos, los casos que siguen indeterminados después de un segundo cotejo se informan separados del cálculo principal. Una división sin casos válidos permanece no definida; no se convierte en cero. Estos resultados no acreditan aprobación institucional ni fraude.</p>
      </section>
      <section v-if="fila" class="panel" aria-label="Revisión independiente">
        <div class="controles"><button class="btn-outline" :disabled="ocupada || posicion <= 0" @click="mover(posicion - 1)">Fila anterior</button><span>{{ posicion + 1 }} / {{ estudio.filas.length }}</span><button class="btn-outline" :disabled="ocupada || posicion + 1 >= estudio.filas.length" @click="mover(posicion + 1)">Fila siguiente</button></div>
        <h2>{{ fila.documento.articulo }} · #{{ fila.id }}</h2>
        <p>{{ fila.documento.codigo }} · Lote {{ fila.documento.lote_id }} · página {{ valor(fila.documento.numero_pagina) }} · fila {{ valor(fila.documento.orden_fila) }}</p>
        <p v-if="estudio.tipo === 'DETECTOR'">Esta revisión no muestra la puntuación, la predicción ni las decisiones analíticas anteriores. Usa los criterios del protocolo y el respaldo institucional; si no permiten concluir, indícalo.</p>
        <p v-if="!fila.evidencia_vigente" class="aviso">La fotografía falta o cambió. Solo se puede registrar una decisión indeterminada; revisa el corte antes de emitir una conclusión.</p>
        <div class="documento">
          <a v-if="foto && !fotoError" :href="foto" target="_blank" rel="noopener"><img :src="foto" alt="Fotografía del documento seleccionado" @error="fotoError = true" /></a>
          <p v-else>Fotografía no disponible.</p>
          <dl><dt>Fecha del documento</dt><dd>{{ fila.documento.fecha ?? fila.documento.fecha_documental_texto ?? 'Sin fecha completa' }}</dd><dt>Detalle transcrito</dt><dd>{{ fila.documento.detalle }}</dd><dt>Área escrita</dt><dd>{{ valor(fila.documento.area) }}</dd><dt>Referencia transcrita</dt><dd>{{ valor(fila.documento.referencia) }}</dd><dt>Ingresos / salidas / saldo</dt><dd>{{ valor(fila.documento.ingresos) }} / {{ valor(fila.documento.salidas) }} / {{ valor(fila.documento.saldo_registrado) }}</dd></dl>
        </div>
        <p v-if="fila.revision">Última decisión: {{ fila.revision.etiqueta }} · {{ fecha(fila.revision.fecha) }} · cuenta #{{ fila.revision.usuario_id }}. Motivo: {{ fila.revision.motivo }} · Referencia: {{ fila.revision.referencia }}</p>
        <form v-if="estudio.puede_etiquetar" aria-label="Registrar conclusión" @submit.prevent="guardar">
          <label>Conclusión<select v-model="etiqueta" aria-label="Conclusión" required><option value="" disabled>Elegir después del cotejo</option><option v-for="o in opciones" :key="o.valor" :value="o.valor" :disabled="!fila.evidencia_vigente && o.valor !== labelIndeterminado">{{ o.texto }}</option></select></label>
          <label v-if="etiqueta === 'ANOMALO'">Inconsistencia documental verificada<select v-model="criterio" aria-label="Criterio de anomalía" required><option value="" disabled>Seleccionar después del cotejo</option><option value="CANTIDAD">Cantidad</option><option value="FECHA">Fecha</option><option value="TIPO_OPERACION">Tipo de operación</option><option value="AREA">Área involucrada</option><option value="MULTIPLE">Más de un criterio</option></select></label>
          <label>Motivo y evidencia cotejada<textarea v-model="motivo" minlength="10" maxlength="4000" required /></label>
          <label>Referencia del respaldo utilizado<input v-model="referencia" type="text" minlength="3" maxlength="500" required /></label>
          <label class="check"><input v-model="independiente" type="checkbox" required /> Declaro que realicé el cotejo de forma independiente, sin utilizar la puntuación ni copiar una decisión anterior.</label>
          <label v-if="criteriosActuales && fila.revision?.etiqueta === labelIndeterminado" class="check"><input v-model="segundaRevision" type="checkbox" aria-label="Segunda revisión" /> Realicé el segundo cotejo previsto en el protocolo. Si el caso sigue indeterminado, esta revisión permite informarlo por separado del denominador principal.</label>
          <p>Una cuenta distinta y esta declaración no reemplazan el criterio profesional ni la comprobación de independencia del protocolo. No registres una conclusión hipotética.</p>
          <button class="btn-primary" :disabled="ocupada || !etiqueta || !independiente || (etiqueta === 'ANOMALO' && !criterio) || motivo.trim().length < 10 || referencia.trim().length < 3">Registrar decisión</button>
        </form>
      </section>
    </template>
  </main>
</template>

<style scoped>
.validacion { max-width: 1150px; margin: auto; padding: 1.5rem; overflow-wrap: anywhere; }
p, dd { line-height: 1.6; } .panel { background: white; border: 1px solid var(--border-color); border-radius: .6rem; padding: 1.3rem; margin: 1.4rem 0; }
.aviso { padding: .8rem; background: #fff4dc; border-radius: .4rem; } .error { color: #a52727; }
.controles, .estudios { display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; margin: 1rem 0; }
label { display: grid; gap: .4rem; margin: .8rem 0; } input, select, textarea { font: inherit; padding: .6rem; border: 1px solid var(--border-color); border-radius: .3rem; max-width: 100%; box-sizing: border-box; }
textarea { min-height: 85px; width: 100%; } .check { display: flex; align-items: start; gap: .6rem; }
.documento { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1.5rem; } img { max-width: 100%; max-height: 600px; object-fit: contain; }
dt { font-weight: 600; } dd { margin: .3rem 0 1rem; } .metricas { display: flex; gap: 2rem; flex-wrap: wrap; }
.tabla { overflow-x: auto; } table { border-collapse: collapse; width: 100%; text-align: left; } th, td { border: 1px solid var(--border-color); padding: .7rem; } caption { margin: .8rem 0; text-align: left; }
@media (max-width: 700px) { .documento { grid-template-columns: 1fr; } .panel { padding: .9rem; } .controles > label { width: 100%; } }
</style>
