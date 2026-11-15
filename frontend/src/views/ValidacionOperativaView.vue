<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { isAxiosError } from 'axios'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

interface Estudio {
  id: number
  gestion: number
  modelo_id: string
  simulado: boolean
  poblacion: number
  creado_en: string
}
interface Documento { id: number; nombre: string }
interface Caso {
  id: number
  etiqueta: string | null
  motivo: string | null
  respaldo: string | null
  evidencia: {
    id: number
    articulo_id: number
    articulo: string
    tipo: string
    direccion: string
    cantidad: number
    saldo_registrado: number | null
    area_origen: string | null
    area_destino: string | null
    ocurrido_en: string
    registrado_en: string
    documento: string | null
    adjuntos: Documento[]
  }
}
interface Detalle extends Estudio {
  total: number
  pendientes: number
  indeterminados: number
  casos: Caso[]
  metricas: {
    verdaderos_positivos: number
    falsos_positivos: number
    falsos_negativos: number
    verdaderos_negativos: number
    clasificados: number
    precision: number | null
    sensibilidad: number | null
    f1: number | null
  } | null
}
const ruta = '/validacion-operativa'
const auth = useAuthStore()
const gestion = ref(Number(new Intl.DateTimeFormat('es-BO', {
  year: 'numeric', timeZone: 'America/La_Paz',
}).format(new Date())))
const limite = ref(50)
const estudios = ref<Estudio[]>([])
const simulacion = ref(false)
const actual = ref<Detalle | null>(null)
const casoId = ref<number>()
const ocupado = ref(false)
const error = ref('')
const mensaje = ref('')
const dictamen = ref({ etiqueta: '', motivo: '', respaldo: '' })
const caso = computed(() => actual.value?.casos.find(c => c.id === casoId.value))
const listo = computed(() => dictamen.value.etiqueta && dictamen.value.motivo.trim().length >= 10 &&
  (dictamen.value.etiqueta === 'INDETERMINADO' || dictamen.value.respaldo.trim()))
const etiquetas: Record<string, string> = { NORMAL: 'Normal', ANOMALO: 'Anómalo', INDETERMINADO: 'Indeterminado' }

function fecha(valor: string) {
  return new Date(valor).toLocaleString('es-BO', { timeZone: 'America/La_Paz' })
}
function valorMetrica(valor: number | null) {
  return valor === null ? 'No calculable' : valor.toLocaleString('es-BO', {
    minimumFractionDigits: 3, maximumFractionDigits: 3,
  })
}
function elegir(id?: number) {
  casoId.value = id
  dictamen.value = { etiqueta: '', motivo: '', respaldo: '' }
}
async function ejecutar(accion: () => Promise<void>) {
  if (ocupado.value) return
  ocupado.value = true
  error.value = ''
  mensaje.value = ''
  try {
    await accion()
  } catch (e) {
    const detalle = isAxiosError(e) ? e.response?.data?.detail : null
    error.value = typeof detalle === 'string' ? detalle : 'No se pudo completar la operación. Revisa los datos e inténtalo de nuevo.'
  } finally {
    ocupado.value = false
  }
}
async function listar() {
  const { data } = await api.get<{ simulacion: boolean; estudios: Estudio[] }>(ruta)
  estudios.value = data.estudios
  simulacion.value = data.simulacion
}
async function abrir(id: number, conservar?: number) {
  const { data } = await api.get<Detalle>(ruta + '/' + id)
  actual.value = data
  elegir(conservar ?? data.casos.find(c => !c.etiqueta)?.id ?? data.casos[0]?.id)
}
function preparar() {
  return ejecutar(async () => {
    const { data } = await api.post<Estudio>(ruta, { gestion: gestion.value, limite: limite.value })
    estudios.value = [data, ...estudios.value]
    await abrir(data.id)
  })
}
function guardar() {
  if (!actual.value || !caso.value || !listo.value) return
  const estudioId = actual.value.id
  const id = caso.value.id
  return ejecutar(async () => {
    const { data } = await api.post<Caso>(ruta + '/' + estudioId + '/casos/' + id, dictamen.value)
    const estudio = actual.value
    const indice = estudio?.casos.findIndex(c => c.id === id) ?? -1
    if (estudio && indice >= 0) estudio.casos[indice] = data
    await abrir(estudioId, id)
    mensaje.value = 'Dictamen guardado.'
  })
}
function descargar(documento: Documento) {
  const articulo = caso.value?.evidencia.articulo_id
  if (!articulo) return
  return ejecutar(async () => {
    const { data } = await api.get<Blob>('/kardex/articulos/' + articulo + '/documentos/' +
      documento.id + '/archivo', { responseType: 'blob' })
    const url = URL.createObjectURL(data)
    const link = document.createElement('a')
    link.href = url
    link.download = documento.nombre
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  })
}
onMounted(() => {
  void ejecutar(async () => {
    await listar()
    if (estudios.value[0]) await abrir(estudios.value[0].id)
  })
})
</script>

<template>
  <main class="evaluacion">
    <router-link :to="{ name: 'revisiones' }">← Revisiones y alertas</router-link>
    <h1>Evaluación de operaciones</h1>
    <p v-if="simulacion || actual?.simulado" class="nota">Entorno de demostración · Datos sintéticos.</p>
    <p>Coteja cada movimiento con su respaldo. Las puntuaciones y las alertas se mantienen ocultas en esta pantalla.</p>
    <p v-if="error" role="alert" class="error">{{ error }}</p>
    <p v-if="mensaje" role="status">{{ mensaje }}</p>
    <form v-if="auth.rol === 'Administrador'" class="panel filtros" @submit.prevent="preparar">
      <label>Gestión de registro<input v-model.number="gestion" type="number" min="1900" max="9998" required /></label>
      <label>Tamaño máximo de la muestra<input v-model.number="limite" type="number" min="2" max="200" required /></label>
      <button class="btn-primary" :disabled="ocupado">Preparar con el modelo activo</button>
    </form>
    <label v-if="estudios.length">Estudio
      <select :value="actual?.id" :disabled="ocupado" @change="ejecutar(() => abrir(Number(($event.target as HTMLSelectElement).value)))">
        <option v-for="e in estudios" :key="e.id" :value="e.id">
          #{{ e.id }} · {{ e.gestion }} · {{ e.simulado ? 'Sintético' : 'Institucional' }} · {{ fecha(e.creado_en) }}
        </option>
      </select>
    </label>
    <p v-else-if="!ocupado">Todavía no hay muestras preparadas.</p>
    <template v-if="actual">
      <section class="panel" aria-label="Avance de la evaluación">
        <h2>Avance del cotejo</h2>
        <p>{{ actual.total - actual.pendientes }} de {{ actual.total }} revisados · {{ actual.indeterminados }} indeterminados</p>
        <p>Gestión {{ actual.gestion }} · Versión {{ actual.modelo_id.slice(0, 8) }} · {{ actual.poblacion }} operaciones puntuadas en el corte</p>
        <div v-if="actual.metricas">
          <h3>Métricas de la muestra</h3>
          <dl class="metricas">
            <div><dt>Precisión</dt><dd>{{ valorMetrica(actual.metricas.precision) }}</dd></div>
            <div><dt>Sensibilidad</dt><dd>{{ valorMetrica(actual.metricas.sensibilidad) }}</dd></div>
            <div><dt>F1</dt><dd>{{ valorMetrica(actual.metricas.f1) }}</dd></div>
          </dl>
          <p>{{ actual.metricas.verdaderos_positivos }} verdaderos positivos · {{ actual.metricas.falsos_positivos }} falsos positivos ·
            {{ actual.metricas.falsos_negativos }} falsos negativos · {{ actual.metricas.verdaderos_negativos }} verdaderos negativos</p>
          <p>Las métricas corresponden a {{ actual.metricas.clasificados }} casos concluyentes de esta muestra.</p>
          <p v-if="actual.metricas.f1 === null">Para calcular el F1 se necesita al menos un caso confirmado como anómalo.</p>
        </div>
        <p v-else>Las métricas se muestran al completar el cotejo de la muestra.</p>
      </section>
      <label>Caso
        <select :value="casoId" :disabled="ocupado" @change="elegir(Number(($event.target as HTMLSelectElement).value))">
          <option v-for="(c, i) in actual.casos" :key="c.id" :value="c.id">
            Caso {{ i + 1 }} · {{ c.etiqueta ? etiquetas[c.etiqueta] : 'Pendiente' }}
          </option>
        </select>
      </label>
      <section v-if="caso" class="panel" aria-label="Evidencia del cotejo">
        <h2>{{ caso.evidencia.articulo }}</h2>
        <p>{{ caso.evidencia.tipo }} #{{ caso.evidencia.id }} · {{ caso.evidencia.cantidad }} unidades</p>
        <p v-if="caso.evidencia.area_origen || caso.evidencia.area_destino">
          Área de origen {{ caso.evidencia.area_origen || '—' }} · Destino {{ caso.evidencia.area_destino || '—' }}
        </p>
        <p>Hecho {{ fecha(caso.evidencia.ocurrido_en) }} · Registro {{ fecha(caso.evidencia.registrado_en) }}</p>
        <p v-if="caso.evidencia.saldo_registrado !== null">Saldo registrado {{ caso.evidencia.saldo_registrado }}</p>
        <p>Referencia {{ caso.evidencia.documento || 'Sin referencia registrada' }}</p>
        <button v-for="adjunto in caso.evidencia.adjuntos" :key="adjunto.id" class="btn-outline"
          :disabled="ocupado" @click="descargar(adjunto)">Descargar {{ adjunto.nombre }}</button>
        <template v-if="caso.etiqueta">
          <h3>{{ etiquetas[caso.etiqueta] }}</h3>
          <p>{{ caso.motivo }}</p>
          <p v-if="caso.respaldo">Respaldo {{ caso.respaldo }}</p>
          <button v-if="actual.casos.some(c => !c.etiqueta)" class="btn-outline"
            :disabled="ocupado" @click="elegir(actual.casos.find(c => !c.etiqueta)?.id)">Ir al siguiente pendiente</button>
        </template>
        <form v-else aria-label="Registrar dictamen" class="dictamen" @submit.prevent="guardar">
          <fieldset :disabled="ocupado">
            <label>Dictamen<select v-model="dictamen.etiqueta" aria-label="Dictamen" required>
              <option value="" disabled>Seleccionar</option>
              <option v-for="(nombre, clave) in etiquetas" :key="clave" :value="clave">{{ nombre }}</option>
            </select></label>
            <label>Motivo y comprobaciones<textarea v-model="dictamen.motivo" required minlength="10" maxlength="2000" rows="3" /></label>
            <label>Referencia del respaldo comprobado
              <input v-model="dictamen.respaldo" maxlength="250" :required="dictamen.etiqueta !== 'INDETERMINADO'" />
            </label>
            <button class="btn-primary" :disabled="!listo">Guardar dictamen</button>
          </fieldset>
        </form>
      </section>
    </template>
  </main>
</template>

<style scoped>
.evaluacion { max-width: 1000px; margin: auto; padding: 1.5rem 1rem; }
.panel { margin: 1rem 0; padding: 1.2rem; border: 1px solid var(--border-color); border-radius: 8px; }
.filtros, .metricas { display: flex; flex-wrap: wrap; align-items: end; gap: 1rem; }
.dictamen fieldset { margin: 0; padding: 0; border: 0; display: grid; gap: .8rem; justify-items: start; }
.dictamen label { width: min(100%, 650px); }
label { display: grid; gap: .35rem; }
input, select, textarea { max-width: 100%; padding: .55rem; border: 1px solid var(--border-color); border-radius: 6px; }
.metricas dd { margin: .25rem 0 0; font-size: 1.4rem; font-weight: 700; }
.nota { padding: .65rem; background: #fff5da; color: #453400; }
.error { color: #a12222; }
</style>
