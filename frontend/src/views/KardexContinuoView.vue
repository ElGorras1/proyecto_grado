<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import TrazabilidadArticulo from '@/components/TrazabilidadArticulo.vue'
import RevisionHil from '@/components/RevisionHil.vue'
import MarcaDocumental from '@/components/MarcaDocumental.vue'
import ObservacionHilArticulo from '@/components/ObservacionHilArticulo.vue'
import BuscadorArticulos from '@/components/BuscadorArticulos.vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import { GESTION_DOCUMENTAL_HASTA, ultimaGestionDocumental } from '@/config/alcance'
import { categoriasHil, type TratamientoHil } from '@/services/tratamientoHil'


// Tipos
interface Articulo {
  id: number
  nombre: string
  codigo: string
  alertas_rojas: number
  alertas_amarillas: number
  observacion_hil?: { observado: boolean; excluir_entrenamiento: boolean; motivo: string } | null
}

interface Movimiento {
  id: number
  lote_id: number | null
  tanda: number | null
  fecha_movimiento: string | null
  fecha_documental_texto?: string | null
  fecha_precision?: string | null
  detalle: string
  referencia: string | null
  area: string | null
  ingresos: number | null
  salidas: number | null
  saldo_registrado: number
  ruta_imagen_respaldo: string | null
  numero_pagina: number | null
  orden_fila: number | null
  tiene_error_saldo: boolean
  saldo_calculado: number | null
  observaciones: string | null
  nodo_grafo: string | null
  requiere_auditoria_nodo: boolean
  area_estado: string
  referencia_estado: string
  requiere_auditoria_referencia: boolean
  fecha_original: string | null
  datos_originales: Record<string, unknown> | null
  tiene_error_fecha: boolean
  fecha_estado: string
  tipos_alerta: string[]
  revision_documental?: Record<string, any> | null
  tratamiento_hil?: TratamientoHil | null
  orden_pagina_validado?: number | null
  estado?: string
}

interface ArchivoKardex {
  id: string
  archivo: File
  previewUrl: string
}

// Estados Globales
const articulos = ref<Articulo[]>([])
const articuloSeleccionado = ref<Articulo | null>(null)
const buscarTexto = ref('')
const filtroObservacion = ref('todos')
const errorMsg = ref('')
const mensajeExito = ref('')

// Vistas
const vistaActual = ref<'buscar' | 'crear' | 'historial' | 'subir_lote'>('buscar')
const subPestaña = ref<'historial' | 'hil' | 'grafo' | 'cobertura'>('historial')

// Historial y Errores
const movimientos = ref<Movimiento[]>([])
const erroresHIL = ref<Movimiento[]>([])
const cargandoHistorial = ref(false)
const loteSeleccionado = ref<number | null>(null)
const tandaSeleccionada = ref<number | null>(null)
const tandaActual = ref<number | null>(null)
const resumenTandas = ref<{ id: number; nombre: string; movimientos: number; escaneos: number }[]>([])
const movimientosTanda = computed(() => movimientos.value.filter(m => tandaSeleccionada.value === null || m.tanda === tandaSeleccionada.value))
watch(tandaSeleccionada, () => { loteSeleccionado.value = null })
async function cargarTandas() {
  try {
    const { data } = await api.get('/kardex/tandas')
    resumenTandas.value = data.tandas
    tandaActual.value = data.tanda_nuevas_cargas
  }
  catch { errorMsg.value = 'No se pudo cargar el resumen de tandas.' }
}
const lotesVisibles = computed(() =>
  [...new Set(movimientosTanda.value.map(m => m.lote_id).filter((id): id is number => id !== null))]
    .sort((a, b) => a - b)
)
const movimientosMostrados = computed(() => loteSeleccionado.value === null
  ? movimientosTanda.value
  : movimientosTanda.value.filter(m => m.lote_id === loteSeleccionado.value)
)

function numeroEscaneo(loteId: number | null): number {
  const todos = [...new Set(movimientos.value.map(m => m.lote_id).filter((id): id is number => id !== null))].sort((a, b) => a - b)
  return loteId === null ? 0 : todos.indexOf(loteId) + 1
}

// Subida de Lote
const archivos = ref<ArchivoKardex[]>([])
const ordenConfirmado = ref(false)
const lotePendiente = ref<{
  pendiente_id: string
  tanda: number
  articulo_nombre: string
  diferencias: { pagina: number; titulo_detectado: string }[]
} | null>(null)
const subiendo = ref(false)
const solicitudesCarga = ref<{ id: number; estado: string; tanda: number; lote_id: number | null; intento: number; reintentable: boolean }[]>([])
async function cargarSolicitudes() {
  if (!articuloSeleccionado.value) return
  try { solicitudesCarga.value = (await api.get(`/kardex/solicitudes?articulo_id=${articuloSeleccionado.value.id}`)).data }
  catch { /* la carga puede seguir; se conserva el mensaje principal de conexión */ }
}
const segundosProcesando = ref(0)
let relojCarga: ReturnType<typeof setInterval> | undefined

// Crear Artículo
const nuevoArticuloNombre = ref('')
const creandoArticulo = ref(false)

// Auditoría y Edición (HIL)
const movimientoRevisando = ref<Movimiento | null>(null)
const tipoHIL = ref('')
const estadoTratamientoHIL = ref('')
const categoriaHIL = ref('')
const erroresPorTanda = computed(() => erroresHIL.value.filter(m => tandaSeleccionada.value === null || m.tanda === tandaSeleccionada.value))
const categorizadosHIL = computed(() => erroresPorTanda.value.filter(m => m.tratamiento_hil?.estado === 'CATEGORIZADO_CON_MARCA').length)
const erroresFiltrados = computed(() => erroresPorTanda.value.filter(m =>
  (!tipoHIL.value || m.tipos_alerta.includes(tipoHIL.value)) &&
  (!estadoTratamientoHIL.value || (m.tratamiento_hil?.estado ?? 'POR_CATEGORIZAR') === estadoTratamientoHIL.value) &&
  (!categoriaHIL.value || m.tratamiento_hil?.categorias.includes(categoriaHIL.value))))
const auth = useAuthStore()
const route = useRoute()
const puedeCorregir = computed(() => auth.rol === 'Administrador' || auth.rol === 'Operador')
const puedeRevisarCobertura = computed(() => auth.rol === 'Administrador' || auth.rol === 'Auditor')
interface FilaCierre {
  movimiento_id: number; lote_id: number; pagina: number; orden_pagina: number; fila: number
  fecha_ocr: string | null; saldo_documental: number; ruta_imagen_respaldo: string | null
}
interface Cobertura {
  huella_fuente: string
  candidatos_cierre: FilaCierre[]
  fuente_cierre: { estado: string; seleccion: FilaCierre | null; propuesta: FilaCierre | null; revisado_por: number | null; revisado_en: string | null } | null
  continuidad: { orden: string; cierre_disponible: { lote_id: number; pagina: number; fecha_ocr: string; saldo_documental: number } | null; interrupciones_entre_lotes: { lote_anterior: number; lote_siguiente: number; saldo_esperado: number; saldo_documento: number }[] }
  evidencia_disponible: {
    lotes: { lote_id: number; tanda: number; paginas_declaradas: number; paginas_con_filas: number; movimientos: number }[]
    gestiones_con_filas: { gestion: number | null; movimientos: number }[]
    paginas_con_filas: number
    movimientos: number
  }
  revision: { estado: string; observacion: string; referencia: string | null; vigente: boolean; revisado_en: string | null }
  tramos: { id: number; gestion_desde: number; gestion_hasta: number; estado: string; paginas_faltantes: number | null; descripcion: string; referencia: string }[]
}
const cobertura = ref<Cobertura | null>(null)
const revisionCobertura = ref({ estado: 'SIN_CONFIRMAR', referencia: '', observacion: '' })
const filaCierre = ref<number | null>(null)
const evidenciaCierreRevisada = ref(false)
const candidatoCierre = computed(() => cobertura.value?.candidatos_cierre?.find(f => f.movimiento_id === filaCierre.value))
watch(filaCierre, () => { evidenciaCierreRevisada.value = false })
let consultaCobertura = 0
const tramoCobertura = ref({ gestion_desde: GESTION_DOCUMENTAL_HASTA, gestion_hasta: GESTION_DOCUMENTAL_HASTA, estado: 'PENDIENTE', paginas_faltantes: '', descripcion: '', referencia: '' })
const guardandoCobertura = ref(false)
async function cargarCobertura() {
  if (!articuloSeleccionado.value) return
  const id = articuloSeleccionado.value.id
  const consulta = ++consultaCobertura
  cobertura.value = null
  evidenciaCierreRevisada.value = false
  try {
    const datos = (await api.get(`/kardex/cobertura/${id}`)).data
    if (consulta !== consultaCobertura || articuloSeleccionado.value?.id !== id) return
    cobertura.value = datos
    const ultima = ultimaGestionDocumental(datos.evidencia_disponible?.gestiones_con_filas?.map((g: { gestion: number | null }) => g.gestion).filter((g: number | null): g is number => g !== null) ?? [])
    tramoCobertura.value = { gestion_desde: ultima || GESTION_DOCUMENTAL_HASTA, gestion_hasta: ultima || GESTION_DOCUMENTAL_HASTA, estado: 'PENDIENTE', paginas_faltantes: '', descripcion: '', referencia: '' }
    filaCierre.value = datos.fuente_cierre?.estado !== 'PROPUESTA' ? datos.fuente_cierre?.seleccion?.movimiento_id ?? null : null
    const r = cobertura.value?.revision
    if (r) revisionCobertura.value = { estado: r.estado, referencia: r.referencia ?? '', observacion: r.observacion === 'La cobertura todavía no ha sido revisada.' ? '' : r.observacion }
  } catch { if (consulta === consultaCobertura && articuloSeleccionado.value?.id === id) errorMsg.value = 'No se pudo consultar la cobertura documental.' }
}
async function guardarRevisionCobertura() {
  if (!articuloSeleccionado.value) return
  guardandoCobertura.value = true
  try {
    await api.put(`/kardex/cobertura/${articuloSeleccionado.value.id}/revision`, {
      ...revisionCobertura.value, cierre_movimiento_id: filaCierre.value,
      huella_fuente_esperada: cobertura.value?.huella_fuente,
      evidencia_revisada: evidenciaCierreRevisada.value,
    })
    await cargarCobertura()
    mensajeExito.value = 'Revisión de cobertura registrada.'
  } catch (err: any) { errorMsg.value = err.response?.data?.detail ?? 'No se pudo registrar la revisión.' }
  finally { guardandoCobertura.value = false }
}
async function guardarTramoCobertura() {
  if (!articuloSeleccionado.value) return
  guardandoCobertura.value = true
  try {
    await api.post(`/kardex/cobertura/${articuloSeleccionado.value.id}/tramos`, {
      ...tramoCobertura.value,
      paginas_faltantes: tramoCobertura.value.paginas_faltantes === '' ? null : Number(tramoCobertura.value.paginas_faltantes),
    })
    await cargarCobertura()
    tramoCobertura.value.descripcion = ''
    mensajeExito.value = 'Tramo documental registrado.'
  } catch (err: any) { errorMsg.value = err.response?.data?.detail ?? 'No se pudo registrar el tramo.' }
  finally { guardandoCobertura.value = false }
}
const limitesCarga = ref({ paginas: 20, mb_imagen: 20, mb_lote: 100 })
const imagenAuditoria = ref<string | null>(null)
const urlImagenAuditoria = computed(() => imagenAuditoria.value
  ? new URL(imagenAuditoria.value, new URL(api.defaults.baseURL ?? '/api/v1', window.location.origin).origin).href : '')


// Computed
const articulosFiltrados = computed(() => {
  const t = buscarTexto.value.toLowerCase()
  return articulos.value.filter(a => (a.nombre.toLowerCase().includes(t) || a.codigo.toLowerCase().includes(t))
    && (filtroObservacion.value === 'todos' || Boolean(a.observacion_hil?.observado) === (filtroObservacion.value === 'observados')))
})

onMounted(async () => {
  await Promise.all([cargarArticulos(), cargarTandas()])
  const tandaRuta = Number(route.query.tanda)
  if (resumenTandas.value.some(t => t.id === tandaRuta)) tandaSeleccionada.value = tandaRuta
  const destino = articulos.value.find(a => a.id === Number(route.query.articulo_id))
  if (destino) {
    const tab = route.query.tab
    seleccionarArticulo(destino, tab === 'hil' || tab === 'grafo' || tab === 'cobertura' ? tab : 'historial')
  }
  try { limitesCarga.value = (await api.get('/kardex/limites-carga')).data } catch { /* el servidor siempre verifica los límites */ }
})

onBeforeUnmount(() => {
  liberarPrevisualizaciones()
  if (relojCarga) clearInterval(relojCarga)
})

async function cargarArticulos() {
  try {
    const res = await api.get('/kardex/articulos')
    articulos.value = res.data
  } catch (err: any) {
    errorMsg.value = "Error al cargar el catálogo de artículos."
  }
}

function seleccionarArticulo(art: Articulo, tab: 'historial' | 'hil' | 'grafo' | 'cobertura' = 'historial') {
  articuloSeleccionado.value = art
  loteSeleccionado.value = null
  vistaActual.value = 'historial'
  cambiarPestaña(tab)
}

function irACrearArticulo() {
  articuloSeleccionado.value = null
  nuevoArticuloNombre.value = ''
  vistaActual.value = 'crear'
  mensajeExito.value = ''
  errorMsg.value = ''
}

function irABuscar() {
  articuloSeleccionado.value = null
  vistaActual.value = 'buscar'
  buscarTexto.value = ''
  cargarArticulos()
}

function irASubirLote() {
  limpiarArchivos()
  vistaActual.value = 'subir_lote'
  mensajeExito.value = ''
  errorMsg.value = ''
  cargarSolicitudes()
}

async function guardarNuevoArticulo() {
  if (!nuevoArticuloNombre.value.trim()) {
    errorMsg.value = "Debes ingresar un nombre para el artículo."
    return
  }
  creandoArticulo.value = true
  errorMsg.value = ''
  try {
    const res = await api.post('/kardex/articulos', { nombre: nuevoArticuloNombre.value })
    articuloSeleccionado.value = { ...res.data, alertas_rojas: 0, alertas_amarillas: 0 }
    mensajeExito.value = "Artículo registrado correctamente."
    vistaActual.value = 'subir_lote'
  } catch (err: any) {
    errorMsg.value = "Error al crear el artículo."
  } finally {
    creandoArticulo.value = false
  }
}

async function cargarHistorial() {
  if (!articuloSeleccionado.value) return
  cargandoHistorial.value = true
  errorMsg.value = ''
  try {
    const res = await api.get(`/kardex/historial/${articuloSeleccionado.value.id}`)
    movimientos.value = res.data
    if (loteSeleccionado.value !== null && !lotesVisibles.value.includes(loteSeleccionado.value)) {
      loteSeleccionado.value = null
    }
  } catch (err: any) {
    errorMsg.value = "Error al cargar el historial del kárdex."
  } finally {
    cargandoHistorial.value = false
  }
}

async function cargarErroresHIL() {
  if (!articuloSeleccionado.value) return
  cargandoHistorial.value = true
  try {
    const res = await api.get(`/kardex/errores?articulo_id=${articuloSeleccionado.value.id}`)
    erroresHIL.value = res.data
  } catch (err: any) {
    errorMsg.value = "Error al cargar la auditoría HIL."
  } finally {
    cargandoHistorial.value = false
  }
}

function cambiarPestaña(tab: 'historial' | 'hil' | 'grafo' | 'cobertura') {
  subPestaña.value = tab
  if (tab === 'historial') cargarHistorial()
  if (tab === 'hil') cargarErroresHIL()
  if (tab === 'cobertura') cargarCobertura()
}

// Logica subida de lote
function liberarPrevisualizaciones() {
  archivos.value.forEach(item => URL.revokeObjectURL(item.previewUrl))
}

function limpiarArchivos() {
  liberarPrevisualizaciones()
  archivos.value = []
  ordenConfirmado.value = false
}

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  limpiarArchivos()
  if (target.files) {
    const seleccion = Array.from(target.files)
    const limite = limitesCarga.value
    const formatos = ['image/jpeg', 'image/png', 'image/webp']
    if (seleccion.length > limite.paginas || seleccion.some(f => f.size > limite.mb_imagen * 1024 * 1024)
      || seleccion.reduce((s, f) => s + f.size, 0) > limite.mb_lote * 1024 * 1024) {
      errorMsg.value = `Límite: ${limite.paginas} páginas, ${limite.mb_imagen} MB por imagen y ${limite.mb_lote} MB por lote.`
      target.value = ''; return
    }
    if (seleccion.some(f => !formatos.includes(f.type))) {
      errorMsg.value = 'Utiliza fotografías JPEG, PNG o WebP.'; target.value = ''; return
    }
    errorMsg.value = ''
    archivos.value = seleccion.map((archivo, index) => ({
      id: `${archivo.name}-${archivo.lastModified}-${index}`,
      archivo,
      previewUrl: URL.createObjectURL(archivo)
    }))
  }
  target.value = ''
}

function moverArchivo(indice: number, desplazamiento: number) {
  const nuevoIndice = indice + desplazamiento
  if (nuevoIndice < 0 || nuevoIndice >= archivos.value.length) return
  const [elemento] = archivos.value.splice(indice, 1)
  archivos.value.splice(nuevoIndice, 0, elemento)
  ordenConfirmado.value = false
}

function eliminarArchivo(indice: number) {
  const [elemento] = archivos.value.splice(indice, 1)
  if (elemento) URL.revokeObjectURL(elemento.previewUrl)
  ordenConfirmado.value = false
}

async function subirLote() {
  if (subiendo.value || lotePendiente.value) return
  if (!articuloSeleccionado.value) return
  if (archivos.value.length === 0) return errorMsg.value = "Selecciona al menos una imagen."
  if (!tandaActual.value) return errorMsg.value = "Consulta la tanda actual antes de cargar fotografías."
  if (!ordenConfirmado.value) return errorMsg.value = "Confirma el orden físico de las páginas antes de procesarlas."
  
  subiendo.value = true
  segundosProcesando.value = 0
  relojCarga = setInterval(() => { segundosProcesando.value += 1 }, 1000)
  errorMsg.value = ''; mensajeExito.value = ''
  
  const formData = new FormData()
  formData.append('tanda', String(tandaActual.value))
  formData.append('articulo_id', articuloSeleccionado.value.id.toString())
  archivos.value.forEach(item => formData.append('archivos', item.archivo, item.archivo.name))

  try {
    // El proceso secuencial puede superar dos minutos con varias páginas y reintentos.
    const respuesta = await api.post('/kardex/upload-lote', formData, { timeout: 0 })
    if (respuesta.data.requiere_confirmacion) {
      lotePendiente.value = respuesta.data
      return
    }
    mensajeExito.value = respuesta.data.duplicado
      ? "Estas páginas ya estaban guardadas. Abajo se muestran sus movimientos; no se agregó ningún duplicado."
      : `Lote escaneado exitosamente en Tanda ${respuesta.data.tanda}.`
    tandaSeleccionada.value = respuesta.data.tanda ?? tandaActual.value
    loteSeleccionado.value = respuesta.data.lote_id ?? null
    await cargarTandas()
    limpiarArchivos()
    vistaActual.value = 'historial'
    cambiarPestaña('historial')
  } catch (err: any) {
    const detalle = err.response?.data?.detail
    if (typeof detalle === 'string') {
      errorMsg.value = detalle
    } else if (err.code === 'ECONNABORTED' || err.code === 'ETIMEDOUT') {
      errorMsg.value = 'Se agotó la espera de la conexión. El servidor podría seguir procesando el lote; revisa el historial antes de repetir la carga.'
    } else if (!err.response) {
      errorMsg.value = 'Se perdió la conexión con el servidor. No se pudo confirmar si el lote terminó. Revisa la conexión y el historial antes de volver a subirlo.'
    } else {
      errorMsg.value = `El servidor rechazó el lote (HTTP ${err.response.status}). Revisa el registro del backend para conocer la causa.`
    }
  } finally {
    if (relojCarga) clearInterval(relojCarga)
    relojCarga = undefined
    subiendo.value = false
    await cargarSolicitudes()
  }
}

// Logica HIL
async function decidirLote(confirmar: boolean) {
  if (!lotePendiente.value || subiendo.value) return
  subiendo.value = true
  errorMsg.value = ''
  try {
    const respuesta = await api.post(`/kardex/lotes-pendientes/${lotePendiente.value.pendiente_id}/decision`, { confirmar })
    lotePendiente.value = null
    if (confirmar) {
      tandaSeleccionada.value = respuesta.data.tanda ?? tandaActual.value
      await cargarTandas()
      limpiarArchivos()
      vistaActual.value = 'historial'
      cambiarPestaña('historial')
      mensajeExito.value = `Lote guardado en Tanda ${respuesta.data.tanda} con tu autorización de las diferencias de título.`
    } else {
      ordenConfirmado.value = false
      mensajeExito.value = 'Lote cancelado. Revisa las fotografías antes de volver a procesar.'
    }
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || 'No se pudo registrar la decisión. Puedes reintentar sin escanear otra vez.'
  } finally {
    subiendo.value = false
  }
}

function iniciarEdicionHIL(mov: Movimiento) {
  movimientoRevisando.value = mov
}

function cerrarEdicionHIL() {
  movimientoRevisando.value = null
}

async function guardarEdicionHIL() {
  cerrarEdicionHIL()
  mensajeExito.value = 'Revisión guardada con su motivo y autoría. Las alertas de fecha y saldo se evaluaron por separado.'
  await Promise.all([cargarErroresHIL(), cargarArticulos()])
}

function verFoto(ruta: string | null) {
  if (ruta) imagenAuditoria.value = '/' + ruta.replace(/\\/g, '/')
}
</script>

<template>
  <div class="kardex-continuo-view">
    <div v-if="lotePendiente" class="confirmacion-fondo">
      <section role="dialog" aria-modal="true" aria-labelledby="titulo-confirmacion" class="confirmacion-dialogo">
        <h2 id="titulo-confirmacion">Revisa los títulos antes de guardar</h2>
        <p>Artículo seleccionado: <strong>{{ lotePendiente.articulo_nombre }}</strong> · Tanda {{ lotePendiente.tanda }}</p>
        <p>Estas páginas tienen encabezados diferentes. Comprueba si son variantes del mismo artículo.</p>
        <ul>
          <li v-for="diferencia in lotePendiente.diferencias" :key="diferencia.pagina">
            Página {{ diferencia.pagina }}: {{ diferencia.titulo_detectado || '(sin título legible)' }}
          </li>
        </ul>
        <p>La extracción ya está conservada. Confirmar no vuelve a escanear las imágenes.</p>
        <p v-if="errorMsg" role="alert">{{ errorMsg }}</p>
        <button class="btn-primary" :disabled="subiendo" @click="decidirLote(true)">Confirmar: mismo artículo y guardar</button>
        <button class="btn-outline" :disabled="subiendo" @click="decidirLote(false)">Cancelar y revisar imágenes</button>
      </section>
    </div>
    <div class="header-nav">
      <router-link v-if="vistaActual === 'buscar'" to="/" class="btn-back"><i class="pi pi-arrow-left"></i> Panel Principal</router-link>
      <button v-else class="btn-back" @click="irABuscar" style="background:none;border:none;cursor:pointer;"><i class="pi pi-arrow-left"></i> Volver al Catálogo</button>
      
      <h1>Kárdex Digital Continuo</h1>
      <div style="flex-grow:1"></div>
      <router-link v-if="vistaActual === 'buscar'" to="/kardex/muestra-validacion" class="btn-outline">Validar muestra migrada</router-link>
      
      <button v-if="vistaActual === 'buscar' && puedeCorregir" class="btn-primary" @click="irACrearArticulo">
        + Nuevo Artículo
      </button>
    </div>
    
    <p v-if="errorMsg" class="alert alert-error">{{ errorMsg }}</p>
    <p v-if="mensajeExito" class="alert alert-success">{{ mensajeExito }}</p>

    <section v-if="vistaActual === 'buscar' || vistaActual === 'historial'" class="tandas-panel" aria-label="Tandas de digitalización">
      <strong>Archivo escaneado por tandas</strong>
      <p>Las nuevas fotografías se guardan en <strong>Tanda {{ tandaActual ?? 'por consultar' }}</strong>. El filtro muestra el historial y la revisión HIL del artículo seleccionado.</p>
      <div class="tandas-controles" role="group" aria-label="Filtrar tanda">
        <button :class="['tab-btn', { active: tandaSeleccionada === null }]" :aria-pressed="tandaSeleccionada === null" @click="tandaSeleccionada = null">Todas las tandas</button>
        <button v-for="t in resumenTandas" :key="t.id" :class="['tab-btn', { active: tandaSeleccionada === t.id }]" :aria-pressed="tandaSeleccionada === t.id" @click="tandaSeleccionada = t.id">{{ t.nombre }} · {{ t.movimientos }} movimientos</button>
      </div>
      <small>Los conteos abarcan todo el archivo. El catálogo de artículos es compartido.</small>
    </section>

    <!-- PANTALLA 1: BUSCADOR -->
    <div v-if="vistaActual === 'buscar'" class="pantalla-buscar">
      <BuscadorArticulos v-model="buscarTexto" placeholder="Buscar artículos escaneados por nombre o código…" />
      <label>Estado documental <select v-model="filtroObservacion"><option value="todos">Todos</option><option value="sin_observacion">Sin observación especial</option><option value="observados">Observados</option></select></label>

      <div class="lista-articulos">
        <button v-for="art in articulosFiltrados" :key="art.id" type="button" class="articulo-card" @click="seleccionarArticulo(art)">
          <div class="art-header">
            <div class="art-codigo">{{ art.codigo }}</div>
            <div class="art-badges">
              <span v-if="art.alertas_rojas > 0" class="badge-alert red" title="Errores Matemáticos">🔴 {{ art.alertas_rojas }}</span>
              <span v-if="art.alertas_amarillas > 0" class="badge-alert yellow" title="Clasificaciones Dudosas">🟡 {{ art.alertas_amarillas }}</span>
              <span v-if="art.alertas_rojas === 0 && art.alertas_amarillas === 0 && !art.observacion_hil?.observado" class="badge-alert green" title="Sin avisos pendientes">Sin avisos</span>
            </div>
          </div>
          <div class="art-nombre">{{ art.nombre }}</div>
          <small v-if="art.observacion_hil?.observado">Observado<span v-if="art.observacion_hil.excluir_entrenamiento"> · fuera del entrenamiento histórico</span></small>
        </button>
        <div v-if="articulosFiltrados.length === 0" class="empty-state">No se encontraron artículos que coincidan.</div>
      </div>
    </div>

    <!-- PANTALLA 2: CREAR ARTICULO -->
    <div v-if="vistaActual === 'crear'" class="pantalla-crear">
      <div class="form-container">
        <h3>Registrar Nuevo Artículo</h3>
        <p class="subtitle">Registra el nombre del artículo antes de subir sus fotografías de kárdex.</p>
        <label>Nombre del Artículo:</label>
        <input type="text" v-model="nuevoArticuloNombre" placeholder="Ej: MUSICA CHAPACA CD" @keyup.enter="guardarNuevoArticulo"/>
        <div class="actions">
          <button class="btn-outline" @click="irABuscar">Cancelar</button>
          <button class="btn-primary" @click="guardarNuevoArticulo" :disabled="creandoArticulo">
            {{ creandoArticulo ? 'Guardando...' : 'Crear y Escanear Lote' }}
          </button>
        </div>
      </div>
    </div>

    <!-- PANTALLA 3: SUBIR LOTE -->
    <div v-if="vistaActual === 'subir_lote' && articuloSeleccionado" class="pantalla-subida">
      <div class="context-header">
        <span class="label">Artículo destino:</span>
        <span class="value">[{{ articuloSeleccionado.codigo }}] {{ articuloSeleccionado.nombre }}</span>
      </div>
      <div class="upload-area">
        <h3>Subir Fotografías del Kárdex · Tanda {{ tandaActual ?? 'por consultar' }}</h3>
        <p>Esta carga se identificará como Tanda {{ tandaActual ?? 'por consultar' }}. Una fotografía ya guardada conserva su tanda original.</p>
        <section aria-label="Estado de cargas recientes">
          <button class="btn-outline btn-small" type="button" @click="cargarSolicitudes">Actualizar estado de cargas</button>
          <p v-for="solicitud in solicitudesCarga.slice(0, 5)" :key="solicitud.id">
            Solicitud {{ solicitud.id }} · {{ solicitud.estado }} · intento {{ solicitud.intento }}
            <span v-if="solicitud.lote_id"> · lote {{ solicitud.lote_id }} guardado</span>
            <span v-else-if="solicitud.reintentable"> · puedes seleccionar y enviar las mismas fotos para reanudar sin duplicar el lote</span>
            <span v-else-if="solicitud.estado === 'PROCESANDO'"> · espera; no envíes de nuevo mientras procesa</span>
          </p>
        </section>
        <div class="upload-controls">
          <input type="file" multiple accept="image/jpeg,image/png,image/webp" @change="handleFileChange" class="file-input" :disabled="subiendo"/>
          <button class="btn-primary" @click="subirLote" :disabled="subiendo || archivos.length === 0 || !ordenConfirmado">
            {{ subiendo ? 'Extrayendo con IA...' : 'Procesar Imágenes' }}
          </button>
        </div>
        <p class="orden-instruccion">JPEG, PNG o WebP · máximo {{ limitesCarga.paginas }} páginas, {{ limitesCarga.mb_imagen }} MB por imagen y {{ limitesCarga.mb_lote }} MB por lote. Se rechazan páginas repetidas dentro del lote antes de consumir IA.</p>
        <template v-if="archivos.length > 0">
          <p v-if="subiendo" role="status">
            Procesando {{ archivos.length }} fotografías · {{ Math.floor(segundosProcesando / 60) }} min {{ segundosProcesando % 60 }} s.
            Puede tardar varios minutos. Mantén esta pantalla abierta; no necesitas volver a enviar el lote.
          </p>
          <p class="orden-instruccion">
            Verifica que la página 1 sea la hoja físicamente más antigua. El LLM procesará
            exactamente este orden; las fechas no reorganizarán las filas.
          </p>
          <ol class="lista-paginas">
            <li v-for="(item, indice) in archivos" :key="item.id" class="pagina-preview">
              <span class="numero-pagina">{{ indice + 1 }}</span>
              <img :src="item.previewUrl" :alt="`Página ${indice + 1}: ${item.archivo.name}`"/>
              <div class="pagina-datos">
                <strong>Página {{ indice + 1 }}</strong>
                <span>{{ item.archivo.name }}</span>
              </div>
              <div class="pagina-acciones">
                <button class="btn-outline btn-small" :disabled="subiendo || indice === 0" @click="moverArchivo(indice, -1)" title="Mover antes">↑</button>
                <button class="btn-outline btn-small" :disabled="subiendo || indice === archivos.length - 1" @click="moverArchivo(indice, 1)" title="Mover después">↓</button>
                <button class="btn-outline btn-small quitar-pagina" :disabled="subiendo" @click="eliminarArchivo(indice)" title="Quitar imagen">×</button>
              </div>
            </li>
          </ol>
          <label class="confirmar-orden">
            <input type="checkbox" v-model="ordenConfirmado"/>
            Confirmo que las {{ archivos.length }} páginas pertenecen a este artículo y están
            ordenadas desde la más antigua hasta la más reciente.
          </label>
        </template>
      </div>
    </div>

    <!-- PANTALLA 4: VISTA DE ARTÍCULO (TABS) -->
    <div v-if="vistaActual === 'historial' && articuloSeleccionado" class="pantalla-historial">
      <div class="context-header with-action">
        <div>
          <span class="label">Activo:</span>
          <span class="value">[{{ articuloSeleccionado.codigo }}] {{ articuloSeleccionado.nombre }}</span>
        </div>
        <button v-if="puedeCorregir" class="btn-outline btn-small" @click="irASubirLote">+ Escanear más páginas · Tanda {{ tandaActual ?? 'por consultar' }}</button>
      </div>
      
      <!-- TABS -->
      <div class="tabs">
        <button :class="['tab-btn', { active: subPestaña === 'historial' }]" @click="cambiarPestaña('historial')">
          <i class="pi pi-list"></i> Historial Continuo
        </button>
        <button :class="['tab-btn', { active: subPestaña === 'hil' }]" @click="cambiarPestaña('hil')">
          <i class="pi pi-check-square"></i> Auditoría HIL 
          <span v-if="articuloSeleccionado.alertas_rojas + articuloSeleccionado.alertas_amarillas > 0" class="tab-badge">
            {{ articuloSeleccionado.alertas_rojas + articuloSeleccionado.alertas_amarillas }}
          </span>
        </button>
        <button :class="['tab-btn', { active: subPestaña === 'grafo' }]" @click="cambiarPestaña('grafo')">
          <i class="pi pi-share-alt"></i> Trazabilidad
        </button>
        <button :class="['tab-btn', { active: subPestaña === 'cobertura' }]" @click="cambiarPestaña('cobertura')">
          <i class="pi pi-folder"></i> Cobertura documental
        </button>
      </div>

      <div v-if="cargandoHistorial" class="loading-state">Cargando datos...</div>
      
      <!-- TAB 1: HISTORIAL -->
      <div v-else-if="subPestaña === 'historial'">
        <p v-if="movimientosTanda.length > 0" class="ref">
          {{ movimientosTanda.length }} movimientos en {{ lotesVisibles.length }} escaneos · {{ tandaSeleccionada === null ? 'Todas las tandas' : `Tanda ${tandaSeleccionada}` }}.
          Cada escaneo individual comienza en la página 1.
        </p>
        <div v-if="lotesVisibles.length > 1" class="tabs-container">
          <button :class="['tab-btn', { active: loteSeleccionado === null }]" @click="loteSeleccionado = null">Todos</button>
          <button v-for="id in lotesVisibles" :key="id"
            :class="['tab-btn', { active: loteSeleccionado === id }]"
            @click="loteSeleccionado = id">
            Escaneo {{ numeroEscaneo(id) }} ({{ movimientosTanda.filter(m => m.lote_id === id).length }})
          </button>
        </div>
        <div v-if="movimientosMostrados.length > 0" class="tabla-scroll"><table class="tabla-kardex">
          <thead>
            <tr>
              <th>Escaneo</th><th>Fecha</th><th>Detalle / Ref</th><th>Ingreso</th><th>Salida</th><th>Saldo</th><th>Nodo Clasificado</th><th>Auditoría</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="mov in movimientosMostrados" :key="mov.id" :class="{'fila-error': mov.tiene_error_saldo, 'fila-dudosa': mov.requiere_auditoria_nodo || mov.requiere_auditoria_referencia}">
              <td><strong>Tanda {{ mov.tanda }}</strong><br/>Escaneo {{ numeroEscaneo(mov.lote_id) }}<br/><small>Foto {{ mov.numero_pagina }}<span v-if="mov.orden_pagina_validado"> · orden validado {{ mov.orden_pagina_validado }}</span></small></td>
              <td>{{ mov.fecha_movimiento || 'Sin fecha completa' }}<small v-if="mov.fecha_documental_texto">Escrito: {{ mov.fecha_documental_texto }}</small><small v-if="mov.fecha_estado === 'ESTIMADA_HIL'" class="fecha-hallazgo">Fecha técnica · sin gestión confirmada</small><small v-if="mov.tiene_error_fecha" class="fecha-hallazgo">{{ mov.fecha_estado === 'PENDIENTE_HIL' ? 'Fecha por revisar' : mov.fecha_estado }}</small></td>
              <td>
                <strong>{{ mov.detalle }}</strong><br/>
                <span class="ref">Ref: {{ mov.referencia || '-' }} | Área: {{ mov.area || '-' }}</span>
                <MarcaDocumental :revision="mov.revision_documental" :tratamiento="mov.tratamiento_hil" />
              </td>
              <td>{{ mov.ingresos !== null ? mov.ingresos : '-' }}</td>
              <td>{{ mov.salidas !== null ? mov.salidas : '-' }}</td>
              <td><strong>{{ mov.saldo_registrado }}</strong></td>
              <td>
                {{ mov.nodo_grafo || '-' }}<br/>
                <small>{{ mov.area_estado }}</small>
              </td>
              <td>
                <button class="btn-outline btn-small" @click="verFoto(mov.ruta_imagen_respaldo)" title="Ver Foto">📸 Foto</button>
              </td>
            </tr>
          </tbody>
        </table></div>
        <div v-else class="empty-state">No hay registros para la tanda seleccionada. <button v-if="puedeCorregir" class="btn-primary" @click="irASubirLote">Escanear en Tanda {{ tandaActual ?? 'por consultar' }}</button></div>
      </div>

      <!-- TAB 2: AUDITORÍA HIL -->
      <div v-else-if="subPestaña === 'hil'">
        <p>{{ categorizadosHIL }} categorizados con marca · {{ erroresPorTanda.length - categorizadosHIL }} por categorizar o actualizar.</p>
        <p>Un aviso ya tratado puede conservar una diferencia del documento, una hipótesis o un dato sin confirmar. Abre la revisión documental para ver la decisión y su evidencia.</p>
        <div class="hil-filtros">
          <label>Tipo de revisión <select v-model="tipoHIL"><option value="">Todas</option><option value="saldo">Saldo</option><option value="fecha">Fecha</option><option value="area">Área / nodo</option><option value="referencia">Referencia</option></select></label>
          <label>Tratamiento <select v-model="estadoTratamientoHIL"><option value="">Todos</option><option value="CATEGORIZADO_CON_MARCA">Categorizados con marca</option><option value="POR_CATEGORIZAR">Por categorizar</option><option value="REQUIERE_RECATEGORIZAR">Revisar categoría tras cambios</option></select></label>
          <label>Categoría <select v-model="categoriaHIL"><option value="">Todas</option><option v-for="(etiqueta, valor) in categoriasHil" :key="valor" :value="valor">{{ etiqueta }}</option></select></label>
          <span>{{ erroresFiltrados.length }} filas con avisos visibles. Una fila puede tener varias marcas.</span>
        </div>
        <p v-if="cargandoHistorial">Cargando revisiones…</p>
        <div v-else-if="erroresFiltrados.length === 0" class="empty-state">
          <h3>Sin alertas pendientes para este filtro</h3>
          <p>Esto no equivale a una certificación humana integral del artículo.</p>
        </div>
        <div v-else class="tabla-scroll"><table class="tabla-kardex tabla-errores">
          <thead>
            <tr>
              <th>Alerta / tratamiento</th><th>Fecha</th><th>Texto de consulta (original conservado)</th><th>Ing/Sal</th><th>Saldo</th><th>Nodo Grafo Asignado</th><th>Acción HIL</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="err in erroresFiltrados" :key="err.id">
              <td style="font-size: 1.2rem; text-align: center;">
                <span v-for="tipo in err.tipos_alerta" :key="tipo" class="alerta-tipo">{{ tipo }}</span>
                <small class="fecha-hallazgo">{{ err.tratamiento_hil?.etiqueta ?? 'Por categorizar' }}</small>
              </td>
              <td><strong>Tanda {{ err.tanda }}</strong><br/>{{ err.fecha_movimiento || 'Sin fecha completa' }}<small v-if="err.fecha_documental_texto">Escrito: {{ err.fecha_documental_texto }}</small><small class="fecha-hallazgo">{{ err.fecha_estado }}</small><small v-if="err.fecha_original !== err.fecha_movimiento">Primera lectura: {{ err.fecha_original || 'Sin fecha' }}</small></td>
              <td class="detalle-col">
                <strong>Detalle:</strong> {{ err.detalle || '-' }} <br/>
                <MarcaDocumental :revision="err.revision_documental" :tratamiento="err.tratamiento_hil" />
                <strong>Ref:</strong> {{ err.referencia || '-' }} ({{ err.referencia_estado }}) |
                <strong>Área:</strong> {{ err.area || '-' }} ({{ err.area_estado }})
              </td>
              
                <td>I: {{ err.ingresos !== null ? err.ingresos : '-' }}<br/>S: {{ err.salidas !== null ? err.salidas : '-' }}</td>
                <td>
                  <span :class="{'error-val': err.tiene_error_saldo}">Registrado: {{ err.saldo_registrado }}</span><br/>
                  <span class="esperado-val" v-if="err.tiene_error_saldo">Calc: {{ err.saldo_calculado }}</span>
                </td>
                <td><span :class="{'nodo-dudoso': err.requiere_auditoria_nodo}">{{ err.nodo_grafo }}</span></td>
                <td><button v-if="puedeCorregir" class="btn-outline btn-small" @click="iniciarEdicionHIL(err)">Revisar evidencia</button><button v-else class="btn-outline btn-small" @click="verFoto(err.ruta_imagen_respaldo)">Ver evidencia</button></td>
            </tr>
          </tbody>
        </table></div>
      </div>

      <!-- TAB 3: GRAFO VISUAL -->
      <div v-else-if="subPestaña === 'cobertura'" class="form-container">
        <h3>Cobertura documental</h3>
        <button class="btn-outline btn-small" :disabled="guardandoCobertura" @click="cargarCobertura">Actualizar evidencia</button>
        <ObservacionHilArticulo v-if="articuloSeleccionado" :key="articuloSeleccionado.id" :articulo-id="articuloSeleccionado.id" :estado="articuloSeleccionado.observacion_hil" :editable="puedeRevisarCobertura" @guardado="estado => { if (articuloSeleccionado) articuloSeleccionado.observacion_hil = estado }" />
        <p>Las páginas y gestiones observadas muestran lo que se digitalizó. No prueban que el archivo del artículo esté completo.</p>
        <div v-if="cobertura">
          <p><strong>Disponible:</strong> {{ cobertura.evidencia_disponible.paginas_con_filas }} páginas con filas,
            {{ cobertura.evidencia_disponible.movimientos }} movimientos, en
            {{ cobertura.evidencia_disponible.lotes.length }} escaneos.</p>
          <p><strong>Gestiones observadas:</strong>
            {{ cobertura.evidencia_disponible.gestiones_con_filas.map(g => g.gestion ?? 'Sin gestión confirmada').join(', ') || 'ninguna' }}.
          </p>
          <p v-if="cobertura.continuidad.cierre_disponible"><strong>Saldo de cierre disponible:</strong>
            {{ cobertura.continuidad.cierre_disponible.saldo_documental }} · lote
            {{ cobertura.continuidad.cierre_disponible.lote_id }}, hoja
            {{ cobertura.continuidad.cierre_disponible.pagina }}. Es una base documental, no un conteo físico.</p>
          <p v-if="cobertura.continuidad.interrupciones_entre_lotes.length" role="alert">
            Hay {{ cobertura.continuidad.interrupciones_entre_lotes.length }} interrupción(es) de saldo entre escaneos; revisa las fotos antes de confirmar el cierre.
          </p>
          <ul v-if="cobertura.continuidad.interrupciones_entre_lotes.length">
            <li v-for="corte in cobertura.continuidad.interrupciones_entre_lotes" :key="`${corte.lote_anterior}-${corte.lote_siguiente}`">
              Lotes {{ corte.lote_anterior }} → {{ corte.lote_siguiente }}: se esperaba
              {{ corte.saldo_esperado }} y el documento indica {{ corte.saldo_documento }}.
            </li>
          </ul>
          <p><strong>Revisión:</strong> {{ cobertura.revision.estado }}
            <span v-if="!cobertura.revision.vigente && cobertura.revision.revisado_en"> · requiere revisar la evidencia o su vigencia</span>
            <span v-if="!cobertura.revision.revisado_en"> · aún sin revisión humana</span>
          </p>
          <p v-if="cobertura.revision.referencia">{{ cobertura.revision.observacion }} · Ref: {{ cobertura.revision.referencia }}</p>
          <p v-if="cobertura.fuente_cierre"><strong>Fuente del cierre:</strong> {{ cobertura.fuente_cierre.estado }}
            <span v-if="cobertura.fuente_cierre.revisado_por"> · responsable #{{ cobertura.fuente_cierre.revisado_por }} · {{ cobertura.fuente_cierre.revisado_en }}</span>
          </p>
          <p v-if="cobertura.fuente_cierre && ['DESACTUALIZADA', 'RETIRADA'].includes(cobertura.fuente_cierre.estado)" class="alert alert-warning">
            La selección anterior se conserva y requiere revisión. Las aperturas ya utilizadas mantienen su base.
          </p>
          <p v-if="cobertura.fuente_cierre?.propuesta && cobertura.fuente_cierre.propuesta.movimiento_id !== cobertura.fuente_cierre.seleccion?.movimiento_id">
            Propuesta por orden de carga: lote {{ cobertura.fuente_cierre.propuesta.lote_id }}, hoja {{ cobertura.fuente_cierre.propuesta.pagina }},
            fila {{ cobertura.fuente_cierre.propuesta.fila }} · {{ cobertura.fuente_cierre.propuesta.fecha_ocr }} · saldo {{ cobertura.fuente_cierre.propuesta.saldo_documental }}.
            Revisa su posición en el archivo antes de sustituir el cierre.
            <button v-if="cobertura.fuente_cierre.propuesta.ruta_imagen_respaldo" class="btn-outline btn-small" @click="verFoto(cobertura.fuente_cierre.propuesta.ruta_imagen_respaldo)">Ver foto de la propuesta</button>
          </p>
          <h4>Periodos declarados</h4>
          <ul v-if="cobertura.tramos.length">
            <li v-for="tramo in cobertura.tramos" :key="tramo.id">
              {{ tramo.gestion_desde }}–{{ tramo.gestion_hasta }} · {{ tramo.estado }}
              <span v-if="tramo.paginas_faltantes !== null"> · {{ tramo.paginas_faltantes }} páginas faltantes</span>
              · {{ tramo.descripcion }} · Ref: {{ tramo.referencia }}
            </li>
          </ul>
          <p v-else>No hay periodos faltantes o confirmados declarados todavía.</p>
          <template v-if="puedeRevisarCobertura">
            <h4>Registrar revisión del artículo</h4>
            <div class="form-group"><label>Estado</label>
              <select v-model="revisionCobertura.estado">
                <option value="SIN_CONFIRMAR">Sin confirmar</option>
                <option value="PARCIAL">Parcial</option>
                <option value="CIERRE_CONFIRMADO">Último cierre documental confirmado</option>
              </select>
            </div>
            <template v-if="revisionCobertura.estado === 'CIERRE_CONFIRMADO'">
              <div class="form-group"><label for="fila-cierre">Fila que acredita el cierre documental</label>
                <select id="fila-cierre" v-model="filaCierre">
                  <option :value="null">Seleccionar una fila tras revisar las hojas</option>
                  <option v-for="fila in cobertura.candidatos_cierre" :key="fila.movimiento_id" :value="fila.movimiento_id">
                    Lote {{ fila.lote_id }} · hoja {{ fila.pagina }} · orden {{ fila.orden_pagina }} · fila {{ fila.fila }} · {{ fila.fecha_ocr ?? 'sin fecha' }} · saldo {{ fila.saldo_documental }}
                  </option>
                </select>
              </div>
              <button v-if="candidatoCierre?.ruta_imagen_respaldo" class="btn-outline btn-small" @click="verFoto(candidatoCierre.ruta_imagen_respaldo)">Ver foto de la fila seleccionada</button>
              <label><input v-model="evidenciaCierreRevisada" type="checkbox" :disabled="!candidatoCierre?.ruta_imagen_respaldo" />
                Revisé la foto y el periodo y confirmo que esta fila acredita el cierre.
              </label>
            </template>
            <div class="form-group"><label>Referencia de revisión</label><input v-model="revisionCobertura.referencia" placeholder="Acta, carpeta o documento" /></div>
            <div class="form-group"><label>Observación</label><textarea v-model="revisionCobertura.observacion" placeholder="Qué se revisó y qué queda pendiente" /></div>
            <button class="btn-primary" :disabled="guardandoCobertura || (revisionCobertura.estado === 'CIERRE_CONFIRMADO' && (!filaCierre || !evidenciaCierreRevisada))" @click="guardarRevisionCobertura">Guardar revisión</button>
            <h4>Registrar periodo pendiente o revisado</h4>
            <div class="form-group"><label>Gestión desde</label><input v-model.number="tramoCobertura.gestion_desde" type="number" min="1900" max="2100" /></div>
            <div class="form-group"><label>Gestión hasta</label><input v-model.number="tramoCobertura.gestion_hasta" type="number" min="1900" max="2100" /></div>
            <div class="form-group"><label>Estado</label><select v-model="tramoCobertura.estado">
              <option value="PENDIENTE">Pendiente</option><option value="SIN_CONFIRMAR">Sin confirmar</option><option value="CONFIRMADO">Confirmado</option>
            </select></div>
            <div class="form-group"><label>Páginas faltantes (si se conocen)</label><input v-model="tramoCobertura.paginas_faltantes" type="number" min="0" /></div>
            <div class="form-group"><label>Detalle</label><textarea v-model="tramoCobertura.descripcion" placeholder="Hojas o periodo que faltan o que se verificaron" /></div>
            <div class="form-group"><label>Referencia</label><input v-model="tramoCobertura.referencia" placeholder="Acta, carpeta o documento" /></div>
            <button class="btn-primary" :disabled="guardandoCobertura" @click="guardarTramoCobertura">Registrar periodo</button>
          </template>
        </div>
      </div>
      <div v-else-if="subPestaña === 'grafo'">
        <TrazabilidadArticulo :key="articuloSeleccionado.id" :articulo-id="articuloSeleccionado.id" ambito-inicial="HISTORICO" />
      </div>
    </div>

    <RevisionHil v-if="movimientoRevisando" :key="movimientoRevisando.id" :movimiento="movimientoRevisando" @guardar="guardarEdicionHIL" @cerrar="cerrarEdicionHIL" />

    <!-- Visor de fotos HIL Modal -->
    <div v-if="imagenAuditoria" class="visor-evidencia">
      <div class="visor-header">
        <h4>Evidencia Física</h4>
        <button class="btn-close" @click="imagenAuditoria = null">✖</button>
      </div>
      <div class="visor-body">
        <img :src="urlImagenAuditoria" alt="Hoja de Kárdex" class="evidencia-img" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.fecha-hallazgo { display: block; color: #985b1e; font-size: .75rem; }
.hil-filtros { display: flex; align-items: center; gap: 1rem; padding: 1rem 0; flex-wrap: wrap; }
.hil-filtros select { margin-left: .5rem; padding: .4rem; }
.alerta-tipo { display: inline-block; padding: .2rem .4rem; margin: .2rem; background: #fff0dd; color: #8f5419; border-radius: 5px; font-size: .75rem; }
.kardex-continuo-view {
  background: var(--bg-color);
  padding: 2.5rem;
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  max-width: 1300px;
  margin: 2.5rem auto;
  position: relative;
}
.btn-back {
  font-size: 1rem;
  color: var(--text-secondary);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}
.btn-back:hover { color: var(--primary); }
.header-nav { display: flex; align-items: center; margin-bottom: 2rem; border-bottom: 1px solid var(--border-color); padding-bottom: 1.5rem; gap: 1rem;}
.header-nav h1 { margin: 0; }

/* Buscador */
.lista-articulos { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1rem; }
.articulo-card { border: 1px solid var(--border-color); padding: 1.25rem; border-radius: var(--radius); cursor: pointer; transition: all 0.2s; background: var(--bg-body); }
.articulo-card:hover { border-color: var(--primary); background: var(--bg-subtle); transform: translateY(-2px); }
.art-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
.art-codigo { font-size: 0.8rem; color: var(--text-secondary); font-weight: 600; }
.art-nombre { font-size: 1.1rem; font-weight: 500; color: var(--text-primary); }
.badge-alert { font-size: 0.75rem; padding: 0.2rem 0.4rem; border-radius: 4px; font-weight: bold; margin-left: 0.3rem;}
.badge-alert.red { background: #fef2f2; color: #991b1b; }
.badge-alert.yellow { background: #fefce8; color: #854d0e; }
.badge-alert.green { background: #ecfdf5; color: #065f46; }

/* Orden previo de páginas */
.confirmacion-fondo { position: fixed; inset: 0; z-index: 1100; background: #0008; display: grid; place-items: center; padding: 1rem; }
.confirmacion-dialogo { background: var(--bg-body); padding: 1.5rem; border-radius: 12px; max-width: 720px; max-height: 90vh; overflow: auto; }
.confirmacion-dialogo button { margin: 0.5rem; }
.orden-instruccion { margin: 1rem 0; padding: 0.85rem 1rem; border-left: 4px solid #2563eb; background: #eff6ff; color: #1e3a8a; }
.lista-paginas { list-style: none; margin: 1rem 0; padding: 0; display: grid; gap: 0.75rem; }
.pagina-preview { display: flex; align-items: center; gap: 1rem; padding: 0.75rem; border: 1px solid var(--border-color); border-radius: var(--radius); background: var(--bg-body); }
.pagina-preview img { width: 72px; height: 92px; object-fit: cover; border: 1px solid var(--border-color); border-radius: 4px; }
.numero-pagina { display: grid; place-items: center; min-width: 2rem; height: 2rem; border-radius: 999px; background: var(--primary); color: white; font-weight: 700; }
.pagina-datos { display: flex; flex: 1; min-width: 0; flex-direction: column; gap: 0.2rem; }
.pagina-datos span { overflow: hidden; color: var(--text-secondary); text-overflow: ellipsis; white-space: nowrap; }
.pagina-acciones { display: flex; gap: 0.35rem; }
.quitar-pagina { color: #991b1b; }
.confirmar-orden { display: flex; align-items: flex-start; gap: 0.65rem; margin-top: 1rem; padding: 1rem; border-radius: var(--radius); background: #f8fafc; font-weight: 600; cursor: pointer; }
.confirmar-orden input { width: 1.1rem; height: 1.1rem; margin-top: 0.15rem; }

/* Tabs */
.tabs { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border-color); }
.tabs-container { display: flex; flex-wrap: wrap; gap: 0.25rem; margin-bottom: 1rem; border-bottom: 1px solid var(--border-color); }
.tab-btn { background: none; border: none; padding: 1rem 1.5rem; font-size: 1rem; color: var(--text-secondary); cursor: pointer; border-bottom: 3px solid transparent; transition: all 0.2s; display: flex; align-items: center; gap: 0.5rem; }
.tab-btn:hover { color: var(--primary); }
.tab-btn.active { color: var(--primary); border-bottom-color: var(--primary); font-weight: 600; }
.tab-badge { background: #ef4444; color: white; border-radius: 10px; padding: 0.1rem 0.5rem; font-size: 0.75rem; font-weight: bold; }

/* Tabla HIL */
.detalle-col { max-width: 250px; font-size: 0.85rem; color: var(--text-secondary); line-height: 1.3; }
.error-val { color: #991b1b; font-weight: bold; }
.esperado-val { color: #065f46; font-weight: bold; }
.nodo-dudoso { background: #fef08a; padding: 0.2rem 0.5rem; border-radius: 4px; color: #854d0e; font-weight: 600; font-size: 0.85rem; }
.text-edit { width: 100% !important; font-size: 0.85rem !important; }
.inline-edit { width: 80px; padding: 0.3rem !important; font-size: 0.9rem; }
.fila-editando { background: #fffbea !important; }
.fila-error td { background-color: #fdf5f5; }
.fila-dudosa td { background-color: #fefce8; }
.mb-1 { margin-bottom: 0.25rem; }
.mt-1 { margin-top: 0.25rem; }

/* Visor Fixed */
.visor-evidencia { position: fixed; bottom: 2rem; right: 2rem; width: 500px; max-height: 600px; background: var(--bg-body); border: 1px solid var(--border-color); border-radius: var(--radius); box-shadow: 0 10px 25px rgba(0,0,0,0.15); display: flex; flex-direction: column; z-index: 1000; overflow: hidden; }
.visor-header { background: var(--bg-subtle); padding: 1rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); }
.visor-header h4 { margin: 0; font-size: 1rem; color: var(--text-primary); }
.btn-close { background: none; border: none; font-size: 1.2rem; cursor: pointer; color: var(--text-muted); }
.visor-body { padding: 1rem; overflow: auto; display: flex; justify-content: center; background: #e5e5e5; }
.evidencia-img { max-width: 100%; height: auto; border-radius: 4px; }

/* Grafo */

/* Generales */
.context-header { background: var(--bg-subtle); padding: 1rem 1.5rem; border-radius: var(--radius); margin-bottom: 1.5rem; border: 1px solid var(--border-color); }
.context-header.with-action { display: flex; justify-content: space-between; align-items: center; }
.empty-state { text-align: center; padding: 4rem; color: var(--text-secondary); background: #f8fafc; border-radius: var(--radius); border: 1px dashed var(--border-color); }
.alert { padding: 1rem; border-radius: 6px; margin-bottom: 1.5rem; }
.alert-error { background-color: #fdf2f2; color: #991b1b; }
.alert-success { background-color: #ecfdf5; color: #065f46; }
.tandas-panel { margin-bottom: 1.5rem; padding: 1rem; border: 1px solid var(--border-color); border-radius: var(--radius); }
.tandas-panel p { margin: .5rem 0; }
.tandas-controles { display: flex; flex-wrap: wrap; gap: .5rem; margin: .75rem 0; }
.tandas-controles .tab-btn { border: 1px solid var(--border-color); border-radius: 6px; }
.tabla-scroll { max-width: 100%; overflow-x: auto; }
.tandas-controles .tab-btn[aria-pressed="true"] { background: #e8f0fc; outline: 2px solid #2563eb; outline-offset: -2px; }
@media (max-width: 640px) {
  .kardex-continuo-view { min-width: 0; }
  .lista-articulos { grid-template-columns: minmax(0, 1fr); }
  .tabs { flex-wrap: wrap; }
  .context-header.with-action { flex-direction: column; align-items: flex-start; gap: .75rem; }
}
</style>
