<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useRoute, useRouter } from 'vue-router'
import { GESTION_DOCUMENTAL_HASTA } from '@/config/alcance'
const props = withDefaults(defineProps<{ seccion?: 'resumen' | 'cierres' | 'completo' }>(), { seccion: 'completo' })
const titulo = computed(() => props.seccion === 'cierres' ? 'Balance y cierre de gestión' : props.seccion === 'resumen' ? 'Resumen institucional' : 'Informe institucional y cierres anuales')

interface Saldo {
  articulo_id: number
  articulo: string
  codigo: string
  saldo_actual: number | null
  origen: string
  operativo: boolean
  distribucion: { sin_ubicacion_confirmada: number; en_custodia_externa: number }
}
interface Evento {
  id: number
  clase: string
  articulo: string
  fecha_registro: string
  fecha_operacion: string
  ingreso: number
  salida: number
  cantidad_transferida: number
}
interface Balance {
  gestion: number
  total: number
  alcance: string
  corte_exclusivo: string
  articulos: {
    articulo_id: number
    articulo: string
    total: number
    sin_ubicacion: number
    custodia: number
  }[]
}
interface Previa {
  snapshot: Balance
  huella: string
  puede_cerrar: boolean
  impedimentos: string[]
}
interface Cierre {
  id: number
  gestion: number
  version: number
  estado: string
  creado_en: string
  documento: string
  motivo: string
  huella: string
  snapshot: Balance
  motivo_reapertura: string | null
}
interface Informe {
  gestion: number
  generado_en: string
  limites: string
  inventario_actual: Saldo[]
  movimientos: Evento[]
  totales_actuales: {
    operativo: number
    documental_sin_activar: number
    articulos_sin_saldo_confiable: number
  }
  resumen_periodo: {
    eventos: number
    ingresos_y_ajustes: number
    salidas_y_ajustes: number
    trasladado: number
  }
  cobertura_historica: {
    historicos: number
    elegibles: number
    porcentaje_fisico: number | null
    por_gestion?: Record<string, { disponibles: number; elegibles: number }>
  }
  articulos_con_error_integridad: number[]
}
const auth = useAuthStore()
const admin = computed(() => auth.rol === 'Administrador')
const ruta = useRoute()
const router = useRouter()
const gestionEnlace = Number(ruta.query.gestion)
const gestion = ref(Number.isInteger(gestionEnlace) && gestionEnlace >= 1900 && gestionEnlace <= 9998
  ? gestionEnlace : GESTION_DOCUMENTAL_HASTA)
const informe = ref<Informe | null>(null),
  previa = ref<Previa | null>(null)
const cierres = ref<Cierre[]>([]),
  totalCierres = ref(0),
  paginaCierres = ref(1)
const cargando = ref(false),
  enviando = ref(false),
  error = ref(''),
  mensaje = ref('')
const documento = ref(''),
  motivo = ref(''),
  revisado = ref(false)
const motivosReapertura = ref<Record<number, string>>({})
const paginaStock = ref(1),
  paginaEventos = ref(1)
function fueraDePagina(indice: number, pagina: number) {
  return indice < (pagina - 1) * 30 || indice >= pagina * 30
}
const hayInventarioActivado = computed(() => informe.value?.inventario_actual.some(a => a.operativo) ?? false)
const historicoGestion = computed(
  () =>
    informe.value?.cobertura_historica.por_gestion?.[String(informe.value.gestion)] ?? {
      disponibles: 0,
      elegibles: 0,
    },
)
const puedeCerrar = computed(
  () =>
    admin.value &&
    previa.value?.puede_cerrar &&
    revisado.value &&
    documento.value.trim().length >= 3 &&
    motivo.value.trim().length >= 10 &&
    gestion.value === previa.value?.snapshot.gestion &&
    !cargando.value &&
    !enviando.value,
)
let consulta = 0,
  ultimoEnvio: { firma: string; id: string } | null = null
onUnmounted(() => {
  consulta++
})
function detalle(e: any) {
  const d = e?.response?.data?.detail
  return typeof d === 'string'
    ? d
    : (d?.mensaje ?? 'No se pudo completar la solicitud. Puedes volver a intentar.')
}
async function cargar() {
  const turno = ++consulta
  cargando.value = true
  error.value = ''
  previa.value = null
  informe.value = null
  revisado.value = false
  try {
    const [i, p, c] = await Promise.all([
      props.seccion !== 'cierres' ? api.get('/reportes/institucional', { params: { gestion: gestion.value } }) : Promise.resolve({ data: null }),
      props.seccion !== 'resumen' ? api.get(`/cierres-anuales/${gestion.value}/vista-previa`) : Promise.resolve({ data: null }),
      props.seccion !== 'resumen' ? api.get('/cierres-anuales', { params: { pagina: paginaCierres.value, limite: 20 } }) : Promise.resolve({ data: { filas: [], total: 0 } }),
    ])
    if (turno !== consulta) return
    informe.value = i.data
    previa.value = p.data
    cierres.value = c.data.filas
    totalCierres.value = c.data.total
    paginaStock.value = paginaEventos.value = 1
    if (String(ruta.query.gestion ?? '') !== String(gestion.value)) void router.replace({ query: { ...ruta.query, gestion: gestion.value } }).catch(() => {})
  } catch (e) {
    if (turno === consulta) error.value = detalle(e)
  } finally {
    if (turno === consulta) cargando.value = false
  }
}
function consultar() {
  paginaCierres.value = 1
  void cargar()
}
watch([() => props.seccion, () => ruta.query.gestion], ([seccion, parametro], [anterior]) => {
  const anio = Number(parametro)
  const valido = Number.isInteger(anio) && anio >= 1900 && anio <= 9998
  if (seccion === anterior && (!valido || anio === gestion.value)) return
  if (valido) gestion.value = anio
  documento.value = motivo.value = mensaje.value = ''
  consultar()
})
function paginarCierres(delta: number) {
  paginaCierres.value += delta
  void cargar()
}
async function cerrar() {
  if (!puedeCerrar.value || !previa.value) return
  const campos = {
    huella_esperada: previa.value.huella,
    documento: documento.value.trim(),
    motivo: motivo.value.trim(),
    balance_revisado: true,
  }
  const firma = JSON.stringify([gestion.value, campos])
  if (ultimoEnvio?.firma !== firma) ultimoEnvio = { firma, id: crypto.randomUUID() }
  enviando.value = true
  error.value = ''
  mensaje.value = ''
  try {
    const { data } = await api.post(`/cierres-anuales/${gestion.value}`, {
      ...campos,
      solicitud_id: ultimoEnvio.id,
    })
    mensaje.value = `Cierre de ${data.gestion}, versión ${data.version}, guardado. El stock permanece disponible para la siguiente gestión.`
    ultimoEnvio = null
    documento.value = motivo.value = ''
    await cargar()
  } catch (e) {
    error.value = detalle(e)
  } finally {
    enviando.value = false
  }
}
async function reabrir(c: Cierre) {
  const razon = motivosReapertura.value[c.id]?.trim() ?? ''
  if (!admin.value || razon.length < 10 || enviando.value) return
  enviando.value = true
  error.value = ''
  mensaje.value = ''
  try {
    await api.post(`/cierres-anuales/registro/${c.id}/reabrir`, { motivo: razon })
    mensaje.value =
      'Reapertura registrada. El balance original se conserva; un nuevo cierre creará otra versión.'
    await cargar()
  } catch (e) {
    error.value = detalle(e)
  } finally {
    enviando.value = false
  }
}
function descargar(datos: unknown, nombre: string) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(datos, null, 2)], { type: 'application/json' }),
  )
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombre
  enlace.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
function imprimir() {
  window.print()
}
function origenBase(v: string) {
  return (
    (
      {
        CONTEO_FISICO_INICIAL: 'Conteo inicial confirmado',
        BASE_DOCUMENTAL_PROVISIONAL: 'Saldo escaneado provisional',
        BASE_BLOQUEADA: 'Cierre con observaciones',
        SIN_BASE: 'Sin base disponible',
      } as Record<string, string>
    )[v] ?? 'Base sin clasificar'
  )
}
function fecha(v: string) {
  return new Date(v).toLocaleString('es-BO', { timeZone: 'America/La_Paz' })
}
onMounted(cargar)
</script>

<template>
  <main class="gestion">
    <header>
      <div>
        <router-link to="/">Volver al inicio</router-link>
        <h1>{{ titulo }}</h1>
        <p v-if="props.seccion === 'cierres'">Conserva un balance revisado cuando exista inventario operativo. Consultar el archivo histórico no exige cerrar una gestión.</p>
        <p v-else>Saldos documentales, inventario activado y registros de la gestión consultada.</p>
        <p>El proyecto utiliza documentos hasta {{ GESTION_DOCUMENTAL_HASTA }}. Los saldos actuales y las fechas de registro digital se presentan por separado.</p>
      </div>
    </header>
    <form class="filtros" @submit.prevent="consultar">
      <label
        >Gestión de registro
        <input
          v-model.number="gestion"
          type="number"
          min="1900"
          max="9998"
          required
          :disabled="enviando || cargando"
      /></label>
      <button :disabled="cargando || enviando">Consultar</button>
      <button type="button" :disabled="!informe && !previa" @click="imprimir">Imprimir o guardar PDF</button>
    </form>
    <details v-if="informe && props.seccion !== 'cierres'" class="exportacion-avanzada"><summary>Exportación avanzada</summary><button :disabled="cargando" @click="descargar(informe, `informe_institucional_${informe.gestion}.json`)">Descargar informe completo en JSON</button></details>
    <p v-if="cargando" role="status">Preparando informe y balance…</p>
    <p v-if="error" role="alert" class="error">{{ error }}</p>
    <p v-if="mensaje" role="status">{{ mensaje }}</p>
    <p v-if="informe && gestion !== informe.gestion" role="status">
      La gestión cambió sin consultar. Pulsa «Consultar»; el informe visible sigue siendo de
      {{ informe.gestion }}.
    </p>
    <template v-if="informe">
      <p>Generado: {{ fecha(informe.generado_en) }} · Gestión documental consultada: {{ informe.gestion }}.</p>
      <section class="panel">
        <h2>Documentos históricos de {{ informe.gestion }}</h2>
        <p>
          {{ historicoGestion.disponibles }} movimientos escaneados activos ·
          {{ historicoGestion.elegibles }} elegibles para análisis.
        </p>
        <p>
          Se agrupan por la fecha del papel. No se cuentan como operaciones digitales nuevas ni
          certifican un cierre físico anual.
        </p>
        <p>Cobertura del archivo físico: {{ informe.cobertura_historica.porcentaje_fisico === null ? 'sin porcentaje verificado' : `${informe.cobertura_historica.porcentaje_fisico}%` }}.</p>
        <p>
          <router-link
            :to="{
              path: '/reportes/inventario',
              query: { gestion: informe.gestion, origen: 'historico' },
            }"
            >Ver todos los movimientos escaneados de {{ informe.gestion }}</router-link
          >
          ·
          <router-link :to="{ path: '/analitica', query: { gestion: informe.gestion } }"
            >Ver auditoría histórica de {{ informe.gestion }}</router-link
          >
        </p>
      </section>
      <section v-if="informe.resumen_periodo.eventos > 0" class="panel">
        <h2>Registros digitales de {{ informe.gestion }}</h2>
        <p>
          Se agrupan por fecha de registro en Bolivia. Una transferencia o entrega a custodia
          conserva el total institucional; una venta lo reduce.
        </p>
        <p>
          {{ informe.resumen_periodo.eventos }} eventos ·
          {{ informe.resumen_periodo.ingresos_y_ajustes }} ingresos y ajustes positivos ·
          {{ informe.resumen_periodo.salidas_y_ajustes }} salidas y ajustes negativos ·
          {{ informe.resumen_periodo.trasladado }} unidades trasladadas.
        </p>
        <p v-if="!informe.movimientos.length">
          No hay registros digitales de esta gestión dentro del inventario activado.
        </p>
        <div v-else class="tabla">
          <table>
            <thead>
              <tr>
                <th>Artículo / operación</th>
                <th>Registro</th>
                <th>Ingreso</th>
                <th>Salida</th>
                <th>Traslado</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(e, indice) in informe.movimientos" :key="`${e.clase}:${e.id}`" :class="{ 'fuera-de-pagina': fueraDePagina(indice, paginaEventos) }">
                <td>
                  {{ e.articulo }}<small>{{ e.clase }} #{{ e.id }}</small>
                </td>
                <td>{{ fecha(e.fecha_registro) }}</td>
                <td>{{ e.ingreso }}</td>
                <td>{{ e.salida }}</td>
                <td>{{ e.cantidad_transferida }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="informe.movimientos.length" class="paginacion">
          <button :disabled="paginaEventos <= 1" @click="paginaEventos--">Anterior</button
          ><span>Página {{ paginaEventos }} · {{ informe.movimientos.length }} eventos</span
          ><button
            :disabled="paginaEventos * 30 >= informe.movimientos.length"
            @click="paginaEventos++"
          >
            Siguiente
          </button>
        </div>
        <p>
          {{ informe.cobertura_historica.historicos }} filas históricas activas;
          {{ informe.cobertura_historica.elegibles }} elegibles para análisis. Cobertura del archivo
          físico:
          {{
            informe.cobertura_historica.porcentaje_fisico === null
              ? 'sin porcentaje verificado'
              : `${informe.cobertura_historica.porcentaje_fisico}%`
          }}.
        </p>
      </section>
      <section class="panel">
        <h2>{{ hayInventarioActivado ? 'Inventario actual' : 'Saldos documentales' }}</h2>
        <p>
          El filtro de gestión cambia los registros del período y la vista previa del cierre. Esta
          tabla conserva los saldos actuales.
        </p>
        <p>{{ informe.limites }}</p>
        <div class="indicadores">
          <div>
            <strong>{{ informe.totales_actuales.operativo }}</strong
            ><span>Unidades de inventario activado</span>
          </div>
          <div>
            <strong>{{ informe.totales_actuales.documental_sin_activar }}</strong
            ><span>Saldo documental sin activar</span>
          </div>
          <div>
            <strong>{{ informe.totales_actuales.articulos_sin_saldo_confiable }}</strong
            ><span>Artículos sin saldo confiable</span>
          </div>
        </div>
        <p v-if="informe.articulos_con_error_integridad.length" class="error">
          Hay inconsistencias de integridad en los artículos
          {{ informe.articulos_con_error_integridad.join(', ') }}. Deben revisarse antes del cierre.
        </p>
        <div class="tabla">
          <table>
            <thead>
              <tr>
                <th>Artículo</th>
                <th>Saldo registrado</th>
                <th>Base</th>
                <th>Sin ubicación</th>
                <th>Custodia externa</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(a, indice) in informe.inventario_actual" :key="a.articulo_id" :class="{ 'fuera-de-pagina': fueraDePagina(indice, paginaStock) }">
                <td>
                  {{ a.articulo }}<small>{{ a.codigo }}</small>
                </td>
                <td>{{ a.saldo_actual ?? 'Sin saldo confiable' }}</td>
                <td>
                  {{ origenBase(a.origen)
                  }}<small>{{ a.operativo ? 'Inventario activado' : 'Sin activar' }}</small>
                </td>
                <td>{{ a.distribucion.sin_ubicacion_confirmada }}</td>
                <td>{{ a.distribucion.en_custodia_externa }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="paginacion">
          <button :disabled="paginaStock <= 1" @click="paginaStock--">Anterior</button
          ><span>Página {{ paginaStock }} · {{ informe.inventario_actual.length }} artículos</span
          ><button
            :disabled="paginaStock * 30 >= informe.inventario_actual.length"
            @click="paginaStock++"
          >
            Siguiente
          </button>
        </div>
      </section>
    </template>
    <section v-if="previa" class="panel">
      <h2>Vista previa del cierre de {{ previa.snapshot.gestion }}</h2>
      <p>{{ previa.snapshot.alcance }}</p>
      <p>
        Saldo al corte: <strong>{{ previa.snapshot.total }}</strong> unidades en
        {{ previa.snapshot.articulos.length }} artículos. Corte exclusivo:
        {{ fecha(previa.snapshot.corte_exclusivo) }}.
      </p>
      <ul v-if="previa.impedimentos.length">
        <li v-for="i in previa.impedimentos" :key="i">{{ i }}</li>
      </ul>
      <details class="exportacion-avanzada"><summary>Exportación avanzada del balance</summary><button @click="descargar(previa, `balance_previo_${previa.snapshot.gestion}.json`)">Descargar balance en JSON</button></details>
      <p v-if="!previa.snapshot.articulos.length" role="status">No hay inventario operativo incluido en este balance. Puedes seguir consultando documentos y reportes; no necesitas registrar un cierre vacío.</p>
      <form v-if="admin && previa.snapshot.articulos.length" class="cierre-form" @submit.prevent="cerrar">
        <label
          >Documento de respaldo
          <input
            v-model="documento"
            maxlength="200"
            :disabled="enviando"
            placeholder="Acta o informe de revisión"
        /></label>
        <label
          >Motivo del cierre <textarea v-model="motivo" maxlength="2000" :disabled="enviando" />
        </label>
        <label class="confirmacion"
          ><input v-model="revisado" type="checkbox" :disabled="enviando || !previa.puede_cerrar" />
          He revisado el balance y su alcance documental.</label
        >
        <button :disabled="!puedeCerrar">Guardar cierre anual</button>
      </form>
      <p v-else-if="!admin">
        El Administrador puede guardar un cierre tras revisar el balance y sus impedimentos.
      </p>
    </section>
    <section v-if="props.seccion !== 'resumen'" class="panel">
      <h2>Cierres conservados de todas las gestiones</h2>
      <p v-if="totalCierres > 20">Este historial muestra la página {{ paginaCierres }} de {{ Math.ceil(totalCierres / 20) }}, con {{ cierres.length }} de {{ totalCierres }} cierres. La impresión incluye únicamente esta página del historial.</p>
      <p v-if="!cierres.length">Todavía no hay cierres anuales guardados.</p>
      <article v-for="c in cierres" :key="c.id">
        <h3>{{ c.gestion }} · versión {{ c.version }} · {{ c.estado }}</h3>
        <p>{{ c.snapshot.total }} unidades · {{ c.documento }} · {{ fecha(c.creado_en) }}</p>
        <p>{{ c.motivo }}</p>
        <p v-if="c.motivo_reapertura">Reapertura: {{ c.motivo_reapertura }}</p>
        <button @click="descargar(c, `cierre_${c.gestion}_v${c.version}.json`)">
          Descargar cierre conservado
        </button>
        <form
          v-if="admin && c.estado === 'CERRADO'"
          class="cierre-form"
          @submit.prevent="reabrir(c)"
        >
          <label
            >Motivo de reapertura
            <textarea
              v-model="motivosReapertura[c.id]"
              maxlength="2000"
              :disabled="enviando"
            /></label
          ><button :disabled="enviando || (motivosReapertura[c.id]?.trim().length ?? 0) < 10">
            Registrar reapertura
          </button>
        </form>
      </article>
      <div v-if="totalCierres > 20" class="paginacion">
        <button :disabled="paginaCierres <= 1 || cargando" @click="paginarCierres(-1)">
          Anterior</button
        ><span>Página {{ paginaCierres }} · {{ totalCierres }} cierres</span
        ><button
          :disabled="paginaCierres * 20 >= totalCierres || cargando"
          @click="paginarCierres(1)"
        >
          Siguiente
        </button>
      </div>
    </section>
  </main>
</template>

<style scoped>
.exportacion-avanzada { margin: .5rem 0 1rem; }
.exportacion-avanzada summary { cursor: pointer; color: var(--text-secondary); }
.gestion {
  max-width: 1200px;
  margin: auto;
  padding: 2rem 1rem;
}
h1 {
  font-size: 1.8rem;
}
h2 {
  font-size: 1.25rem;
}
.filtros,
.paginacion {
  display: flex;
  gap: 1rem;
  align-items: end;
  flex-wrap: wrap;
}
.filtros {
  margin: 1.5rem 0;
}
.panel {
  padding: 1.5rem;
  background: var(--surface-card, #fff);
  border: 1px solid #dce4eb;
  border-radius: 12px;
  margin: 1.5rem 0;
}
.indicadores {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin: 1.5rem 0;
}
.indicadores strong {
  font-size: 1.8rem;
  display: block;
}
span,
small {
  display: block;
}
.tabla {
  overflow: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th,
td {
  text-align: left;
  padding: 0.8rem;
  border-bottom: 1px solid #dce4eb;
}
small {
  color: #637584;
}
button {
  padding: 0.65rem 0.9rem;
  border: 1px solid #b6c9d7;
  border-radius: 6px;
  background: white;
  cursor: pointer;
}
button:disabled {
  opacity: 0.5;
  cursor: default;
}
label {
  display: block;
}
input:not([type='checkbox']),
textarea {
  display: block;
  max-width: 600px;
  width: 100%;
  padding: 0.6rem;
  margin: 0.4rem 0;
}
input[type='number'] {
  max-width: 140px;
}
textarea {
  min-height: 70px;
}
.cierre-form {
  margin-top: 1.5rem;
  max-width: 600px;
}
.confirmacion {
  display: flex;
  gap: 0.5rem;
  margin: 1rem 0;
}
.error {
  color: #a32929;
}
article {
  border-top: 1px solid #dce4eb;
  padding: 1rem 0;
}
.paginacion {
  margin-top: 1rem;
  justify-content: space-between;
}
@media (max-width: 600px) {
  .indicadores {
    grid-template-columns: 1fr;
  }
  .panel {
    padding: 1rem;
  }
  h1 {
    font-size: 1.4rem;
  }
}
.fuera-de-pagina {
  display: none;
}
@media print {
  :global(body) {
    background: white;
  }
  button,
  .cierre-form,
  .exportacion-avanzada,
  .filtros,
  .paginacion {
    display: none !important;
  }
  .gestion {
    max-width: none;
    padding: 0;
    font-size: 10pt;
    background: white;
  }
  header a {
    display: none;
  }
  h1 {
    font-size: 18pt;
  }
  h2 {
    font-size: 12pt;
    break-after: avoid;
  }
  .panel {
    break-inside: auto;
    padding: .5rem 0;
    margin: .5rem 0;
    border: none;
    border-radius: 0;
  }
  .tabla {
    overflow: visible;
  }
  thead {
    display: table-header-group;
  }
  table {
    table-layout: fixed;
    border-radius: 0 !important;
  }
  th,
  td {
    padding: 5pt !important;
    font-size: 9pt !important;
    overflow-wrap: anywhere;
  }
  th:first-child {
    width: 36%;
  }
  th:nth-child(3) {
    width: 22%;
  }
  tr {
    break-inside: avoid;
  }
  tr.fuera-de-pagina {
    display: table-row;
  }
}
</style>
