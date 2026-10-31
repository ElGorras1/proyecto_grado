<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

interface Operacion {
  clase: string
  id: number
  tipo: string
  cantidad: number
  direccion: string
  documento: string | null
  receptor: string | null
  ocurrido_en: string | null
  registrado_en: string | null
  justificacion_operador: string | null
  encargado_id: number | null
  registrador_id: number | null
  area_origen_id: number | null
  area_destino_id: number | null
  alertas: { codigo: string; nivel: string; mensaje: string; datos: Record<string, unknown> }[]
  cantidad_vigente?: number
  ultima_rectificacion_id?: number | null
  cantidad_fuera?: number
  cantidad_vendida?: number
  cantidad_devuelta?: number
  ubicacion_externa?: string
  ciudad?: string
  receptor_custodia?: string
}
interface Caso {
  id: number
  articulo_id: number
  articulo: string
  codigo: string
  estado: string
  prioridad: string
  asignado_id: number | null
  asignado_nombre: string | null
  revision_numero: number
  creado_en: string
  conclusion: string | null
  operacion: Operacion
}
interface Revision {
  id: number
  usuario_nombre: string
  creado_en: string
  motivo: string
  documento: string | null
  anterior: { estado: string; prioridad: string; asignado_nombre: string | null }
  nuevo: { estado: string; prioridad: string; asignado_nombre: string | null; conclusion: string }
  correccion_movimiento_id: number | null
}
interface Detalle extends Caso {
  actual: Operacion
  huella_contexto: string
  personas: Record<number, string>
  areas: Record<number, string>
  historial: { total: number; filas: Revision[] }
}
const auth = useAuthStore()
const route = useRoute()
const puedeRevisar = computed(() => ['Administrador', 'Auditor'].includes(auth.rol || ''))
const estados = {
  ABIERTOS: 'Abiertos',
  TODOS: 'Todos',
  PENDIENTE: 'Pendiente',
  EN_REVISION: 'En revisión',
  SEGUIMIENTO: 'Seguimiento',
  JUSTIFICADO: 'Justificado',
  CERRADO: 'Cerrado',
}
const prioridades = { ALTA: 'Alta', MEDIA: 'Media', BAJA: 'Baja' }
const conclusiones = {
  NO_CONCLUYENTE: 'No concluyente',
  LEGITIMO: 'Legítimo',
  REQUIERE_CORRECCION: 'Requiere corrección',
  CORREGIDO: 'Corregido mediante rectificación',
}
const textoEstado = (valor: string) => estados[valor as keyof typeof estados] || valor
const textoPrioridad = (valor: string) => prioridades[valor as keyof typeof prioridades] || valor
const filtros = ref({
  estado: 'ABIERTOS',
  prioridad: '',
  articulo_id: typeof route.query.articulo_id === 'string' ? route.query.articulo_id : '',
  asignado: '',
  gestion: '' as number | '',
  desde: '',
  hasta: '',
})
const aplicados = ref({ ...filtros.value })
const filtrosPendientes = computed(
  () => JSON.stringify(filtros.value) !== JSON.stringify(aplicados.value),
)
const filas = ref<Caso[]>([])
const total = ref(0)
const conteos = ref<Record<string, number>>({})
const pagina = ref(1)
const catalogo = ref<{ id: number; nombre: string }[]>([])
const revisores = ref<{ id: number; nombre: string; rol: string }[]>([])
const detalle = ref<Detalle | null>(null)
const paginaHistorial = ref(1)
const cargando = ref(false)
const abriendo = ref(false)
const cargandoHistorial = ref(false)
const guardando = ref(false)
const error = ref('')
const errorCatalogos = ref('')
const exito = ref('')
const desactualizado = ref(false)
const solicitud = ref(crypto.randomUUID())
const decision = ref({
  estado: 'EN_REVISION',
  prioridad: 'MEDIA',
  asignado_id: '' as number | '',
  conclusion: 'NO_CONCLUYENTE',
  motivo: '',
  documento: '',
  correccion_movimiento_id: '' as number | '',
})
watch(
  decision,
  () => {
    solicitud.value = crypto.randomUUID()
  },
  { deep: true },
)
const siguientes = computed(() =>
  detalle.value?.estado === 'PENDIENTE' ||
  ['JUSTIFICADO', 'CERRADO'].includes(detalle.value?.estado || '')
    ? ['EN_REVISION']
    : ['EN_REVISION', 'SEGUIMIENTO', 'JUSTIFICADO', 'CERRADO'],
)
let consulta = 0,
  consultaDetalle = 0,
  consultaHistorial = 0,
  desmontado = false
onUnmounted(() => {
  desmontado = true
  consulta++
  consultaDetalle++
  consultaHistorial++
})
function cerrarDetalle() {
  consultaDetalle++
  consultaHistorial++
  detalle.value = null
  abriendo.value = false
  cargandoHistorial.value = false
}
function fecha(valor: string | null) {
  return valor
    ? new Intl.DateTimeFormat('es-BO', {
        timeZone: 'America/La_Paz',
        dateStyle: 'short',
        timeStyle: 'short',
      }).format(new Date(valor))
    : 'No registrada'
}
function mensaje(err: any, alternativa: string) {
  return typeof err.response?.data?.detail === 'string' ? err.response.data.detail : alternativa
}
async function cargar() {
  const turno = ++consulta
  cargando.value = true
  error.value = ''
  filas.value = []
  total.value = 0
  conteos.value = {}
  try {
    const f = aplicados.value
    const { data } = await api.get('/control-alertas', {
      params: {
        estado: f.estado,
        prioridad: f.prioridad || undefined,
        articulo_id: f.articulo_id || undefined,
        asignado_id: f.asignado && f.asignado !== 'sin' ? f.asignado : undefined,
        sin_asignar: f.asignado === 'sin',
        gestion: f.gestion || undefined,
        desde: f.desde || undefined,
        hasta: f.hasta || undefined,
        pagina: pagina.value,
        limite: 30,
      },
    })
    if (turno !== consulta) return
    filas.value = data.filas
    total.value = data.total
    conteos.value = data.conteos
  } catch (err) {
    if (turno === consulta)
      error.value = mensaje(err, 'No se pudo cargar la bandeja. Vuelve a intentar.')
  } finally {
    if (turno === consulta) cargando.value = false
  }
}
async function filtrar() {
  if (guardando.value || cargando.value) return
  if (filtros.value.desde && filtros.value.hasta && filtros.value.desde > filtros.value.hasta) {
    error.value = 'El inicio no puede ser posterior al fin'
    return
  }
  cerrarDetalle()
  aplicados.value = { ...filtros.value }
  pagina.value = 1
  await cargar()
}
async function limpiarFiltros() {
  if (guardando.value || cargando.value) return
  filtros.value = {
    estado: 'ABIERTOS',
    prioridad: '',
    articulo_id: '',
    asignado: '',
    gestion: '',
    desde: '',
    hasta: '',
  }
  await filtrar()
}
async function paginarCasos(delta: number) {
  if (cargando.value || guardando.value) return
  cerrarDetalle()
  pagina.value += delta
  await cargar()
}
function preparar(data: Detalle) {
  detalle.value = data
  paginaHistorial.value = 1
  desactualizado.value = false
  decision.value = {
    estado: 'EN_REVISION',
    prioridad: data.prioridad,
    asignado_id:
      data.asignado_id && revisores.value.some((r) => r.id === data.asignado_id)
        ? data.asignado_id
        : (auth.usuario?.id ?? ''),
    conclusion: 'NO_CONCLUYENTE',
    motivo: '',
    documento: '',
    correccion_movimiento_id: '',
  }
  solicitud.value = crypto.randomUUID()
}
async function abrir(id: number, conservarMotivo = false) {
  if (guardando.value) return
  const turno = ++consultaDetalle
  consultaHistorial++
  cargandoHistorial.value = false
  abriendo.value = true
  error.value = ''
  exito.value = ''
  const anotacion = conservarMotivo ? decision.value.motivo : ''
  try {
    const { data } = await api.get('/control-alertas/' + id)
    if (turno !== consultaDetalle) return
    preparar(data)
    if (anotacion) decision.value.motivo = anotacion
  } catch (err) {
    if (turno === consultaDetalle) {
      detalle.value = null
      error.value = mensaje(err, 'No se pudo abrir el caso.')
    }
  } finally {
    if (turno === consultaDetalle) abriendo.value = false
  }
}
async function historial(anterior: boolean) {
  if (!detalle.value || cargandoHistorial.value) return
  const id = detalle.value.id,
    turno = ++consultaHistorial
  cargandoHistorial.value = true
  const nueva = paginaHistorial.value + (anterior ? -1 : 1)
  try {
    const { data } = await api.get('/control-alertas/' + id + '/revisiones', {
      params: { pagina: nueva },
    })
    if (turno !== consultaHistorial || detalle.value?.id !== id) return
    detalle.value.historial = data
    paginaHistorial.value = nueva
  } catch (err) {
    if (turno === consultaHistorial) error.value = mensaje(err, 'No se pudo cargar el historial.')
  } finally {
    if (turno === consultaHistorial) cargandoHistorial.value = false
  }
}
async function guardar() {
  if (!detalle.value || !puedeRevisar.value || guardando.value || desactualizado.value) return
  if (!decision.value.asignado_id || decision.value.motivo.trim().length < 10) {
    error.value = 'Selecciona un revisor y escribe un motivo de al menos 10 caracteres.'
    return
  }
  const resuelto = ['JUSTIFICADO', 'CERRADO'].includes(decision.value.estado)
  if (
    resuelto &&
    (!['LEGITIMO', 'CORREGIDO'].includes(decision.value.conclusion) ||
      decision.value.documento.trim().length < 3)
  ) {
    error.value = 'Para resolver, registra una conclusión válida y el documento que la respalda.'
    return
  }
  if (decision.value.conclusion === 'CORREGIDO' && !decision.value.correccion_movimiento_id) {
    error.value = 'Vincula la rectificación del movimiento antes de marcarlo corregido.'
    return
  }
  guardando.value = true
  error.value = ''
  exito.value = ''
  try {
    const { data } = await api.post('/control-alertas/' + detalle.value.id + '/revision', {
      solicitud_id: solicitud.value,
      revision_esperada: detalle.value.revision_numero,
      huella_contexto: detalle.value.huella_contexto,
      estado: decision.value.estado,
      prioridad: decision.value.prioridad,
      asignado_id: decision.value.asignado_id,
      conclusion: decision.value.conclusion,
      motivo: decision.value.motivo.trim(),
      documento: decision.value.documento.trim() || null,
      correccion_movimiento_id:
        decision.value.conclusion === 'CORREGIDO' ? decision.value.correccion_movimiento_id : null,
    })
    preparar(data)
    exito.value = 'Decisión registrada. El inventario conserva sus cantidades.'
    await cargar()
  } catch (err: any) {
    desactualizado.value = err.response?.status === 409
    error.value = mensaje(
      err,
      'No se pudo confirmar la revisión. Conservamos tus datos; reintenta la misma decisión.',
    )
  } finally {
    guardando.value = false
  }
}
onMounted(async () => {
  try {
    const [a, r] = await Promise.all([
      api.get('/kardex/articulos'),
      api.get('/control-alertas/revisores'),
    ])
    if (desmontado) return
    catalogo.value = a.data
    revisores.value = r.data
  } catch {
    errorCatalogos.value =
      'No se pudieron cargar los artículos o revisores. Recarga esta página para usar esos filtros.'
  }
  if (!desmontado) {
    await cargar()
    const id = Number(route.query.caso_id)
    if (!desmontado && Number.isInteger(id) && id > 0) await abrir(id)
  }
})
</script>

<template>
  <main class="bandeja">
    <router-link to="/">Volver al inicio</router-link>
    <h1>Alertas de inventario</h1>
    <p>
      Revisa los avisos de operaciones registradas y documenta su seguimiento. Cada caso reúne los
      avisos de una operación.
    </p>
    <p class="enlaces">
      <router-link to="/analitica">Auditoría histórica con Isolation Forest</router-link>
    </p>
    <p v-if="error" class="alert alert-error" role="alert">{{ error }}</p>
    <p v-if="errorCatalogos" class="alert alert-error" role="alert">{{ errorCatalogos }}</p>
    <p v-if="exito" class="alert alert-success" role="status">{{ exito }}</p>
    <form class="filtros" aria-label="Filtrar alertas" @submit.prevent="filtrar">
      <label
        >Estado<select v-model="filtros.estado" aria-label="Estado del caso">
          <option v-for="(t, k) in estados" :key="k" :value="k">{{ t }}</option>
        </select></label
      >
      <label
        >Prioridad<select v-model="filtros.prioridad" aria-label="Prioridad del caso">
          <option value="">Todas</option>
          <option v-for="(t, k) in prioridades" :key="k" :value="k">{{ t }}</option>
        </select></label
      >
      <label
        >Artículo<select v-model="filtros.articulo_id" aria-label="Artículo">
          <option value="">Todos</option>
          <option v-for="a in catalogo" :key="a.id" :value="String(a.id)">{{ a.nombre }}</option>
        </select></label
      >
      <label
        >Revisor<select v-model="filtros.asignado" aria-label="Revisor asignado">
          <option value="">Todos</option>
          <option value="sin">Sin asignar</option>
          <option v-for="r in revisores" :key="r.id" :value="String(r.id)">
            {{ r.nombre }} · {{ r.rol }}
          </option>
        </select></label
      >
      <label
        >Gestión de registro<input
          v-model.number="filtros.gestion"
          type="number"
          min="1900"
          max="9998"
          step="1"
          placeholder="Todas"
          aria-label="Gestión de registro"
      /></label>
      <label>Desde<input v-model="filtros.desde" type="date" aria-label="Desde" /></label>
      <label>Hasta<input v-model="filtros.hasta" type="date" aria-label="Hasta" /></label>
      <button type="submit" :disabled="cargando || guardando">Aplicar filtros</button>
      <button type="button" :disabled="cargando || guardando" @click="limpiarFiltros">
        Limpiar filtros
      </button>
    </form>
    <p>
      La gestión y las fechas usan el registro de la operación en Bolivia. Si combinas ambos
      filtros, deben coincidir.
    </p>
    <p v-if="filtrosPendientes" role="status">Hay cambios sin aplicar. Pulsa «Aplicar filtros».</p>
    <p aria-label="Resumen de casos">
      {{ total }} casos en esta selección
      <span v-for="(cantidad, estado) in conteos" :key="estado">
        · {{ textoEstado(String(estado)) }}: {{ cantidad }}</span
      >
    </p>
    <p v-if="cargando" role="status">Cargando casos...</p>
    <p v-else-if="!error && !filas.length" class="vacio">
      No hay casos para estos filtros. Los avisos confirmados en nuevas operaciones aparecerán aquí.
    </p>
    <div class="columnas">
      <section aria-label="Lista de alertas">
        <button
          v-for="c in filas"
          :key="c.id"
          class="caso"
          :class="{ seleccionado: detalle?.id === c.id }"
          :disabled="abriendo || guardando"
          :aria-pressed="detalle?.id === c.id"
          @click="abrir(c.id)"
        >
          <strong>{{ c.articulo }}</strong
          ><span>{{ c.operacion.tipo }} · {{ c.operacion.cantidad }} u. · {{ c.codigo }}</span>
          <span
            ><b :class="'prioridad-' + c.prioridad">{{ textoPrioridad(c.prioridad) }}</b> ·
            {{ textoEstado(c.estado) }} · {{ c.operacion.alertas.length }} avisos</span
          >
          <span>{{ c.asignado_nombre || 'Sin revisor asignado' }} · {{ fecha(c.creado_en) }}</span>
        </button>
        <nav v-if="total > 30" class="paginacion" aria-label="Páginas de casos">
          <button :disabled="pagina === 1 || cargando || guardando" @click="paginarCasos(-1)">
            Anterior
          </button>
          <span>Página {{ pagina }} de {{ Math.ceil(total / 30) }}</span>
          <button
            :disabled="pagina * 30 >= total || cargando || guardando"
            @click="paginarCasos(1)"
          >
            Siguiente
          </button>
        </nav>
      </section>
      <p v-if="abriendo" role="status">Abriendo evidencia...</p>
      <section v-else-if="detalle" class="detalle" aria-label="Detalle de alerta">
        <header>
          <h2>{{ detalle.articulo }}</h2>
          <p>
            Caso #{{ detalle.id }} · {{ textoEstado(detalle.estado) }} ·
            {{ textoPrioridad(detalle.prioridad) }}
          </p>
        </header>
        <p>Revisor: {{ detalle.asignado_nombre || 'Sin asignar' }}</p>
        <h3>Operación y evidencia</h3>
        <p>
          {{ detalle.operacion.tipo }} · {{ detalle.operacion.cantidad }} u. ·
          {{ detalle.operacion.direccion }}
        </p>
        <p v-if="detalle.actual.cantidad_vigente !== undefined">
          Cantidad vigente: {{ detalle.actual.cantidad_vigente }} u.<span
            v-if="detalle.actual.ultima_rectificacion_id"
          >
            · última rectificación #{{ detalle.actual.ultima_rectificacion_id }}</span
          >
        </p>
        <p v-if="detalle.actual.cantidad_fuera !== undefined">
          Custodia actual: {{ detalle.actual.cantidad_fuera }} u. fuera ·
          {{ detalle.actual.cantidad_vendida }} vendidas ·
          {{ detalle.actual.cantidad_devuelta }} devueltas
        </p>
        <p>
          Origen:
          {{
            detalle.operacion.area_origen_id
              ? detalle.areas[detalle.operacion.area_origen_id] ||
                'Área #' + detalle.operacion.area_origen_id
              : 'Sin área de origen registrada'
          }}<span v-if="detalle.operacion.area_destino_id">
            · Destino:
            {{
              detalle.areas[detalle.operacion.area_destino_id] ||
              'Área #' + detalle.operacion.area_destino_id
            }}</span
          >
        </p>
        <p v-if="detalle.operacion.receptor">Receptor: {{ detalle.operacion.receptor }}</p>
        <p v-if="detalle.actual.ubicacion_externa">
          Ubicación externa: {{ detalle.actual.ubicacion_externa }} · {{ detalle.actual.ciudad
          }}<span v-if="detalle.actual.receptor_custodia">
            · Custodio: {{ detalle.actual.receptor_custodia }}</span
          >
        </p>
        <p>
          Encargado:
          {{
            detalle.operacion.encargado_id
              ? detalle.personas[detalle.operacion.encargado_id]
              : 'No registrado'
          }}
          · Registró:
          {{
            detalle.operacion.registrador_id
              ? detalle.personas[detalle.operacion.registrador_id]
              : 'No registrado'
          }}
        </p>
        <p>
          Hecho: {{ fecha(detalle.operacion.ocurrido_en) }} · Registro:
          {{ fecha(detalle.operacion.registrado_en) }}
        </p>
        <p>Documento: {{ detalle.operacion.documento || 'No registrado' }}</p>
        <p v-if="detalle.operacion.justificacion_operador">
          <strong>Justificación al registrar:</strong>
          {{ detalle.operacion.justificacion_operador }}
        </p>
        <ul class="avisos">
          <li v-for="a in detalle.operacion.alertas" :key="a.codigo">
            <strong>{{ a.mensaje }}</strong
            ><span>Nivel {{ a.nivel }} · {{ a.codigo }}</span>
            <details>
              <summary>Datos que originaron el aviso</summary>
              <pre>{{ JSON.stringify(a.datos, null, 2) }}</pre>
            </details>
          </li>
        </ul>
        <p class="enlaces">
          <router-link
            :to="{ path: '/kardex-digital', query: { articulo_id: detalle.articulo_id } }"
            >Kárdex y trazabilidad del artículo</router-link
          ><router-link to="/inventario-vivo">Abrir inventario para una rectificación</router-link>
        </p>
        <form
          v-if="puedeRevisar"
          aria-label="Revisar caso"
          class="revision"
          @submit.prevent="guardar"
        >
          <h3>
            {{
              ['JUSTIFICADO', 'CERRADO'].includes(detalle.estado)
                ? 'Reabrir con motivo'
                : 'Registrar revisión'
            }}
          </h3>
          <p v-if="detalle.estado === 'PENDIENTE'">
            Primero asigna un revisor y abre el caso en revisión.
          </p>
          <label
            >Estado siguiente<select v-model="decision.estado" aria-label="Estado siguiente">
              <option v-for="s in siguientes" :key="s" :value="s">{{ textoEstado(s) }}</option>
            </select></label
          >
          <label
            >Prioridad de revisión<select
              v-model="decision.prioridad"
              aria-label="Prioridad de revisión"
            >
              <option v-for="(t, k) in prioridades" :key="k" :value="k">{{ t }}</option>
            </select></label
          >
          <label
            >Asignar a<select v-model.number="decision.asignado_id" aria-label="Asignar a" required>
              <option value="">Seleccionar revisor</option>
              <option v-for="r in revisores" :key="r.id" :value="r.id">
                {{ r.nombre }} · {{ r.rol }}
              </option>
            </select></label
          >
          <label
            >Conclusión<select v-model="decision.conclusion" aria-label="Conclusión">
              <option v-for="(t, k) in conclusiones" :key="k" :value="k">{{ t }}</option>
            </select></label
          >
          <label
            >Motivo y comprobaciones<textarea
              v-model="decision.motivo"
              aria-label="Motivo y comprobaciones"
              minlength="10"
              maxlength="2000"
              rows="4"
              required
            ></textarea>
          </label>
          <label
            >Documento de respaldo<input
              v-model="decision.documento"
              aria-label="Documento de respaldo"
              maxlength="200"
              placeholder="Acta, factura o referencia verificable"
          /></label>
          <label v-if="decision.conclusion === 'CORREGIDO'"
            >Rectificación vinculada<input
              v-model.number="decision.correccion_movimiento_id"
              type="number"
              aria-label="Rectificación vinculada"
              min="1"
              step="1"
          /></label>
          <p>
            Resolver el caso exige una conclusión y un respaldo. Las diferencias pendientes
            permanecen en seguimiento. Las cantidades se corrigen desde Inventario Actual.
          </p>
          <p v-if="desactualizado" role="alert">
            La decisión no se guardó. Actualiza el detalle antes de volver a revisar; tu anotación
            se conservará.
          </p>
          <button v-if="desactualizado" type="button" @click="abrir(detalle.id, true)">
            Actualizar detalle
          </button>
          <button type="submit" :disabled="guardando || desactualizado">
            {{ guardando ? 'Guardando...' : 'Guardar revisión' }}
          </button>
        </form>
        <p v-else>
          Solo administradores y auditores pueden registrar decisiones. Puedes consultar la
          evidencia y el historial.
        </p>
        <section aria-label="Historial de revisiones" class="historial">
          <h3>Historial de revisiones</h3>
          <p v-if="!detalle.historial.total">Aún no hay decisiones de revisión.</p>
          <ol>
            <li v-for="r in detalle.historial.filas" :key="r.id">
              <strong
                >{{ textoEstado(r.anterior.estado) }} → {{ textoEstado(r.nuevo.estado) }}</strong
              >
              <p>{{ r.usuario_nombre }} · {{ fecha(r.creado_en) }}</p>
              <p>
                Asignado: {{ r.nuevo.asignado_nombre }} · Prioridad:
                {{ textoPrioridad(r.anterior.prioridad) }} →
                {{ textoPrioridad(r.nuevo.prioridad) }} ·
                {{ conclusiones[r.nuevo.conclusion as keyof typeof conclusiones] }}
              </p>
              <p>{{ r.motivo }}</p>
              <p v-if="r.documento">Respaldo: {{ r.documento }}</p>
              <p v-if="r.correccion_movimiento_id">
                Rectificación #{{ r.correccion_movimiento_id }}
              </p>
            </li>
          </ol>
          <nav
            v-if="detalle.historial.total > 50"
            class="paginacion"
            aria-label="Páginas de revisiones"
          >
            <button :disabled="paginaHistorial === 1 || cargandoHistorial" @click="historial(true)">
              Más recientes
            </button>
            <span>Página {{ paginaHistorial }}</span
            ><button
              :disabled="paginaHistorial * 50 >= detalle.historial.total || cargandoHistorial"
              @click="historial(false)"
            >
              Más antiguas
            </button>
          </nav>
        </section>
      </section>
    </div>
  </main>
</template>

<style scoped>
.bandeja {
  max-width: 1280px;
  margin: auto;
  padding: 2rem 1.5rem;
}
h1 {
  margin: 1rem 0 0.6rem;
}
h2 {
  margin: 0 0 0.6rem;
  font-size: 1.3rem;
}
h3 {
  margin: 1.5rem 0 0.6rem;
  font-size: 1.05rem;
}
p {
  line-height: 1.6;
  overflow-wrap: anywhere;
}
.enlaces {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem 1.5rem;
}
.filtros {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.9rem;
  margin: 1.5rem 0;
  padding: 1.2rem;
  background: var(--bg-subtle);
  border-radius: 12px;
}
label {
  display: grid;
  gap: 0.35rem;
  font-size: 0.9rem;
}
input,
select,
textarea {
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
}
.columnas {
  display: grid;
  grid-template-columns: minmax(260px, 0.8fr) minmax(0, 1.4fr);
  gap: 1.3rem;
  align-items: start;
}
.caso {
  display: block !important;
  text-align: left;
  width: 100%;
  padding: 1rem;
  margin: 0 0 0.65rem;
  border: 1px solid var(--border-color) !important;
  border-radius: 10px;
  background: white !important;
  color: var(--text-primary) !important;
  white-space: normal;
}
.caso span,
.caso strong {
  display: block;
  overflow-wrap: anywhere;
  margin-bottom: 0.3rem;
}
.caso .prioridad-ALTA {
  color: #9f2a2a;
}
.caso .prioridad-MEDIA {
  color: #8a5500;
}
.caso.seleccionado {
  border-color: var(--primary) !important;
  background: var(--bg-subtle) !important;
}
.detalle {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.25rem;
  min-width: 0;
}
.avisos {
  padding-left: 1.2rem;
}
.avisos li {
  margin-bottom: 1rem;
}
.avisos span {
  display: block;
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin: 0.3rem 0;
}
pre {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font-size: 0.8rem;
}
.revision {
  display: grid;
  gap: 0.8rem;
  border-top: 1px solid var(--border-color);
  margin-top: 1rem;
}
.historial {
  margin-top: 1rem;
  border-top: 1px solid var(--border-color);
}
.historial ol {
  padding-left: 1.2rem;
}
.historial li {
  padding: 0.6rem 0;
}
.historial p {
  margin: 0.35rem 0;
}
.paginacion {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.7rem;
}
.vacio {
  background: var(--bg-subtle);
  padding: 1rem;
  border-radius: 8px;
}
@media (max-width: 800px) {
  .columnas {
    grid-template-columns: 1fr;
  }
  .filtros {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 480px) {
  .bandeja {
    padding: 1rem;
  }
  .filtros {
    grid-template-columns: 1fr;
  }
  .detalle {
    padding: 1rem;
  }
}
</style>
