<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

interface Revision {
  resultado: 'COINCIDE_DOCUMENTO' | 'DIFERENCIA_DOCUMENTO'
  motivo: string
  revisor: string
  fecha: string
  vigente: boolean
}
interface Fila {
  id: number
  articulo_id?: number
  articulo_nombre?: string
  tanda?: number
  fecha_movimiento?: string
  detalle?: string
  ingresos?: number | null
  salidas?: number | null
  saldo_registrado?: number
  tipos_alerta?: string[]
  ruta_imagen_respaldo?: string | null
  datos_originales?: Record<string, unknown> | null
  huella_actual?: string
  revision?: Revision | null
  no_disponible?: boolean
}
interface Muestra {
  id: number
  creada_en: string
  tanda: number | null
  semilla: string
  elegibles: number
  ids: number[]
  resumen: { sin_revisar: number; coinciden: number; diferencias: number; desactualizadas: number }
  filas: Fila[]
}
interface MuestraBreve { id: number; creada_en: string; creada_por: string; ids: number[]; tanda: number | null }

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const puedeValidar = computed(() => auth.rol === 'Administrador' || auth.rol === 'Auditor')
const muestras = ref<MuestraBreve[]>([])
const muestra = ref<Muestra | null>(null)
const tanda = ref('todas')
const tandas = ref([1, 2, 3])
const tamano = ref(30)
const semilla = ref('revision-institucional')
const motivos = ref<Record<number, string>>({})
const ocupada = ref(false)
const error = ref('')
const aviso = ref('')

function mensajeError(e: any, alternativa: string): string {
  return typeof e.response?.data?.detail === 'string' ? e.response.data.detail : alternativa
}
function fecha(value: string): string {
  return new Intl.DateTimeFormat('es-BO', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'America/La_Paz' }).format(new Date(value))
}
function foto(fila: Fila): string {
  if (!fila.ruta_imagen_respaldo) return ''
  const base = new URL(api.defaults.baseURL ?? '/api/v1', window.location.origin)
  return new URL('/' + fila.ruta_imagen_respaldo.replace(/\\/g, '/'), base.origin).href
}
async function cargarMuestras() {
  muestras.value = (await api.get('/kardex/muestras-validacion')).data
}
async function abrir(id: number) {
  error.value = ''
  try {
    muestra.value = (await api.get(`/kardex/muestras-validacion/${id}`)).data
    if (route.query.muestra !== String(id)) await router.replace({ query: { muestra: String(id) } })
  } catch (e) { error.value = mensajeError(e, 'No se pudo abrir la muestra.') }
}
async function crear() {
  if (!puedeValidar.value || ocupada.value) return
  ocupada.value = true; error.value = ''; aviso.value = ''
  try {
    const { data } = await api.post('/kardex/muestras-validacion', {
      tanda: tanda.value === 'todas' ? null : Number(tanda.value),
      tamano: tamano.value, semilla: semilla.value.trim()
    })
    await cargarMuestras()
    const resumen = (await api.get('/kardex/tandas')).data
    if (Array.isArray(resumen.tandas)) tandas.value = resumen.tandas.map((t: { id: number }) => t.id)
    await abrir(data.id)
    aviso.value = `Muestra #${data.id} creada con ${data.ids.length} filas. Aún no hay decisiones humanas.`
  } catch (e) { error.value = mensajeError(e, 'No se pudo crear la muestra.') }
  finally { ocupada.value = false }
}
async function revisar(fila: Fila, resultado: Revision['resultado']) {
  if (!muestra.value || !puedeValidar.value || ocupada.value) return
  const motivo = (motivos.value[fila.id] || '').trim()
  if (motivo.length < 10) { error.value = 'Describe lo que comprobaste en la fotografía con al menos 10 caracteres.'; return }
  ocupada.value = true; error.value = ''; aviso.value = ''
  try {
    await api.post(`/kardex/muestras-validacion/${muestra.value.id}/movimientos/${fila.id}/revision`, {
      resultado, motivo, huella_fila: fila.huella_actual
    })
    await abrir(muestra.value.id)
    motivos.value[fila.id] = ''
    aviso.value = `Decisión sobre la fila #${fila.id} registrada con tu usuario.`
  } catch (e) { error.value = mensajeError(e, 'No se pudo guardar la revisión.') }
  finally { ocupada.value = false }
}
onMounted(async () => {
  try {
    await cargarMuestras()
    const id = Number(route.query.muestra) || muestras.value[0]?.id
    if (id) await abrir(id)
  } catch (e) { error.value = mensajeError(e, 'No se pudieron cargar las muestras.') }
})
</script>

<template>
  <main class="muestra-view">
    <router-link to="/kardex-digital">← Volver al Kárdex</router-link>
    <h1>Validación humana de la muestra migrada</h1>
    <p>Compara cada fila con su fotografía. «Coincide» confirma la fidelidad de la transcripción, no certifica el saldo físico ni descarta anomalías del documento.</p>
    <p v-if="error" class="mensaje error" role="alert">{{ error }}</p>
    <p v-if="aviso" class="mensaje exito" role="status">{{ aviso }}</p>

    <section v-if="puedeValidar" class="panel">
      <h2>Crear un corte de revisión</h2>
      <div class="controles">
        <label>Tanda <select v-model="tanda"><option value="todas">Todas</option><option v-for="n in tandas" :key="n" :value="String(n)">Tanda {{ n }}</option></select></label>
        <label>Filas <input v-model.number="tamano" type="number" min="1" max="100" /></label>
        <label>Semilla <input v-model="semilla" maxlength="80" /></label>
        <button :disabled="ocupada || tamano < 1 || tamano > 100 || !semilla.trim()" @click="crear">Crear muestra</button>
      </div>
      <small>La selección queda congelada. Se distribuye entre tandas y filas con y sin alertas cuando existen en el archivo.</small>
    </section>

    <section class="panel">
      <label>Muestra guardada
        <select :value="muestra?.id ?? ''" @change="abrir(Number(($event.target as HTMLSelectElement).value))">
          <option value="" disabled>Seleccionar</option>
          <option v-for="item in muestras" :key="item.id" :value="item.id">#{{ item.id }} · {{ fecha(item.creada_en) }} · {{ item.ids.length }} filas · {{ item.creada_por }}</option>
        </select>
      </label>
      <p v-if="!muestras.length">Todavía no hay muestras. Un Administrador o Auditor puede crear la primera.</p>
    </section>

    <template v-if="muestra">
      <section class="panel">
        <h2>Muestra #{{ muestra.id }}</h2>
        <p>Corte: {{ fecha(muestra.creada_en) }} · {{ muestra.ids.length }} de {{ muestra.elegibles }} filas elegibles · {{ muestra.tanda ? `Tanda ${muestra.tanda}` : 'Todas las tandas' }} · semilla {{ muestra.semilla }}</p>
        <div class="resumen"><span>Sin revisar: {{ muestra.resumen.sin_revisar }}</span><span>Coinciden: {{ muestra.resumen.coinciden }}</span><span>Diferencias: {{ muestra.resumen.diferencias }}</span><span>Revisar de nuevo: {{ muestra.resumen.desactualizadas }}</span></div>
      </section>

      <article v-for="fila in muestra.filas" :key="fila.id" class="panel fila">
        <div v-if="fila.no_disponible">La fila #{{ fila.id }} ya no está disponible. Conserva el corte y consulta la auditoría.</div>
        <template v-else>
          <header><h3>{{ fila.articulo_nombre }} · fila #{{ fila.id }}</h3><span>Tanda {{ fila.tanda }}</span></header>
          <p>{{ fila.fecha_movimiento || 'Sin fecha completa' }} · {{ fila.detalle }} · ingreso {{ fila.ingresos ?? '—' }} · salida {{ fila.salidas ?? '—' }} · saldo escrito {{ fila.saldo_registrado }}</p>
          <p v-if="fila.tipos_alerta?.length" class="alerta">Alertas existentes: {{ fila.tipos_alerta.join(', ') }}. Verifica el papel y deja la anomalía documentada si realmente aparece allí.</p>
          <p v-if="fila.revision" :class="fila.revision.vigente ? 'decision' : 'alerta'">{{ fila.revision.vigente ? (fila.revision.resultado === 'COINCIDE_DOCUMENTO' ? 'Coincide con el documento' : 'Diferencia documental') : 'Decisión desactualizada: la fila cambió' }} · {{ fila.revision.revisor }} · {{ fecha(fila.revision.fecha) }} · {{ fila.revision.motivo }}</p>
          <details>
            <summary>Ver fotografía y datos originales</summary>
            <a v-if="foto(fila)" :href="foto(fila)" target="_blank" rel="noopener">Abrir fotografía completa ↗</a>
            <img v-if="foto(fila)" :src="foto(fila)" :alt="`Fotografía del Kárdex para la fila ${fila.id}`" />
            <p v-else>La fotografía no está disponible.</p>
            <pre v-if="fila.datos_originales">{{ fila.datos_originales }}</pre>
          </details>
          <div v-if="puedeValidar" class="decision-form">
            <label :for="`motivo-${fila.id}`">Qué comprobaste en el documento</label>
            <textarea :id="`motivo-${fila.id}`" v-model="motivos[fila.id]" rows="2" maxlength="1000" placeholder="Describe la comparación de fecha, cantidad, saldo y detalle…" />
            <div><button :disabled="ocupada || !foto(fila)" @click="revisar(fila, 'COINCIDE_DOCUMENTO')">Coincide con la foto</button><button :disabled="ocupada || !foto(fila)" class="secundario" @click="revisar(fila, 'DIFERENCIA_DOCUMENTO')">Hay una diferencia</button></div>
          </div>
          <router-link v-if="fila.revision?.resultado === 'DIFERENCIA_DOCUMENTO'" :to="{ path: '/kardex-digital', query: { articulo_id: fila.articulo_id, tab: 'hil', tanda: fila.tanda } }">Abrir Kárdex para corregir con evidencia</router-link>
        </template>
      </article>
    </template>
  </main>
</template>

<style scoped>
.muestra-view { max-width: 1100px; margin: 2rem auto; padding: 1.5rem; color: var(--text-primary); }
.panel { background: var(--bg-body); border: 1px solid var(--border-color); border-radius: var(--radius); padding: 1.25rem; margin: 1rem 0; }
.panel h2, .panel h3 { margin-top: 0; }
.controles, .resumen { display: flex; gap: 1rem; flex-wrap: wrap; align-items: end; }
label { display: grid; gap: .35rem; }
input, select, textarea { border: 1px solid var(--border-color); border-radius: .35rem; padding: .55rem; background: var(--bg-body); color: inherit; }
select { max-width: 100%; }
button { background: var(--primary); color: white; border: 0; border-radius: .35rem; padding: .6rem .9rem; cursor: pointer; }
button:disabled { opacity: .5; cursor: not-allowed; }
button.secundario { background: #7c2d12; }
.mensaje, .alerta { padding: .65rem; border-radius: .35rem; }
.error, .alerta { background: #fff7ed; color: #9a3412; }
.exito { background: #ecfdf5; color: #065f46; }
.fila header { display: flex; justify-content: space-between; gap: 1rem; }
.fila details { margin: .8rem 0; }
.fila img { display: block; max-width: 100%; max-height: 560px; object-fit: contain; margin: .7rem 0; border: 1px solid var(--border-color); }
.fila pre { white-space: pre-wrap; overflow-wrap: anywhere; }
.decision { color: #065f46; }
.decision-form { display: grid; gap: .6rem; }
.decision-form div { display: flex; gap: .6rem; flex-wrap: wrap; }
@media (max-width: 640px) { .muestra-view { padding: 1rem; } .fila header { display: block; } }
</style>
