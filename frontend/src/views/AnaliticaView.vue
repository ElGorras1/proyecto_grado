<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { isAxiosError } from 'axios'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import EvaluacionAnalitica from '@/components/EvaluacionAnalitica.vue'
import ReglasHistoricas from '@/components/ReglasHistoricas.vue'
import type { DiagnosticoAnalitica } from '@/services/analitica'

interface Perfil {
  total: number
  historicos_activos: number
  elegibles: number
  exclusiones: Record<string, number>
  por_gestion: Record<string, { disponibles: number; elegibles: number }>
  advertencia: string
  por_articulo?: Record<string, { nombre: string; disponibles: number; elegibles: number }>
}
interface Metricas {
  particiones: Record<string, number>
  alertas: number
  k: number
  jaccard_top_entre_semillas: number[]
  solapamiento_top_regla: number
  sin_referencia_propia_evaluacion: number
  evaluacion_humana: string
}
interface Modelo {
  id: string
  estado: string
  creado_en: string
  error: string | null
  perfil: Perfil
  metricas: Metricas | null
  umbral: number | null
  datos_cambiaron?: boolean
}
interface Fila {
  id: number
  articulo: string
  codigo: string
  fecha: string
  fecha_estado: string
  lote_id: number
  numero_pagina: number
  orden_fila: number
  detalle: string
  ingresos: number | null
  salidas: number | null
  nodo_grafo: string | null
  ruta_imagen_respaldo: string | null
}
interface Resultado {
  id: number
  nodo: string | null
  movimiento_id: number
  score: number
  alerta: boolean
  particion: string
  muestra_control: boolean
  estado_revision: string
  revision_numero: number
  etiqueta: string | null
  snapshot: Fila
  contexto: { mediana: number; referencias: number; indicadores: string[]; regla_magnitud: boolean }
}
interface Detalle extends Resultado {
  datos_cambiaron: boolean
  vecinos: Fila[]
  revisiones: {
    id: number
    usuario: string
    fecha: string
    estado: string
    motivo: string
    etiqueta: string
  }[]
}
const auth = useAuthStore()
const route = useRoute()
const perfil = ref<Perfil | null>(null)
const modelos = ref<Modelo[]>([])
const totalModelos = ref(0)
const paginaModelos = ref(1)
const seleccionado = ref('')
const modelo = ref<Modelo | null>(null)
const diagnostico = ref<DiagnosticoAnalitica | null>(null)
const filas = ref<Resultado[]>([])
const total = ref(0)
const pagina = ref(1)
const gestion = ref(typeof route.query.gestion === 'string' ? route.query.gestion : '')
const articulo = ref('')
const nodo = ref('')
const estado = ref('')
const seleccion = ref('todos')
const aplicados = ref({
  gestion: gestion.value,
  articulo: '',
  nodo: '',
  estado: '',
  seleccion: 'todos',
})
const filtrosPendientes = computed(
  () =>
    JSON.stringify({
      gestion: gestion.value,
      articulo: articulo.value.trim(),
      nodo: nodo.value.trim(),
      estado: estado.value,
      seleccion: seleccion.value,
    }) !== JSON.stringify(aplicados.value),
)
const porcentaje = ref(5)
const modo = ref<'RETROSPECTIVO' | 'TEMPORAL'>('RETROSPECTIVO')
const anioTemporal = ref(new Date().getFullYear() - 1)
const planTemporal = ref<{
  suficiente: boolean
  particiones: Record<string, number>
  purga: Record<string, number>
  faltantes: Record<string, number>
} | null>(null)
const preparandoTemporal = ref(false)
const excluidos = ref<number[]>([])
const detalle = ref<Detalle | null>(null)
const revision = ref({ estado: 'EN_REVISION', etiqueta: 'NO_CONCLUYENTE', motivo: '' })
const error = ref('')
const cargando = ref(false)
const guardando = ref(false)
const iniciando = ref(false)
const fotoError = ref(false)
const puedeRevisar = computed(() => ['Administrador', 'Auditor'].includes(auth.rol ?? ''))
const activo = computed(() =>
  modelos.value.some((m) => ['PENDIENTE', 'EN_EJECUCION'].includes(m.estado)),
)
const gestiones = computed(() =>
  [
    ...new Set([
      ...Object.keys(modelo.value?.perfil.por_gestion ?? perfil.value?.por_gestion ?? {}),
      ...(gestion.value ? [gestion.value] : []),
    ]),
  ]
    .sort()
    .reverse(),
)
const foto = computed(() => {
  const ruta = detalle.value?.snapshot.ruta_imagen_respaldo?.replace(/\\/g, '/')
  if (!ruta?.startsWith('storage/')) return ''
  return new URL(
    '/' + ruta,
    new URL(api.defaults.baseURL ?? '/api/v1', window.location.origin).origin,
  ).href
})
let timer: ReturnType<typeof setTimeout> | undefined
let desmontado = false
let solicitudTemporal = 0
let solicitud = 0
let solicitudDetalle = 0
function fallo(e: unknown) {
  const d = isAxiosError(e) ? e.response?.data?.detail : null
  error.value =
    typeof d === 'string'
      ? d
      : 'No se pudo completar la consulta. Reintenta; si persiste, revisa el servicio.'
}
async function lista() {
  const { data } = await api.get('/analitica/modelos', { params: { pagina: paginaModelos.value } })
  modelos.value = data.filas
  totalModelos.value = data.total
}
async function cargar(p = 1, nuevos = false) {
  const numero = ++solicitud
  cargando.value = true
  error.value = ''
  try {
    if (!seleccionado.value) {
      filas.value = []
      modelo.value = null
      diagnostico.value = null
      return
    }
    const id = seleccionado.value
    if (modelo.value?.id !== id) {
      modelo.value = null
      filas.value = []
      diagnostico.value = null
    }
    const filtros = nuevos
      ? {
          gestion: gestion.value,
          articulo: articulo.value.trim(),
          nodo: nodo.value.trim(),
          estado: estado.value,
          seleccion: seleccion.value,
        }
      : aplicados.value
    const [m, r, e] = await Promise.all([
      api.get<Modelo>('/analitica/modelos/' + id),
      api.get('/analitica/resultados', {
        params: {
          modelo_id: id,
          gestion: filtros.gestion || undefined,
          articulo: filtros.articulo || undefined,
          nodo: filtros.nodo || undefined,
          estado: filtros.estado || undefined,
          seleccion: filtros.seleccion,
          pagina: p,
        },
      }),
      api.get<DiagnosticoAnalitica>('/analitica/modelos/' + id + '/diagnostico'),
    ])
    if (numero !== solicitud || desmontado) return
    aplicados.value = filtros
    modelo.value = m.data
    filas.value = r.data.filas
    total.value = r.data.total
    pagina.value = p
    diagnostico.value = e.data.version === 1 && e.data.modelo_id === id ? e.data : null
  } catch (e) {
    if (numero === solicitud) {
      filas.value = []
      total.value = 0
      fallo(e)
    }
  } finally {
    if (numero === solicitud) cargando.value = false
  }
}
async function cambiarVersion() {
  cerrarDetalle()
  await cargar()
}
async function aplicarFiltros() {
  cerrarDetalle()
  await cargar(1, true)
}
async function limpiarFiltros() {
  await revisarSeleccion('todos')
}
async function revisarSeleccion(filtro: string) {
  gestion.value = ''
  articulo.value = ''
  nodo.value = ''
  estado.value = ''
  seleccion.value = filtro
  await aplicarFiltros()
}
async function actualizar() {
  try {
    error.value = ''
    perfil.value = (await api.get<Perfil>('/analitica/perfil')).data
    await lista()
    if (!seleccionado.value && modelos.value.length) seleccionado.value = modelos.value[0].id
    await cargar()
  } catch (e) {
    fallo(e)
  }
}
async function sondear() {
  if (desmontado) return
  try {
    const previo = modelos.value.find((m) => m.id === seleccionado.value)?.estado
    await lista()
    const nuevo = modelos.value.find((m) => m.id === seleccionado.value)?.estado
    if (previo !== nuevo) await cargar(pagina.value)
  } catch (e) {
    fallo(e)
  }
  if (!desmontado) timer = setTimeout(sondear, activo.value ? 5000 : 30000)
}
async function entrenar() {
  iniciando.value = true
  error.value = ''
  try {
    const { data } = await api.post('/analitica/entrenar', {
      porcentaje_revision: porcentaje.value,
      excluir_articulos: excluidos.value,
      modo: modo.value,
      gestion_evaluacion: modo.value === 'TEMPORAL' ? anioTemporal.value : undefined,
    })
    paginaModelos.value = 1
    await lista()
    cerrarDetalle()
    seleccionado.value = data.job_id
    await cargar()
    if (timer) clearTimeout(timer)
    timer = setTimeout(sondear, 2000)
  } catch (e) {
    fallo(e)
  } finally {
    iniciando.value = false
  }
}
async function prepararTemporal() {
  const turno = ++solicitudTemporal
  planTemporal.value = null
  if (modo.value !== 'TEMPORAL') {
    preparandoTemporal.value = false
    return
  }
  preparandoTemporal.value = true
  try {
    const { data } = await api.get('/analitica/temporal/plan', {
      params: { gestion_evaluacion: anioTemporal.value, excluir_articulos: excluidos.value },
      paramsSerializer: { indexes: null },
    })
    if (turno === solicitudTemporal && !desmontado) planTemporal.value = data
  } catch (e) {
    if (turno === solicitudTemporal && !desmontado) fallo(e)
  } finally {
    if (turno === solicitudTemporal && !desmontado) preparandoTemporal.value = false
  }
}
function cerrarDetalle() {
  solicitudDetalle++
  detalle.value = null
}
async function abrir(id: number) {
  if (guardando.value) return
  await cargarDetalle(id)
}
async function cargarDetalle(id: number) {
  const numero = ++solicitudDetalle
  detalle.value = null
  error.value = ''
  try {
    const { data } = await api.get<Detalle>('/analitica/resultados/' + id)
    if (numero !== solicitudDetalle || desmontado) return
    detalle.value = data
    fotoError.value = false
    revision.value = { estado: 'EN_REVISION', etiqueta: 'NO_CONCLUYENTE', motivo: '' }
  } catch (e) {
    if (numero === solicitudDetalle && !desmontado) fallo(e)
  }
}
async function guardar() {
  if (!detalle.value || guardando.value) return
  guardando.value = true
  error.value = ''
  const id = detalle.value.id
  const numero = solicitudDetalle
  const version = seleccionado.value
  try {
    await api.post('/analitica/resultados/' + id + '/revision', {
      ...revision.value,
      revision_esperada: detalle.value.revision_numero,
    })
    if (numero === solicitudDetalle && !desmontado) await cargarDetalle(id)
    if (version === seleccionado.value && !desmontado) await cargar(pagina.value)
  } catch (e) {
    fallo(e)
  } finally {
    guardando.value = false
  }
}
async function cambiarPaginaModelos(delta: number) {
  paginaModelos.value += delta
  try {
    await lista()
    seleccionado.value = modelos.value[0]?.id ?? ''
    cerrarDetalle()
    await cargar()
  } catch (e) {
    fallo(e)
  }
}
onMounted(async () => {
  await actualizar()
  if (!desmontado) timer = setTimeout(sondear, 5000)
})
onUnmounted(() => {
  desmontado = true
  solicitud++
  solicitudDetalle++
  if (timer) clearTimeout(timer)
})
</script>

<template>
  <main class="analitica">
    <header>
      <div>
        <router-link to="/">← Inicio</router-link>
        <p class="eyebrow">AUDITORÍA HISTÓRICA</p>
        <h1>Movimientos que merecen una revisión</h1>
        <p>Explora el Kárdex por gestión y documenta los hallazgos junto a su evidencia.</p>
      </div>
      <button :disabled="cargando" @click="actualizar">Actualizar datos</button>
    </header>
    <ReglasHistoricas :gestion-inicial="typeof route.query.gestion === 'string' ? route.query.gestion : ''" />
    <p class="nota">
      Análisis retrospectivo de varios años. Una puntuación alta indica rareza, no probabilidad de
      fraude. La cobertura del archivo físico sigue siendo desconocida.
    </p>
    <p v-if="error" role="alert" class="error">{{ error }}</p>
    <section v-if="perfil" class="panel">
      <h2>Preparación del histórico</h2>
      <div class="cifras">
        <p>
          <strong>{{ perfil.historicos_activos }}</strong> históricos activos
        </p>
        <p>
          <strong>{{ perfil.elegibles }}</strong> candidatos elegibles
        </p>
      </div>
      <details>
        <summary>Exclusiones y cobertura actual</summary>
        <p>
          Las exclusiones usan un motivo principal por fila. Las operaciones modernas no participan.
        </p>
        <ul>
          <li v-for="(n, razon) in perfil.exclusiones" :key="razon">
            {{ razon.split('_').join(' ') }}: {{ n }}
          </li>
        </ul>
        <div class="tabla">
          <table>
            <thead>
              <tr>
                <th>Gestión documental</th>
                <th>Digitalizados</th>
                <th>Elegibles</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(g, anio) in perfil.por_gestion" :key="anio">
                <td>{{ anio === 'SIN_GESTION_CONFIRMADA' ? 'Sin gestión confirmada' : anio }}</td>
                <td>{{ g.disponibles }}</td>
                <td>{{ g.elegibles }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </details>
      <form v-if="auth.rol === 'Administrador'" class="entrenamiento" @submit.prevent="entrenar">
        <label
          >Tipo de evaluación
          <select v-model="modo" @change="prepararTemporal">
            <option value="RETROSPECTIVO">Retrospectiva por lotes</option>
            <option value="TEMPORAL">Comparación con un año reservado</option>
          </select>
        </label>
        <label v-if="modo === 'TEMPORAL'"
          >Año reservado
          <input
            v-model.number="anioTemporal"
            type="number"
            min="1902"
            :max="new Date().getFullYear() - 1"
            required
            @change="prepararTemporal"
          />
        </label>
        <div v-if="modo === 'TEMPORAL'" class="plan-temporal">
          <p>
            Entrenamiento hasta {{ anioTemporal - 2 }}, calibración {{ anioTemporal - 1 }} y
            evaluación {{ anioTemporal }}. Los grupos que mezclan períodos se excluyen.
          </p>
          <p v-if="preparandoTemporal">Comprobando documentos disponibles…</p>
          <template v-else-if="planTemporal">
            <p v-for="(n, parte) in planTemporal.particiones" :key="parte">
              {{ parte }}: {{ n }} movimientos
            </p>
            <p v-if="!planTemporal.suficiente" class="nota">
              La muestra temporal es insuficiente. Se necesitan al menos 50 de entrenamiento, 20 de
              calibración, 20 de evaluación y cinco grupos independientes.
            </p>
            <p v-for="(n, razon) in planTemporal.purga" :key="razon">
              {{ razon.replace(/_/g, ' ') }}: {{ n }}
            </p>
          </template>
        </div>
        <label
          >Capacidad inicial de revisión (%)<input
            v-model.number="porcentaje"
            type="number"
            min="1"
            max="20"
            step="0.5"
            required
        /></label>
        <label
          >Excluir artículos (opcional)
          <select
            v-model="excluidos"
            multiple
            aria-label="Artículos excluidos"
            @change="prepararTemporal"
          >
            <option v-for="(a, id) in perfil.por_articulo" :key="id" :value="Number(id)">
              {{ a.nombre }}
            </option>
          </select></label
        >
        <button
          class="primario"
          :disabled="
            activo ||
            iniciando ||
            (modo === 'TEMPORAL' && (!planTemporal?.suficiente || preparandoTemporal))
          "
        >
          {{ iniciando ? 'Preparando corte…' : 'Entrenar nueva versión' }}
        </button>
        <p>
          El porcentaje define un umbral provisional en calibración. No representa la tasa de
          irregularidades. Cada versión conserva sus datos y resultados.
        </p>
      </form>
    </section>
    <section class="panel">
      <h2>Versiones y trabajos</h2>
      <p v-if="!modelos.length">
        Todavía no hay modelos. Un administrador puede iniciar el primer entrenamiento.
      </p>
      <label v-else
        >Versión<select v-model="seleccionado" @change="cambiarVersion">
          <option v-for="m in modelos" :key="m.id" :value="m.id">
            {{ new Date(m.creado_en).toLocaleString() }} · {{ m.estado }} · {{ m.id.slice(0, 8) }}
          </option>
        </select></label
      >
      <div v-if="totalModelos > 20" class="paginacion">
        <button :disabled="paginaModelos === 1" @click="cambiarPaginaModelos(-1)">
          Versiones anteriores</button
        ><span>Página {{ paginaModelos }}</span
        ><button :disabled="paginaModelos * 20 >= totalModelos" @click="cambiarPaginaModelos(1)">
          Más versiones
        </button>
      </div>
      <template v-if="modelo">
        <p role="status">
          Estado: <strong>{{ modelo.estado }}</strong>
        </p>
        <p v-if="['PENDIENTE', 'EN_EJECUCION'].includes(modelo.estado)">
          El trabajo continúa en el servidor. Puedes salir de esta pantalla.
        </p>
        <p v-if="modelo.error" class="error">{{ modelo.error }}</p>
        <p v-if="modelo.datos_cambiaron" class="nota">
          Hay cambios posteriores al corte. Estos resultados conservan los datos anteriores; entrena
          otra versión para incorporar las novedades.
        </p>
        <p>
          Elegibles en este corte: {{ modelo.perfil.elegibles }}. El filtro anual no limita el
          entrenamiento a ese año.
        </p>
        <details v-if="modelo.metricas">
          <summary>Evaluación y límites del modelo</summary>
          <p>Umbral: {{ modelo.umbral?.toFixed(4) }} · Alertas: {{ modelo.metricas.alertas }}</p>
          <p v-for="(n, parte) in modelo.metricas.particiones" :key="parte">{{ parte }}: {{ n }}</p>
          <p>
            Coincidencia entre semillas (Jaccard):
            {{ modelo.metricas.jaccard_top_entre_semillas.map((n) => n.toFixed(2)).join(', ') }}.
            Coincidencia con regla de magnitud:
            {{ (modelo.metricas.solapamiento_top_regla * 100).toFixed(0) }}%.
          </p>
          <p>
            {{ modelo.metricas.sin_referencia_propia_evaluacion }} movimientos de evaluación sin
            referencia propia de artículo/dirección. Se compararon con una referencia global.
          </p>
          <p>
            Estas medidas no demuestran precisión. Revisa las selecciones del modelo, la regla y el
            control sin alertas.
          </p>
          <EvaluacionAnalitica
            v-if="diagnostico"
            :diagnostico="diagnostico"
            :cargando="cargando"
            @seleccionar="revisarSeleccion"
          />
        </details>
      </template>
    </section>
    <section v-if="modelo?.estado === 'COMPLETADO'" class="panel">
      <h2>Resultados por gestión</h2>
      <form class="filtros" @submit.prevent="aplicarFiltros">
        <label
          >Gestión documental<select v-model="gestion" aria-label="Gestión documental">
            <option value="">Todas</option>
            <option v-for="g in gestiones" :key="g">{{ g }}</option>
          </select></label
        >
        <label>Artículo o código<input v-model="articulo" aria-label="Artículo o código" /></label>
        <label>Nodo exacto<input v-model="nodo" aria-label="Nodo exacto" /></label>
        <label
          >Revisión<select v-model="estado" aria-label="Revisión histórica">
            <option value="">Todas</option>
            <option
              v-for="e in [
                'PENDIENTE',
                'EN_REVISION',
                'JUSTIFICADO',
                'REQUIERE_SEGUIMIENTO',
                'CERRADO',
              ]"
              :key="e"
            >
              {{ e }}
            </option>
          </select></label
        >
        <label
          >Selección<select v-model="seleccion" aria-label="Selección">
            <option value="todos">Todos los evaluados</option>
            <option value="alertas">Sobre el umbral</option>
            <option value="top_modelo">Primeros del modelo (evaluación)</option>
            <option value="top_regla">Primeros de regla (evaluación)</option>
            <option value="control">Muestra de control sin alertas</option>
          </select></label
        >
        <button :disabled="cargando">Aplicar filtros</button>
        <button type="button" :disabled="cargando" @click="limpiarFiltros">Limpiar filtros</button>
      </form>
      <p>
        La gestión corresponde a la fecha del documento. Esta lista muestra los movimientos
        evaluados por la versión seleccionada.
      </p>
      <p v-if="filtrosPendientes" role="status">
        Hay cambios sin aplicar. Pulsa «Aplicar filtros».
      </p>
      <p v-if="cargando" role="status">Consultando resultados…</p>
      <p v-else-if="!error && !filas.length">No hay resultados para estos filtros.</p>
      <div v-else class="tabla">
        <table>
          <thead>
            <tr>
              <th>Fecha documental</th>
              <th>Artículo</th>
              <th>Entrada / salida</th>
              <th>Puntuación</th>
              <th>Revisión</th>
              <th>Detalle</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in filas" :key="r.id">
              <td>
                {{ r.snapshot.fecha
                }}<small v-if="r.snapshot.fecha_estado === 'CONFIRMADA_DOCUMENTO'"
                  >Fecha confirmada en papel; cronología no garantizada</small
                >
              </td>
              <td>
                {{ r.snapshot.articulo }}<small>{{ r.nodo }}</small>
              </td>
              <td>{{ r.snapshot.ingresos || 0 }} / {{ r.snapshot.salidas || 0 }}</td>
              <td>
                <strong>{{ r.score.toFixed(4) }}</strong
                ><small
                  >{{ r.alerta ? 'Sobre el umbral' : 'Bajo el umbral' }} · {{ r.particion }}</small
                >
              </td>
              <td>{{ r.estado_revision }}</td>
              <td><button @click="abrir(r.id)">Ver evidencia</button></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="paginacion">
        <button :disabled="pagina <= 1 || cargando" @click="cargar(pagina - 1)">Anterior</button
        ><span
          >{{ total }} resultados · Página {{ pagina }} de
          {{ Math.max(1, Math.ceil(total / 30)) }}</span
        ><button :disabled="pagina * 30 >= total || cargando" @click="cargar(pagina + 1)">
          Siguiente
        </button>
      </div>
    </section>
    <section v-if="detalle" class="panel detalle" aria-label="Evidencia del hallazgo">
      <header>
        <h2>Movimiento #{{ detalle.movimiento_id }} · {{ detalle.snapshot.articulo }}</h2>
        <button :disabled="guardando" @click="cerrarDetalle">Cerrar detalle</button>
      </header>
      <p v-if="detalle.datos_cambiaron" class="nota">
        El registro actual cambió. La puntuación y la revisión corresponden al corte conservado que
        se muestra aquí.
      </p>
      <div class="evidencia">
        <div>
          <a v-if="foto && !fotoError" :href="foto" target="_blank" rel="noopener"
            ><img :src="foto" alt="Fotografía original del Kárdex" @error="fotoError = true"
          /></a>
          <p v-else>Fotografía no disponible. Revisa la conservación del archivo de respaldo.</p>
        </div>
        <div>
          <p>{{ detalle.snapshot.detalle }}</p>
          <p>
            Lote {{ detalle.snapshot.lote_id }} · Página {{ detalle.snapshot.numero_pagina }} · Fila
            {{ detalle.snapshot.orden_fila }}
          </p>
          <p>
            Mediana de referencia: {{ detalle.contexto.mediana }} ·
            {{ detalle.contexto.referencias }} movimientos comparables en entrenamiento.
          </p>
          <ul>
            <li v-for="texto in detalle.contexto.indicadores" :key="texto">{{ texto }}</li>
          </ul>
          <p>Los indicadores dan contexto; no son una explicación causal del modelo.</p>
          <router-link to="/kardex-digital">
            Abrir Kárdex para revisar calidad documental
          </router-link>
        </div>
      </div>
      <h3>Contexto en orden físico del corte</h3>
      <ol>
        <li v-for="v in detalle.vecinos" :key="v.id">
          #{{ v.id }} · {{ v.fecha }} · {{ v.detalle }} · +{{ v.ingresos || 0 }} / −{{
            v.salidas || 0
          }}
        </li>
      </ol>
      <p v-if="error" role="alert" class="error">{{ error }}</p>
      <form v-if="puedeRevisar" class="revision" @submit.prevent="guardar">
        <h3>Documentar revisión</h3>
        <label
          >Estado<select v-model="revision.estado">
            <option
              v-for="e in ['EN_REVISION', 'JUSTIFICADO', 'REQUIERE_SEGUIMIENTO', 'CERRADO']"
              :key="e"
            >
              {{ e }}
            </option>
          </select></label
        >
        <label
          >Conclusión<select v-model="revision.etiqueta">
            <option value="NO_CONCLUYENTE">No concluyente</option>
            <option value="LEGITIMO">Operación legítima</option>
            <option value="INUSUAL_RELEVANTE">Inusual y relevante para investigar</option>
            <option value="ERROR_DOCUMENTAL">Error documental: derivar a HIL</option>
          </select></label
        >
        <label
          >Motivo y evidencia consultada<textarea
            v-model="revision.motivo"
            minlength="10"
            maxlength="4000"
            required
            rows="3"
          ></textarea></label
        ><button class="primario" :disabled="guardando">
          {{ guardando ? 'Guardando…' : 'Guardar revisión' }}
        </button>
      </form>
      <h3>Historial de revisión</h3>
      <p v-if="!detalle.revisiones.length">Aún no hay revisiones.</p>
      <article v-for="r in detalle.revisiones" :key="r.id">
        <strong>{{ r.usuario }} · {{ r.estado }}</strong>
        <p>{{ new Date(r.fecha).toLocaleString() }} · {{ r.etiqueta }}</p>
        <p>{{ r.motivo }}</p>
      </article>
    </section>
  </main>
</template>

<style scoped>
.analitica {
  max-width: 1250px;
  margin: auto;
  padding: 2rem 1.25rem;
  color: var(--text-primary, #243746);
}
header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 1rem;
}
h1 {
  font-size: 1.8rem;
  margin: 0.5rem 0;
}
h2 {
  font-size: 1.2rem;
}
h3 {
  font-size: 1rem;
}
.eyebrow {
  font-size: 0.72rem;
  letter-spacing: 0.14em;
  margin-top: 1.5rem;
  color: #54728a;
}
.panel {
  background: white;
  border: 1px solid #dce4eb;
  border-radius: 14px;
  padding: 1.5rem;
  margin: 1.25rem 0;
}
.nota {
  background: #f5f2e8;
  border-left: 3px solid #ac8737;
  padding: 1rem;
  line-height: 1.6;
}
.error {
  color: #9b2525;
  background: #fff0f0;
  padding: 1rem;
}
.cifras {
  display: flex;
  gap: 3rem;
}
.cifras strong {
  display: block;
  font-size: 1.8rem;
  color: #355b76;
}
label {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.85rem;
}
input,
select,
textarea,
button {
  font: inherit;
  padding: 0.65rem;
  border: 1px solid #b9c9d5;
  border-radius: 7px;
  background: white;
  color: inherit;
}
button {
  cursor: pointer;
}
button:disabled {
  opacity: 0.55;
  cursor: default;
}
.primario {
  background: #355b76;
  color: white;
}
button:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible {
  outline: 3px solid #8db1ca;
  outline-offset: 2px;
}
.entrenamiento,
.filtros {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: end;
  margin-top: 1rem;
}
.entrenamiento label {
  flex: 0 1 300px;
  min-width: 0;
  max-width: 100%;
}
.entrenamiento select {
  width: 100%;
  max-width: 100%;
}
.entrenamiento p {
  width: 100%;
  font-size: 0.85rem;
  color: #596d7b;
}
.filtros label {
  flex: 1;
  min-width: 140px;
}
.tabla {
  overflow: auto;
  margin-top: 1rem;
}
table {
  border-collapse: collapse;
  width: 100%;
  font-size: 0.86rem;
}
th,
td {
  text-align: left;
  padding: 0.8rem;
  border-bottom: 1px solid #e1e7ed;
}
th {
  background: #f3f6f8;
}
small {
  display: block;
  color: #596d7b;
  margin-top: 0.3rem;
}
summary {
  cursor: pointer;
  color: #355b76;
  padding: 0.5rem 0;
}
.paginacion {
  display: flex;
  gap: 1rem;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  font-size: 0.85rem;
}
.evidencia {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}
.evidencia img {
  width: 100%;
  max-height: 650px;
  object-fit: contain;
  background: #f4f6f8;
}
.revision {
  display: grid;
  gap: 1rem;
  max-width: 650px;
}
article {
  border-top: 1px solid #dce4eb;
  padding: 1rem 0;
}
li {
  margin: 0.5rem 0;
}
p {
  line-height: 1.6;
}
@media (max-width: 700px) {
  header {
    flex-direction: column;
  }
  .evidencia {
    grid-template-columns: 1fr;
  }
  .panel {
    padding: 1rem;
  }
  .paginacion {
    flex-wrap: wrap;
  }
  .cifras {
    gap: 1.5rem;
  }
  h1 {
    font-size: 1.45rem;
  }
}
</style>
