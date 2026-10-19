<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import BuscadorArticulos from '@/components/BuscadorArticulos.vue'
import TrazabilidadArticulo from '@/components/TrazabilidadArticulo.vue'

interface Articulo {
  id: number
  nombre: string
  codigo: string
  alertas_rojas: number
  alertas_amarillas: number
  observacion_hil?: { observado: boolean; excluir_entrenamiento: boolean; motivo: string } | null
  stock_actual: number | null
  apertura: { cantidad_inicial: number; cantidad_actual: number; ultimo_moderno_id: number;
    aprobado_por: number; aprobado_en: string; referencia_documento: string; justificacion: string;
    origen: 'CONTEO_FISICO' | 'KARDEX_HISTORICO'; movimiento_historico_id: number | null; lote_historico_id: number | null } | null
  base_kardex: { saldo: number; movimiento_id: number; lote_id: number; fecha_movimiento: string;
    saldo_documental?: number | null; origen_saldo?: string; origen_fecha?: string; hallazgos_documentales?: string[];
    operable: boolean; motivo_bloqueo: string | null } | null
  corte_operativo?: { fecha_inicio: string; estado: string; movimientos_previos_no_registrados: string } | null
  diferencia_documental?: { saldo_base_congelada: number; saldo_cierre_disponible: number; diferencia: number } | null
  conciliacion_inicial?: { fecha_conteo: string; cantidad_base: number; cantidad_fisica: number; diferencia: number; ajuste_movimiento_id: number | null } | null
}

interface Movimiento {
  id: number
  fecha_movimiento: string
  detalle: string
  ingresos: number | null
  salidas: number | null
  saldo_registrado: number
  nodo_grafo: string | null
  observaciones: string | null
  usuario_operador: string | null
  encargado_id: number | null
  encargado_nombre: string | null
  area_operativa_id: number | null
  registrado_en: string | null
  ocurrido_en: string | null
  solicitud_id: string | null
  alertas_control: { codigo: string; nivel: string; mensaje: string }[] | null
  justificacion_alertas: string | null
  tipo_operacion: string | null
  receptor: string | null
  receptor_tipo: string | null
  ciudad_feria: string | null
  canal_venta: string | null
  motivo_baja: string | null
  referencia_documento: string | null
  movimiento_origen_id: number | null
  devuelto_por: string | null
  corrige_movimiento_id: number | null
  cantidad_anterior: number | null
  cantidad_corregida: number | null
  motivo_correccion: string | null
  autorizado_por_id: number | null
  estado?: string | null
}

interface NodoCatalogo {
  valor: string
  etiqueta: string
  grupo: string
}

interface Feria {
  id: number
  nombre: string
  ciudad: string
}

interface Encargado {
  id: number
  nombre: string
}

interface DistribucionArea {
  total_institucional: number | null
  sin_ubicacion_confirmada: number | null
  en_custodia_externa: number | null
  areas: { area_id: number; area: string; cantidad: number }[]
  estado: string
}

interface EventoCustodia {
  id: number; tipo: 'VENTA' | 'RETORNO'; cantidad: number;
  comprador: string | null; area_destino: string | null;
  ocurrido_en: string; registrado_en: string; referencia_documento: string;
  encargado_id: number; registrado_por: number;
  total_institucional_despues: number; cantidad_fuera_despues: number
  alertas_control?: AlertaControl[] | null; justificacion_alertas?: string | null
}

interface CustodiaExterna {
  id: number; tipo: 'FERIA' | 'CONSIGNACION'; estado: 'ABIERTA' | 'CERRADA';
  area_origen: string; receptor_nombre: string; receptor_tipo: string;
  ubicacion_externa: string; ciudad: string | null;
  cantidad_entregada: number; cantidad_fuera: number;
  cantidad_vendida: number; cantidad_devuelta: number;
  referencia_documento: string; ocurrido_en: string; registrado_en: string;
  encargado_id: number; registrado_por: number; eventos: EventoCustodia[]
  alertas_control?: AlertaControl[] | null; justificacion_alertas?: string | null
}

interface TransferenciaArea {
  id: number; solicitud_id: string; area_origen_id: number; area_destino_id: number;
  area_origen: string; area_destino: string; cantidad: number; total_institucional: number;
  encargado_id: number; registrado_por: number; ocurrido_en: string; registrado_en: string;
  referencia_documento: string; observaciones: string
  alertas_control?: AlertaControl[] | null; justificacion_alertas?: string | null
}

interface KardexDigital {
  estado: 'SIN_BASE' | 'BASE_DOCUMENTAL_SIN_CORTE' | 'OPERATIVO'
  base: { cantidad: number; origen: string; movimiento_historico_id: number | null;
    lote_historico_id: number | null; fecha_corte: string | null;
    referencia_documento: string | null } | null
  eventos: { clase: 'OPERACION' | 'TRANSFERENCIA' | 'CUSTODIA_ENTREGA' | 'CUSTODIA_VENTA' | 'CUSTODIA_RETORNO'; id: number;
    fecha_operacion: string | null; fecha_documental: string | null;
    fecha_registro: string | null; descripcion: string; ingreso: number; salida: number;
    cantidad_original: number; cantidad_transferida: number;
    area_origen: string | null; area_destino: string | null;
    documento: string | null; encargado: string | null; registrador: string | null;
    receptor: string | null; movimiento_origen_id: number | null;
    devuelto_por: string | null; custodia_id: number | null;
    corrige_movimiento_id: number | null; motivo_correccion: string | null;
    cantidad_anterior: number | null; cantidad_corregida: number | null;
    estado: string; saldo_institucional: number; alertas_control?: AlertaControl[] | null;
    justificacion_alertas?: string | null }[]
  saldo_final: number | null
  integridad: boolean | null
}

interface ConciliacionInicial {
  estado: 'DISPONIBLE' | 'NO_DISPONIBLE' | 'REGISTRADA'
  motivo?: string | null
  cantidad_base?: number | null
  registro?: { cantidad_base: number; cantidad_fisica: number; diferencia: number;
    fecha_conteo: string; referencia_documento: string; justificacion: string;
    ajuste_movimiento_id: number | null; areas: { area_id: number; area: string; cantidad: number }[] } | null
}

interface AlertaControl {
  codigo: string
  nivel: string
  mensaje: string
}

const auth = useAuthStore()
const esAdmin = computed(() => auth.rol === 'Administrador')
const puedeOperar = computed(() => esAdmin.value || auth.rol === 'Operador')
const aperturaForm = ref({ cantidad: 0, referencia_documento: '', justificacion: '', conteo_verificado: false })
const aprobando = ref(false)
async function aprobarApertura() {
  if (!articuloSeleccionado.value || aprobando.value) return
  const articulo = articuloSeleccionado.value
  aprobando.value = true
  errorMsg.value = ''
  try {
    const { data } = await api.post(`/kardex/articulos/${articulo.id}/apertura`, aperturaForm.value)
    articulo.apertura = data
    articulo.stock_actual = data.cantidad_actual
    transferenciaForm.value.fecha_operacion_local = ahoraBoliviaLocal()
    mensajeExito.value = 'Apertura aprobada. Ya puedes registrar operaciones con este stock.'
    await cargarExistenciasArea()
    await cargarConciliacion()
    await cargarKardexDigital()
  } catch (err: any) {
    errorMsg.value = typeof err.response?.data?.detail === 'string' ? err.response.data.detail : 'No se pudo aprobar la apertura. Revisa los datos y consulta el artículo antes de reintentar.'
  } finally {
    aprobando.value = false
  }
}
const articulos = ref<Articulo[]>([])
const buscarTexto = ref('')
const filtroObservacion = ref('todos')
const errorMsg = ref('')
const mensajeExito = ref('')

const vistaActual = ref<'buscar' | 'detalle' | 'transaccion' | 'nuevo_producto'>('buscar')
const articuloSeleccionado = ref<Articulo | null>(null)
const mostrarTrazabilidad = ref(false)

// Datos para Nuevo Producto
const nuevoProducto = ref({ nombre: '' })
const creandoProducto = ref(false)

// Catálogos
const nodosDisponibles = ref<NodoCatalogo[]>([])
const ferias = ref<Feria[]>([])
const encargados = ref<Encargado[]>([])
const areasOperativas = ref<{ id: number; nombre: string }[]>([])
const existenciasArea = ref<DistribucionArea | null>(null)
const conciliacionInicial = ref<ConciliacionInicial | null>(null)
const guardandoConciliacion = ref(false)
const conteosArea = ref<Record<number, number>>({})
const conciliacionForm = ref({ fecha_conteo: '', encargado_id: '' as number | '',
  referencia_documento: '', justificacion: '', alcance_total: false, conteo_verificado: false })
const asignandoArea = ref(false)
const asignacionArea = ref({ area_id: '' as number | '', cantidad: 1, encargado_id: '' as number | '', referencia_documento: '', justificacion: '' })
const transferenciasArea = ref<TransferenciaArea[]>([])
const custodiasExternas = ref<CustodiaExterna[]>([])
const guardandoCustodia = ref(false)
const guardandoEventoCustodia = ref<number | null>(null)
const entregaExternaForm = ref({ solicitud_id: crypto.randomUUID(), tipo: 'FERIA' as 'FERIA' | 'CONSIGNACION',
  area_origen_id: '' as number | '', receptor_nombre: '', receptor_tipo: 'INSTITUCION' as 'PERSONA' | 'INSTITUCION',
  ubicacion_externa: '', ciudad: '', cantidad: 1, encargado_id: '' as number | '',
  fecha_operacion_local: '', referencia_documento: '', observaciones: '' })
const eventoCustodiaForms = ref<Record<number, { solicitud_id: string; tipo: 'VENTA' | 'RETORNO';
  cantidad: number; comprador: string; area_destino_id: number | ''; encargado_id: number | '';
  fecha_operacion_local: string; referencia_documento: string; observaciones: string }>>({})
const alertasEntregaExterna = ref<AlertaControl[]>([])
const firmaEntregaExterna = ref('')
const motivoEntregaExterna = ref('')
const alertasEventosCustodia = ref<Record<number, AlertaControl[]>>({})
const firmasEventosCustodia = ref<Record<number, string>>({})
const motivosEventosCustodia = ref<Record<number, string>>({})
watch(entregaExternaForm, () => {
  alertasEntregaExterna.value = []
  firmaEntregaExterna.value = ''
  motivoEntregaExterna.value = ''
}, { deep: true })
watch(eventoCustodiaForms, () => {
  alertasEventosCustodia.value = {}
  firmasEventosCustodia.value = {}
  motivosEventosCustodia.value = {}
}, { deep: true })
const kardexDigital = ref<KardexDigital | null>(null)
const descargandoKardex = ref(false)
const guardandoTransferencia = ref(false)
const politicaControl = ref<{ version: string; hora_inicio: number; hora_fin: number;
  cantidad_extrema: number; porcentaje_mayoritario: number; stock_minimo_mayoritario: number;
  factor_atipico: number; min_comparables: number; min_cantidad_atipica: number;
  repeticion_minutos: number; registro_tardio_horas: number } | null>(null)
const alertasTransferencia = ref<AlertaControl[]>([])
const firmaTransferencia = ref('')
const motivoTransferencia = ref('')
const transferenciaForm = ref({ solicitud_id: '', area_origen_id: '' as number | '',
  area_destino_id: '' as number | '', cantidad: 1, encargado_id: '' as number | '',
  fecha_operacion_local: '', referencia_documento: '', observaciones: '' })
watch(transferenciaForm, () => {
  alertasTransferencia.value = []; firmaTransferencia.value = ''; motivoTransferencia.value = ''
}, { deep: true })
const operacionesCatalogo = ref<{ valor: string; direccion: string; requiere_receptor: boolean; habilitada: boolean; motivo_pendiente?: string }[]>([])
const salidasDevolvibles = ref<{ id: number; tipo_operacion: string; receptor: string | null;
  cantidad_original: number; cantidad_devuelta: number; cantidad_pendiente: number;
  referencia_documento: string | null; ocurrido_en: string | null }[]>([])
const cargandoSalidasDevolvibles = ref(false)
const errorSalidasDevolvibles = ref(false)

// Datos para Transacción Enriquecida
const creandoTransaccion = ref(false)
const fechaOperacionEditada = ref(false)
const solicitudTransaccion = ref('')
const alertasPendientes = ref<AlertaControl[]>([])
const firmaAlertas = ref('')
const motivoAlertas = ref('')
const tx = ref({
  tipo: 'salida', 
  cantidad: 1, 
  encargado_id: '' as number | '',
  area_operativa_id: '' as number | '',
  tipo_operacion: '', 
  area_destino: '',
  receptor: '',
  receptor_tipo: '',
  feria_id: '' as number | '',
  ciudad_feria: '',
  canal_venta: '',
  motivo_baja: '',
  movimiento_origen_id: '' as number | '',
  devuelto_por: '',
  referencia: '',
  fecha_operacion_local: '',
  observaciones: ''
})

// Historial moderno
const movimientosModernos = ref<Movimiento[]>([])
const cargandoHistorial = ref(false)
const movimientoRectificado = ref<number | null>(null)
const guardandoCorreccion = ref(false)
const correccionForm = ref({ solicitud_id: crypto.randomUUID(), cantidad_corregida: 0,
  motivo: '', referencia_documento: '' })
const guardandoAjuste = ref(false)
const ajusteForm = ref({ solicitud_id: crypto.randomUUID(), direccion: 'ingreso' as 'ingreso' | 'salida',
  cantidad: 1, area_id: '' as number | '', encargado_id: '' as number | '',
  motivo: '', referencia_documento: '' })
watch(() => [correccionForm.value.cantidad_corregida, correccionForm.value.motivo,
  correccionForm.value.referencia_documento], () => { correccionForm.value.solicitud_id = crypto.randomUUID() })
watch(() => [ajusteForm.value.direccion, ajusteForm.value.cantidad, ajusteForm.value.area_id,
  ajusteForm.value.encargado_id, ajusteForm.value.motivo, ajusteForm.value.referencia_documento],
  () => { ajusteForm.value.solicitud_id = crypto.randomUUID() })

const articulosFiltrados = computed(() => {
  const t = buscarTexto.value.toLowerCase()
  return articulos.value.filter(a => (a.nombre.toLowerCase().includes(t) || a.codigo.toLowerCase().includes(t))
    && (filtroObservacion.value === 'todos' || Boolean(a.observacion_hil?.observado) === (filtroObservacion.value === 'observados')))
})

const areasCatalogo = computed(() => nodosDisponibles.value.filter(n => n.grupo === 'Departamentos'))
const totalContado = computed(() => areasOperativas.value.reduce((total, area) => total + Number(conteosArea.value[area.id] || 0), 0))
const direccionEsperada = computed<'ingreso' | 'salida' | null>(() => {
  const direccion = operacionesCatalogo.value.find(o => o.valor === tx.value.tipo_operacion)?.direccion
  return direccion === 'ingreso' || direccion === 'salida' ? direccion : null
})
const salidaSeleccionada = computed(() => salidasDevolvibles.value.find(s => s.id === tx.value.movimiento_origen_id))
watch(direccionEsperada, valor => { if (valor) tx.value.tipo = valor })

function fechaRegistro(fecha: string | null) {
  return fecha ? new Intl.DateTimeFormat('es-BO', {
    timeZone: 'America/La_Paz', dateStyle: 'short', timeStyle: 'short'
  }).format(new Date(fecha)) : 'Hora no registrada'
}

function ahoraBoliviaLocal() {
  const partes = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/La_Paz', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23'
  }).formatToParts(new Date())
  const valor = (tipo: string) => partes.find(parte => parte.type === tipo)?.value || ''
  return `${valor('year')}-${valor('month')}-${valor('day')}T${valor('hour')}:${valor('minute')}:${valor('second')}`
}

watch(tx, () => {
  alertasPendientes.value = []
  firmaAlertas.value = ''
  motivoAlertas.value = ''
}, { deep: true })

// Auto-seleccionar ciudad al elegir feria
watch(() => tx.value.feria_id, (newVal) => {
  if (newVal) {
    const f = ferias.value.find(x => x.id === newVal)
    if (f) tx.value.ciudad_feria = f.ciudad
  } else {
    tx.value.ciudad_feria = ''
  }
})

onMounted(async () => {
  await cargarArticulos()
  await cargarCatalogos()
  try {
    const { data } = await api.get('/kardex/politica-control')
    politicaControl.value = data?.version ? data : null
  } catch { /* Las reglas se verifican siempre en el servidor. */ }
})

async function cargarArticulos() {
  try {
    const res = await api.get('/kardex/articulos')
    articulos.value = res.data
    if (articuloSeleccionado.value) {
      articuloSeleccionado.value = articulos.value.find(a => a.id === articuloSeleccionado.value?.id) ?? null
    }
  } catch (err: any) {
    errorMsg.value = "Error al cargar el catálogo."
  }
}

async function cargarCatalogos() {
  try {
    const resNodos = await api.get('/kardex/nodos')
    nodosDisponibles.value = resNodos.data
    operacionesCatalogo.value = (await api.get('/kardex/operaciones-inventario')).data
    areasOperativas.value = (await api.get('/kardex/areas-operativas')).data
    for (const area of areasOperativas.value) conteosArea.value[area.id] ??= 0
    const resFerias = await api.get('/kardex/ferias')
    ferias.value = resFerias.data
    if (puedeOperar.value) {
      const resEncargados = await api.get('/kardex/encargados')
      encargados.value = resEncargados.data
    }
  } catch (err) {
    console.error("Error al cargar catálogos", err)
  }
}

async function cargarExistenciasArea() {
  if (!articuloSeleccionado.value) return
  const articuloId = articuloSeleccionado.value.id
  try {
    const { data } = await api.get(`/kardex/articulos/${articuloId}/existencias-area`)
    if (articuloSeleccionado.value?.id === articuloId) existenciasArea.value = data
  } catch (err) {
    console.error('Error al cargar existencias por área', err)
    if (articuloSeleccionado.value?.id === articuloId) existenciasArea.value = null
  }
}

async function cargarConciliacion() {
  if (!articuloSeleccionado.value) return
  const articuloId = articuloSeleccionado.value.id
  try {
    const { data } = await api.get(`/kardex/articulos/${articuloId}/conciliacion-inicial`)
    if (articuloSeleccionado.value?.id === articuloId) conciliacionInicial.value = data
  } catch (err) {
    console.error('Error al cargar conciliación inicial', err)
    if (articuloSeleccionado.value?.id === articuloId) conciliacionInicial.value = null
  }
}

async function registrarConciliacion() {
  if (!articuloSeleccionado.value || guardandoConciliacion.value) return
  if (!conciliacionForm.value.alcance_total || !conciliacionForm.value.conteo_verificado) return
  guardandoConciliacion.value = true
  errorMsg.value = ''
  try {
    const articuloId = articuloSeleccionado.value.id
    const { data } = await api.post(`/kardex/articulos/${articuloId}/conciliacion-inicial`, {
      ...conciliacionForm.value,
      areas: areasOperativas.value.map(area => ({ area_id: area.id, cantidad: Number(conteosArea.value[area.id] || 0) }))
    })
    conciliacionInicial.value = { estado: 'REGISTRADA', registro: data.registro }
    existenciasArea.value = data.distribucion
    mensajeExito.value = 'Conteo físico conciliado. La base documental y el ajuste quedaron conservados.'
    await cargarArticulos()
    await cargarHistorialModerno()
    await cargarKardexDigital()
  } catch (err: any) {
    errorMsg.value = typeof err.response?.data?.detail === 'string' ? err.response.data.detail : 'No se pudo registrar la conciliación.'
    await cargarConciliacion()
  } finally {
    guardandoConciliacion.value = false
  }
}

async function asignarArea() {
  if (!articuloSeleccionado.value || asignandoArea.value) return
  asignandoArea.value = true
  errorMsg.value = ''
  try {
    existenciasArea.value = (await api.post(`/kardex/articulos/${articuloSeleccionado.value.id}/asignar-area`, asignacionArea.value)).data
    mensajeExito.value = 'Ubicación registrada. El total institucional no cambió.'
    asignacionArea.value = { area_id: '', cantidad: 1, encargado_id: '', referencia_documento: '', justificacion: '' }
    await cargarArticulos()
  } catch (err: any) {
    errorMsg.value = typeof err.response?.data?.detail === 'string' ? err.response.data.detail : 'No se pudo asignar la ubicación.'
  } finally {
    asignandoArea.value = false
  }
}

async function cargarTransferencias() {
  if (!articuloSeleccionado.value) return
  try {
    transferenciasArea.value = (await api.get(`/kardex/articulos/${articuloSeleccionado.value.id}/transferencias`)).data
  } catch (err) {
    console.error('Error al cargar transferencias', err)
  }
}

function formularioEventoCustodia() {
  return { solicitud_id: crypto.randomUUID(), tipo: 'RETORNO' as 'VENTA' | 'RETORNO',
    cantidad: 1, comprador: '', area_destino_id: '' as number | '',
    encargado_id: (auth.usuario?.id ? Number(auth.usuario.id) : '') as number | '',
    fecha_operacion_local: ahoraBoliviaLocal(),
    referencia_documento: '', observaciones: '' }
}

async function cargarCustodias() {
  if (!articuloSeleccionado.value) return
  const articuloId = articuloSeleccionado.value.id
  try {
    const { data } = await api.get(`/kardex/articulos/${articuloId}/custodias-externas`)
    if (articuloSeleccionado.value?.id !== articuloId) return
    custodiasExternas.value = data
    for (const custodia of custodiasExternas.value) {
      eventoCustodiaForms.value[custodia.id] ??= formularioEventoCustodia()
    }
  } catch (err) {
    console.error('Error al cargar custodias externas', err)
    if (articuloSeleccionado.value?.id === articuloId) custodiasExternas.value = []
  }
}

async function registrarEntregaExterna() {
  if (!articuloSeleccionado.value || guardandoCustodia.value) return
  const form = entregaExternaForm.value
  if (!form.area_origen_id || !form.encargado_id || !form.receptor_nombre.trim() || !form.ubicacion_externa.trim())
    return (errorMsg.value = 'Indica el área, encargado, receptor y ubicación externa.')
  if (form.tipo === 'FERIA' && !form.ciudad.trim()) return (errorMsg.value = 'Indica la ciudad de la feria.')
  if (!Number.isInteger(form.cantidad) || form.cantidad <= 0) return (errorMsg.value = 'Indica una cantidad entera positiva.')
  if (form.referencia_documento.trim().length < 3) return (errorMsg.value = 'Indica el acta de entrega.')
  if (alertasEntregaExterna.value.length && motivoEntregaExterna.value.trim().length < 10)
    return (errorMsg.value = 'Justifica la entrega alertada con al menos 10 caracteres.')
  const fecha = new Date(`${form.fecha_operacion_local}-04:00`)
  if (Number.isNaN(fecha.getTime())) return (errorMsg.value = 'Revisa la fecha de la entrega.')
  guardandoCustodia.value = true
  errorMsg.value = ''
  try {
    const { data } = await api.post(`/kardex/articulos/${articuloSeleccionado.value.id}/custodias-externas`, {
      solicitud_id: form.solicitud_id, tipo: form.tipo,
      area_origen_id: form.area_origen_id, receptor_nombre: form.receptor_nombre.trim(),
      receptor_tipo: form.receptor_tipo, ubicacion_externa: form.ubicacion_externa.trim(),
      ciudad: form.ciudad.trim() || null, cantidad: form.cantidad,
      encargado_id: form.encargado_id, fecha_operacion: fecha.toISOString(),
      referencia_documento: form.referencia_documento.trim(),
      observaciones: form.observaciones.trim(),
      confirmacion_alertas: firmaEntregaExterna.value || null,
      motivo_alertas: motivoEntregaExterna.value
    })
    existenciasArea.value = data.distribucion
    alertasEntregaExterna.value = []
    firmaEntregaExterna.value = ''
    motivoEntregaExterna.value = ''
    mensajeExito.value = `Entrega externa #${data.registro.id} registrada sin reducir el total institucional.`
    entregaExternaForm.value = { solicitud_id: crypto.randomUUID(), tipo: 'FERIA',
      area_origen_id: '', receptor_nombre: '', receptor_tipo: 'INSTITUCION',
      ubicacion_externa: '', ciudad: '', cantidad: 1,
      encargado_id: auth.usuario?.id ?? '', fecha_operacion_local: ahoraBoliviaLocal(),
      referencia_documento: '', observaciones: '' }
    await cargarCustodias()
    await cargarKardexDigital()
  } catch (err: any) {
    const detalle = err.response?.data?.detail
    if (err.response?.status === 409 && detalle?.codigo === 'ALERTAS_CONTROL') {
      alertasEntregaExterna.value = detalle.alertas
      firmaEntregaExterna.value = detalle.firma_confirmacion
      motivoEntregaExterna.value = ''
      errorMsg.value = 'Revisa los avisos y justifica la entrega antes de confirmarla.'
    } else if (err.response?.status === 409 && detalle?.codigo === 'CONTROL_DESACTUALIZADO') {
      alertasEntregaExterna.value = []; firmaEntregaExterna.value = ''; motivoEntregaExterna.value = ''
      errorMsg.value = detalle.mensaje
    } else errorMsg.value = typeof detalle === 'string' ? detalle :
      'No se pudo confirmar la entrega. Consulta el historial y reintenta esta misma solicitud antes de crear otra.'
  } finally {
    guardandoCustodia.value = false
  }
}

async function registrarEventoCustodia(custodia: CustodiaExterna) {
  if (!articuloSeleccionado.value || guardandoEventoCustodia.value !== null) return
  const form = eventoCustodiaForms.value[custodia.id]
  if (!form || !form.encargado_id) return (errorMsg.value = 'Selecciona al encargado.')
  if (!Number.isInteger(form.cantidad) || form.cantidad <= 0 || form.cantidad > custodia.cantidad_fuera)
    return (errorMsg.value = `Indica entre 1 y ${custodia.cantidad_fuera} unidades.`)
  if (form.tipo === 'VENTA' && !form.comprador.trim()) return (errorMsg.value = 'Identifica al comprador.')
  if (form.tipo === 'RETORNO' && !form.area_destino_id) return (errorMsg.value = 'Indica el área que recibe el retorno.')
  if (form.referencia_documento.trim().length < 3) return (errorMsg.value = 'Indica la factura o acta de retorno.')
  if (alertasEventosCustodia.value[custodia.id]?.length &&
      (motivosEventosCustodia.value[custodia.id] || '').trim().length < 10)
    return (errorMsg.value = 'Justifica la operación alertada con al menos 10 caracteres.')
  const fecha = new Date(`${form.fecha_operacion_local}-04:00`)
  if (Number.isNaN(fecha.getTime())) return (errorMsg.value = 'Revisa la fecha de la operación.')
  guardandoEventoCustodia.value = custodia.id
  errorMsg.value = ''
  try {
    const { data } = await api.post(`/kardex/articulos/${articuloSeleccionado.value.id}/custodias-externas/${custodia.id}/eventos`, {
      solicitud_id: form.solicitud_id, tipo: form.tipo, cantidad: form.cantidad,
      area_destino_id: form.tipo === 'RETORNO' ? form.area_destino_id : null,
      comprador: form.tipo === 'VENTA' ? form.comprador.trim() : null,
      encargado_id: form.encargado_id, fecha_operacion: fecha.toISOString(),
      referencia_documento: form.referencia_documento.trim(),
      observaciones: form.observaciones.trim(),
      confirmacion_alertas: firmasEventosCustodia.value[custodia.id] || null,
      motivo_alertas: motivosEventosCustodia.value[custodia.id] || ''
    })
    existenciasArea.value = data.distribucion
    articuloSeleccionado.value.stock_actual = data.distribucion.total_institucional
    delete alertasEventosCustodia.value[custodia.id]
    delete firmasEventosCustodia.value[custodia.id]
    delete motivosEventosCustodia.value[custodia.id]
    mensajeExito.value = form.tipo === 'VENTA' ? 'Venta desde custodia registrada.' : 'Retorno de custodia registrado.'
    eventoCustodiaForms.value[custodia.id] = formularioEventoCustodia()
    await cargarCustodias()
    await cargarKardexDigital()
    await cargarArticulos()
  } catch (err: any) {
    const detalle = err.response?.data?.detail
    if (err.response?.status === 409 && detalle?.codigo === 'ALERTAS_CONTROL') {
      alertasEventosCustodia.value[custodia.id] = detalle.alertas
      firmasEventosCustodia.value[custodia.id] = detalle.firma_confirmacion
      motivosEventosCustodia.value[custodia.id] = ''
      errorMsg.value = 'Revisa los avisos y justifica la operación antes de confirmarla.'
    } else if (err.response?.status === 409 && detalle?.codigo === 'CONTROL_DESACTUALIZADO') {
      delete alertasEventosCustodia.value[custodia.id]
      delete firmasEventosCustodia.value[custodia.id]
      delete motivosEventosCustodia.value[custodia.id]
      errorMsg.value = detalle.mensaje
    } else errorMsg.value = typeof detalle === 'string' ? detalle :
      'No se pudo confirmar el resultado. Consulta el historial y reintenta esta misma solicitud.'
  } finally {
    guardandoEventoCustodia.value = null
  }
}

async function cargarKardexDigital() {
  if (!articuloSeleccionado.value) return
  const articuloId = articuloSeleccionado.value.id
  try {
    const { data } = await api.get(`/kardex/articulos/${articuloId}/kardex-digital`)
    if (articuloSeleccionado.value?.id === articuloId)
      kardexDigital.value = data && typeof data.estado === 'string' ? data : null
  } catch (err) {
    console.error('Error al cargar el Kárdex digital', err)
    if (articuloSeleccionado.value?.id === articuloId) kardexDigital.value = null
  }
}

async function descargarKardexDigital() {
  if (!articuloSeleccionado.value || descargandoKardex.value) return
  descargandoKardex.value = true
  errorMsg.value = ''
  try {
    const id = articuloSeleccionado.value.id
    const { data } = await api.get(`/kardex/articulos/${id}/kardex-digital.csv`, {
      responseType: 'blob'
    })
    const url = URL.createObjectURL(data)
    const enlace = document.createElement('a')
    enlace.href = url
    enlace.download = `kardex_digital_articulo_${id}.csv`
    document.body.appendChild(enlace)
    enlace.click()
    enlace.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch (err: any) {
    errorMsg.value = 'No se pudo descargar el Kárdex digital.'
  } finally {
    descargandoKardex.value = false
  }
}

async function registrarTransferencia() {
  if (!articuloSeleccionado.value || guardandoTransferencia.value) return
  const form = transferenciaForm.value
  if (!form.area_origen_id || !form.area_destino_id || form.area_origen_id === form.area_destino_id)
    return (errorMsg.value = 'Selecciona dos áreas distintas.')
  if (!form.encargado_id) return (errorMsg.value = 'Selecciona al encargado de la transferencia.')
  if (!Number.isInteger(form.cantidad) || form.cantidad <= 0)
    return (errorMsg.value = 'La cantidad debe ser un número entero positivo.')
  if (form.referencia_documento.trim().length < 3)
    return (errorMsg.value = 'Indica el acta u otro documento de respaldo.')
  if (alertasTransferencia.value.length && motivoTransferencia.value.trim().length < 10)
    return (errorMsg.value = 'Justifica la transferencia alertada con al menos 10 caracteres.')
  const fecha = new Date(`${form.fecha_operacion_local}-04:00`)
  if (Number.isNaN(fecha.getTime())) return (errorMsg.value = 'Revisa la fecha y hora de la transferencia.')
  guardandoTransferencia.value = true
  errorMsg.value = ''
  try {
    const { data } = await api.post(`/kardex/articulos/${articuloSeleccionado.value.id}/transferencias`, {
      solicitud_id: form.solicitud_id,
      area_origen_id: form.area_origen_id,
      area_destino_id: form.area_destino_id,
      cantidad: form.cantidad,
      encargado_id: form.encargado_id,
      fecha_operacion: fecha.toISOString(),
      referencia_documento: form.referencia_documento.trim(),
      observaciones: form.observaciones.trim(),
      confirmacion_alertas: firmaTransferencia.value || null,
      motivo_alertas: motivoTransferencia.value
    })
    existenciasArea.value = data.distribucion
    mensajeExito.value = `Transferencia #${data.registro.id} registrada. El total institucional no cambió.`
    transferenciaForm.value = { solicitud_id: crypto.randomUUID(), area_origen_id: '',
      area_destino_id: '', cantidad: 1, encargado_id: auth.usuario?.id ?? '',
      fecha_operacion_local: ahoraBoliviaLocal(), referencia_documento: '', observaciones: '' }
    await cargarTransferencias()
    await cargarKardexDigital()
  } catch (err: any) {
    const detalle = err.response?.data?.detail
    if (err.response?.status === 409 && detalle?.codigo === 'ALERTAS_CONTROL') {
      alertasTransferencia.value = detalle.alertas; firmaTransferencia.value = detalle.firma_confirmacion
      motivoTransferencia.value = ''
      errorMsg.value = 'Revisa los avisos y justifica la transferencia antes de confirmarla.'
    } else if (err.response?.status === 409 && detalle?.codigo === 'CONTROL_DESACTUALIZADO') {
      alertasTransferencia.value = []; firmaTransferencia.value = ''; motivoTransferencia.value = ''
      errorMsg.value = detalle.mensaje
    } else errorMsg.value = typeof detalle === 'string' ? detalle :
      'No se pudo confirmar el resultado. Consulta el historial y reintenta esta misma solicitud antes de crear otra.'
  } finally {
    guardandoTransferencia.value = false
  }
}

async function cargarHistorialModerno() {
  if (!articuloSeleccionado.value) return
  cargandoHistorial.value = true
  try {
    const res = await api.get(`/kardex/historial-actual/${articuloSeleccionado.value.id}`)
    movimientosModernos.value = res.data
  } catch (err) {
    console.error("Error al cargar historial moderno", err)
  } finally {
    cargandoHistorial.value = false
  }
}

function cantidadVigente(m: Movimiento): number {
  const ultimo = [...movimientosModernos.value].reverse().find(
    asiento => asiento.corrige_movimiento_id === m.id && asiento.estado === 'ACTIVO')
  return ultimo?.cantidad_corregida ?? m.ingresos ?? m.salidas ?? 0
}

function seleccionarRectificacion(m: Movimiento) {
  movimientoRectificado.value = m.id
  correccionForm.value = { solicitud_id: crypto.randomUUID(),
    cantidad_corregida: cantidadVigente(m), motivo: '', referencia_documento: '' }
  errorMsg.value = ''
}

async function refrescarTrasAjuste() {
  await Promise.all([cargarHistorialModerno(), cargarExistenciasArea(),
    cargarConciliacion(), cargarKardexDigital()])
  const { data } = await api.get('/kardex/articulos')
  articulos.value = data
  const articulo = data.find((a: Articulo) => a.id === articuloSeleccionado.value?.id)
  if (articulo) articuloSeleccionado.value = articulo
}

async function guardarRectificacion() {
  if (!esAdmin.value || !movimientoRectificado.value || guardandoCorreccion.value) return
  guardandoCorreccion.value = true
  errorMsg.value = ''
  try {
    await api.post(`/kardex/movimiento-actual/${movimientoRectificado.value}/corregir`, correccionForm.value)
    movimientoRectificado.value = null
    mensajeExito.value = 'Rectificación documentada. El movimiento original se conservó.'
    await refrescarTrasAjuste()
  } catch (err: any) {
    errorMsg.value = typeof err.response?.data?.detail === 'string' ? err.response.data.detail :
      'No se pudo confirmar la rectificación. Revisa el historial y reintenta esta misma solicitud.'
  } finally {
    guardandoCorreccion.value = false
  }
}

async function guardarAjuste() {
  if (!esAdmin.value || !articuloSeleccionado.value || guardandoAjuste.value) return
  guardandoAjuste.value = true
  errorMsg.value = ''
  try {
    await api.post(`/kardex/articulos/${articuloSeleccionado.value.id}/ajustes-operativos`, {
      ...ajusteForm.value, area_id: ajusteForm.value.area_id || null
    })
    mensajeExito.value = 'Ajuste documentado y autorizado.'
    ajusteForm.value = { solicitud_id: crypto.randomUUID(), direccion: 'ingreso',
      cantidad: 1, area_id: '', encargado_id: auth.usuario?.id ?? '',
      motivo: '', referencia_documento: '' }
    await refrescarTrasAjuste()
  } catch (err: any) {
    errorMsg.value = typeof err.response?.data?.detail === 'string' ? err.response.data.detail :
      'No se pudo confirmar el ajuste. Revisa el historial y reintenta esta misma solicitud.'
  } finally {
    guardandoAjuste.value = false
  }
}

function verDetalle(art: Articulo) {
  mostrarTrazabilidad.value = false
  articuloSeleccionado.value = art
  existenciasArea.value = null
  transferenciasArea.value = []
  custodiasExternas.value = []
  eventoCustodiaForms.value = {}
  kardexDigital.value = null
  movimientoRectificado.value = null
  ajusteForm.value = { solicitud_id: crypto.randomUUID(), direccion: 'ingreso',
    cantidad: 1, area_id: '', encargado_id: auth.usuario?.id ?? '',
    motivo: '', referencia_documento: '' }
  transferenciaForm.value = { solicitud_id: crypto.randomUUID(), area_origen_id: '',
    area_destino_id: '', cantidad: 1, encargado_id: auth.usuario?.id ?? '',
    fecha_operacion_local: ahoraBoliviaLocal(), referencia_documento: '', observaciones: '' }
  entregaExternaForm.value = { solicitud_id: crypto.randomUUID(), tipo: 'FERIA',
    area_origen_id: '', receptor_nombre: '', receptor_tipo: 'INSTITUCION',
    ubicacion_externa: '', ciudad: '', cantidad: 1, encargado_id: auth.usuario?.id ?? '',
    fecha_operacion_local: ahoraBoliviaLocal(), referencia_documento: '', observaciones: '' }
  conciliacionInicial.value = null
  conteosArea.value = Object.fromEntries(areasOperativas.value.map(area => [area.id, 0]))
  conciliacionForm.value = {
    fecha_conteo: new Intl.DateTimeFormat('sv-SE', { timeZone: 'America/La_Paz',
      year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date()),
    encargado_id: '', referencia_documento: '', justificacion: '',
    alcance_total: false, conteo_verificado: false
  }
  aperturaForm.value = { cantidad: 0, referencia_documento: '', justificacion: '', conteo_verificado: false }
  vistaActual.value = 'detalle'
  errorMsg.value = ''
  mensajeExito.value = ''
  cargarHistorialModerno()
  cargarExistenciasArea()
  cargarConciliacion()
  cargarTransferencias()
  cargarCustodias()
  cargarKardexDigital()
}

function iniciarTransaccion() {
  vistaActual.value = 'transaccion'
  solicitudTransaccion.value = crypto.randomUUID()
  fechaOperacionEditada.value = false
  tx.value = {
    tipo: 'salida', cantidad: 1, tipo_operacion: '', area_destino: '',
    encargado_id: auth.usuario?.id ?? '',
    area_operativa_id: '',
    receptor: '', receptor_tipo: '', feria_id: '', ciudad_feria: '', canal_venta: '',
    motivo_baja: '', movimiento_origen_id: '', devuelto_por: '',
    referencia: '', fecha_operacion_local: ahoraBoliviaLocal(), observaciones: ''
  }
  const articuloId = articuloSeleccionado.value?.id
  salidasDevolvibles.value = []
  cargandoSalidasDevolvibles.value = true
  errorSalidasDevolvibles.value = false
  api.get(`/kardex/devoluciones-disponibles/${articuloId}`)
    .then(({ data }) => {
      if (articuloSeleccionado.value?.id === articuloId) salidasDevolvibles.value = data
    })
    .catch(() => {
      if (articuloSeleccionado.value?.id === articuloId) errorSalidasDevolvibles.value = true
    })
    .finally(() => { if (articuloSeleccionado.value?.id === articuloId) cargandoSalidasDevolvibles.value = false })
  errorMsg.value = ''
  mensajeExito.value = ''
  alertasPendientes.value = []
  firmaAlertas.value = ''
  motivoAlertas.value = ''
}

function irANuevoProducto() {
  vistaActual.value = 'nuevo_producto'
  nuevoProducto.value = { nombre: '' }
  errorMsg.value = ''
  mensajeExito.value = ''
}

function volver() {
  vistaActual.value = 'buscar'
  articuloSeleccionado.value = null
  cargarArticulos()
}

function volverADetalle() {
  vistaActual.value = 'detalle'
  transferenciaForm.value.fecha_operacion_local = ahoraBoliviaLocal()
  errorMsg.value = ''
  mensajeExito.value = ''
  cargarArticulos()
  cargarHistorialModerno()
  cargarExistenciasArea()
  cargarConciliacion()
  cargarTransferencias()
  cargarCustodias()
  cargarKardexDigital()
}

async function guardarNuevoProducto() {
  if (!nuevoProducto.value.nombre.trim()) return (errorMsg.value = "El nombre es obligatorio.")
  creandoProducto.value = true
  errorMsg.value = ''
  try {
    const res = await api.post('/kardex/articulos', { nombre: nuevoProducto.value.nombre })
    verDetalle({ ...res.data, stock_actual: null, apertura: null, base_kardex: null, alertas_rojas: 0, alertas_amarillas: 0 })
    mensajeExito.value = 'Producto creado. Un administrador debe aprobar el conteo inicial para habilitar sus operaciones.'
  } catch (err) {
    errorMsg.value = "Error al crear el producto."
  } finally {
    creandoProducto.value = false
  }
}

async function registrarTransaccion() {
  if (!articuloSeleccionado.value || creandoTransaccion.value) return
  if (!tx.value.tipo_operacion) return (errorMsg.value = "Selecciona el Tipo de Operación.")
  if (!tx.value.encargado_id) return (errorMsg.value = "Selecciona al encargado del movimiento.")
  if (tx.value.referencia.trim().length < 3) return (errorMsg.value = 'Indica el acta, factura u otro documento de respaldo (al menos 3 caracteres).')
  if (!tx.value.fecha_operacion_local) return (errorMsg.value = 'Indica la fecha y hora en que ocurrió la operación.')
  if (alertasPendientes.value.length && motivoAlertas.value.trim().length < 10)
    return (errorMsg.value = "Justifica la operación alertada con al menos 10 caracteres.")
  if (tx.value.cantidad <= 0) return (errorMsg.value = "La cantidad debe ser mayor a 0.")
  
  // Validaciones condicionales
  if (tx.value.tipo_operacion === 'Transferencia Interna' && !tx.value.area_destino) return (errorMsg.value = "Selecciona el área de destino.")
  if (operacionesCatalogo.value.find(o => o.valor === tx.value.tipo_operacion)?.requiere_receptor) {
    if (!tx.value.receptor.trim()) return (errorMsg.value = 'Ingresa el nombre de la persona o institución que recibe.')
    if (!tx.value.receptor_tipo) return (errorMsg.value = 'Selecciona el tipo de receptor.')
  }
  if (tx.value.tipo_operacion === 'Salida a Feria' && !tx.value.feria_id && !tx.value.ciudad_feria) return (errorMsg.value = "Ingresa la feria y/o ciudad.")
  if (tx.value.tipo_operacion === 'Baja / Pérdida' && !tx.value.motivo_baja) return (errorMsg.value = "Selecciona el motivo de baja.")
  if (tx.value.tipo_operacion === 'Devolución') {
    if (!salidaSeleccionada.value) return (errorMsg.value = 'Selecciona una venta o donación pendiente de devolución.')
    if (!tx.value.devuelto_por.trim()) return (errorMsg.value = 'Identifica a quien devuelve las unidades.')
    if (!tx.value.area_operativa_id) return (errorMsg.value = 'Indica el área que recibe físicamente la devolución.')
    if (tx.value.cantidad > salidaSeleccionada.value.cantidad_pendiente)
      return (errorMsg.value = `Quedan ${salidaSeleccionada.value.cantidad_pendiente} unidades pendientes de esa entrega.`)
  }

  if (!fechaOperacionEditada.value) {
    tx.value.fecha_operacion_local = ahoraBoliviaLocal()
    fechaOperacionEditada.value = true
  }
  const fechaOperacion = new Date(`${tx.value.fecha_operacion_local}-04:00`)
  if (Number.isNaN(fechaOperacion.getTime())) return (errorMsg.value = 'Revisa la fecha y hora de la operación.')

  creandoTransaccion.value = true
  errorMsg.value = ''
  
  // Determinar nodo grafo según la operación
  let nodo = tx.value.tipo_operacion
  if (nodo === 'Transferencia Interna') nodo = tx.value.area_destino
  if (nodo === 'Salida a Feria') nodo = 'Feria'
  
  try {
    const { data } = await api.post('/kardex/movimiento-actual', {
      articulo_id: articuloSeleccionado.value.id,
      solicitud_id: solicitudTransaccion.value,
      tipo: tx.value.tipo,
      cantidad: tx.value.cantidad,
      fecha_operacion: fechaOperacion.toISOString(),
      encargado_id: tx.value.encargado_id,
      area_operativa_id: tx.value.area_operativa_id || null,
      nodo_grafo: nodo,
      tipo_operacion: tx.value.tipo_operacion,
      receptor: tx.value.receptor,
      receptor_tipo: tx.value.receptor_tipo || null,
      feria_id: tx.value.feria_id || null,
      ciudad_feria: tx.value.ciudad_feria,
      canal_venta: tx.value.canal_venta,
      motivo_baja: tx.value.motivo_baja,
      movimiento_origen_id: tx.value.tipo_operacion === 'Devolución' ? tx.value.movimiento_origen_id : null,
      devuelto_por: tx.value.tipo_operacion === 'Devolución' ? tx.value.devuelto_por : null,
      referencia_documento: tx.value.referencia,
      observaciones: tx.value.observaciones,
      confirmacion_alertas: firmaAlertas.value || null,
      motivo_alertas: motivoAlertas.value
    })
    mensajeExito.value = "Transacción registrada correctamente."
    articuloSeleccionado.value!.stock_actual = data.saldo_registrado
    await cargarExistenciasArea()
    setTimeout(volverADetalle, 1500)
  } catch (err: any) {
    const detalle = err.response?.data?.detail
    if (err.response?.status === 409 && detalle?.codigo === 'ALERTAS_CONTROL') {
      alertasPendientes.value = detalle.alertas
      firmaAlertas.value = detalle.firma_confirmacion
      motivoAlertas.value = ''
      errorMsg.value = 'Revisa los avisos y justifica la operación antes de confirmarla.'
    } else if (err.response?.status === 409 && detalle?.codigo === 'CONTROL_DESACTUALIZADO') {
      alertasPendientes.value = []; firmaAlertas.value = ''; motivoAlertas.value = ''
      errorMsg.value = detalle.mensaje
    } else if (typeof detalle === 'string') {
      errorMsg.value = detalle
    } else {
      errorMsg.value = 'No se pudo confirmar el resultado. Consulta el historial de este artículo antes de iniciar otra transacción; puedes reintentar esta misma solicitud.'
    }
  } finally {
    creandoTransaccion.value = false
  }
}

</script>

<template>
  <div class="inventario-actual-view">
    <div class="header-nav">
      <button v-if="vistaActual !== 'buscar'" class="btn-back" @click="vistaActual === 'transaccion' ? volverADetalle() : volver()">
        <i class="pi pi-arrow-left"></i> Volver
      </button>
      <router-link v-else to="/" class="btn-back"><i class="pi pi-arrow-left"></i> Panel Principal</router-link>
      
      <h1>Inventario Actual en Vivo</h1>
      <div style="flex-grow:1"></div>
      
      <button v-if="vistaActual === 'buscar' && puedeOperar" class="btn-primary" @click="irANuevoProducto">
        + Nuevo Producto
      </button>
    </div>
    
    <p v-if="errorMsg" class="alert alert-error">{{ errorMsg }}</p>
    <p v-if="mensajeExito" class="alert alert-success">{{ mensajeExito }}</p>

    <!-- PANTALLA BUSCAR -->
    <div v-if="vistaActual === 'buscar'" class="pantalla-buscar">
      <p class="subtitle">Selecciona un artículo para ver su stock actual y registrar operaciones en vivo.</p>
      <BuscadorArticulos v-model="buscarTexto" />
      <label>Estado documental <select v-model="filtroObservacion"><option value="todos">Todos</option><option value="sin_observacion">Sin observación especial</option><option value="observados">Observados</option></select></label>

      <div class="lista-articulos">
        <div v-for="art in articulosFiltrados" :key="art.id" class="articulo-card" @click="verDetalle(art)">
          <div class="art-header">
            <div class="art-codigo">{{ art.codigo }}</div>
            <div class="stock-badge" :class="art.base_kardex && !art.apertura && !art.base_kardex.operable ? 'stock-review' : (art.stock_actual ?? 0) > 0 ? 'stock-ok' : 'stock-zero'">
              {{ art.stock_actual === null ? 'Sin saldo inicial' : `${art.stock_actual} u.${!art.apertura ? art.base_kardex?.operable ? ' · Kárdex' : ' · revisar' : ''}` }}
            </div>
          </div>
          <div class="art-nombre">{{ art.nombre }}</div>
          <small v-if="art.observacion_hil?.observado">Observado<span v-if="art.observacion_hil.excluir_entrenamiento"> · fuera del entrenamiento histórico</span></small>
        </div>
      </div>
    </div>

    <!-- PANTALLA DETALLE ARTÍCULO -->
    <div v-if="vistaActual === 'detalle' && articuloSeleccionado" class="pantalla-detalle">
      <div class="detalle-header">
        <div>
          <h2>{{ articuloSeleccionado.nombre }}</h2>
          <span class="art-codigo">{{ articuloSeleccionado.codigo }}</span>
        </div>
        <div class="stock-display">
          <div class="stock-numero">{{ articuloSeleccionado.stock_actual ?? 'Sin apertura' }}</div>
          <div class="stock-label">{{ articuloSeleccionado.apertura ? 'Total institucional' : articuloSeleccionado.base_kardex ? 'Saldo final escaneado' : 'Stock actual' }}</div>
        </div>
      </div>

      <section v-if="!articuloSeleccionado.apertura && articuloSeleccionado.base_kardex" class="context-box mt-4">
        <p v-if="articuloSeleccionado.observacion_hil?.observado"><strong>Artículo observado:</strong> {{ articuloSeleccionado.observacion_hil.motivo }}<span v-if="articuloSeleccionado.observacion_hil.excluir_entrenamiento"> Queda fuera del entrenamiento histórico. Las operaciones digitales mantienen sus controles de saldo.</span></p>
        <strong>Base de trabajo del Kárdex histórico: {{ articuloSeleccionado.base_kardex.saldo }} u.</strong>
        <p v-if="['RECONSTRUIDO', 'HIPOTESIS', 'ANOTACION_MARGEN'].includes(articuloSeleccionado.base_kardex.origen_saldo || '')">Origen: {{ articuloSeleccionado.base_kardex.origen_saldo }}. Saldo escrito cotejado: {{ articuloSeleccionado.base_kardex.saldo_documental ?? 'vacío o no legible' }}. La reconstrucción se conserva separada de la fuente.</p>
        <p>Último movimiento escaneado #{{ articuloSeleccionado.base_kardex.movimiento_id }} · lote #{{ articuloSeleccionado.base_kardex.lote_id }} · {{ articuloSeleccionado.base_kardex.fecha_movimiento }}.</p>
        <p>Este saldo documental será el punto de partida al registrar la primera operación moderna. No es un conteo físico de 2026; las hojas escaneadas permanecen intactas para auditoría.</p>
        <p v-if="articuloSeleccionado.base_kardex.motivo_bloqueo" class="alert alert-error">{{ articuloSeleccionado.base_kardex.motivo_bloqueo }}</p>
        <router-link :to="{ path: '/kardex-digital', query: { articulo_id: articuloSeleccionado.id } }">Ver Kárdex y evidencia</router-link>
      </section>
      <details v-if="politicaControl" class="context-box mt-4" aria-label="Reglas de control inmediato">
        <summary>Reglas de control inmediato · umbrales provisionales</summary>
        <p><router-link :to="{ path: '/alertas-inventario', query: { articulo_id: articuloSeleccionado.id } }">Ver alertas y seguimiento de este artículo</router-link></p>
        <p>Se revisan el total institucional y las unidades de la ubicación seleccionada. Superar el stock disponible bloquea la operación; los avisos permiten confirmar una operación justificada.</p>
        <ul>
          <li>Usar todas las unidades disponibles o al menos {{ politicaControl.porcentaje_mayoritario }} % cuando hay {{ politicaControl.stock_minimo_mayoritario }} o más.</li>
          <li>Cantidades de {{ politicaControl.cantidad_extrema }} unidades o más.</li>
          <li>Cantidades desde {{ politicaControl.min_cantidad_atipica }} unidades que alcancen {{ politicaControl.factor_atipico }} veces la mediana de {{ politicaControl.min_comparables }} o más operaciones comparables.</li>
          <li>Registro o hecho fuera de {{ String(politicaControl.hora_inicio).padStart(2, '0') }}:00–{{ String(politicaControl.hora_fin).padStart(2, '0') }}:00 en Bolivia, o registro {{ politicaControl.registro_tardio_horas }} horas después del hecho.</li>
          <li>Posible repetición con el mismo documento, cantidad y participantes o ubicaciones dentro de {{ politicaControl.repeticion_minutos }} minutos.</li>
        </ul>
        <p>Los avisos ayudan a revisar errores y situaciones inusuales. La comparación usa operaciones digitales posteriores al corte; el Kárdex escaneado mantiene su función de auditoría.</p>
      </details>
      <section v-if="!articuloSeleccionado.apertura && (!articuloSeleccionado.base_kardex || !articuloSeleccionado.base_kardex.operable)" class="form-container mt-4">
        <h3>Saldo de apertura pendiente</h3>
        <p>{{ articuloSeleccionado.base_kardex ? 'El cierre histórico requiere revisión. Como alternativa, registra un conteo físico documentado.' : 'Este producto no tiene cierre histórico escaneado. Registra un conteo físico documentado.' }}</p>
        <form v-if="esAdmin" @submit.prevent="aprobarApertura">
          <div class="form-group mt-3">
            <label for="apertura-cantidad">Cantidad física verificada (se permite cero)</label>
            <input id="apertura-cantidad" v-model.number="aperturaForm.cantidad" type="number" min="0" max="2147483647" step="1" required />
          </div>
          <div class="form-group mt-3">
            <label for="apertura-referencia">Referencia del acta o documento de conteo</label>
            <input id="apertura-referencia" v-model="aperturaForm.referencia_documento" minlength="3" maxlength="255" required />
          </div>
          <div class="form-group mt-3">
            <label for="apertura-justificacion">Justificación del saldo</label>
            <textarea id="apertura-justificacion" v-model="aperturaForm.justificacion" minlength="10" maxlength="2000" required></textarea>
          </div>
          <p><label><input v-model="aperturaForm.conteo_verificado" type="checkbox" required /> Confirmo que el conteo físico está verificado. Esta apertura se aprueba una sola vez.</label></p>
          <button class="btn-primary" type="submit" :disabled="aprobando || !aperturaForm.conteo_verificado">{{ aprobando ? 'Aprobando...' : 'Aprobar saldo de apertura' }}</button>
        </form>
        <p v-else>Un administrador debe aprobar la apertura para habilitar las operaciones.</p>
      </section>
      <div v-if="articuloSeleccionado.apertura" class="context-box mt-4">
        <strong>{{ articuloSeleccionado.apertura.origen === 'KARDEX_HISTORICO' ? 'Base histórica fijada' : 'Apertura aprobada' }}: {{ articuloSeleccionado.apertura.cantidad_inicial }} u.</strong>
        <p>{{ new Date(articuloSeleccionado.apertura.aprobado_en).toLocaleString('es-BO') }} · Responsable #{{ articuloSeleccionado.apertura.aprobado_por }}</p>
        <p>Documento: {{ articuloSeleccionado.apertura.referencia_documento }}</p>
        <p>{{ articuloSeleccionado.apertura.justificacion }}</p>
        <p v-if="articuloSeleccionado.corte_operativo?.estado === 'BASE_DOCUMENTAL_PROVISIONAL'">
          Base documental provisional desde {{ fechaRegistro(articuloSeleccionado.corte_operativo.fecha_inicio) }}.
          Los movimientos reales anteriores al inicio deben conciliarse con respaldo o conteo físico.
        </p>
        <p v-if="articuloSeleccionado.corte_operativo?.estado === 'CONTEO_FISICO_CONCILIADO'">
          El saldo inicial fue cotejado con un conteo físico por áreas. Los movimientos anteriores
          que ocurrieron fuera del sistema siguen pendientes de reconstrucción documental.
        </p>
        <p v-if="articuloSeleccionado.diferencia_documental" role="alert" class="alert alert-error">
          Un escaneo o corrección posterior cambió el cierre documental: base congelada
          {{ articuloSeleccionado.diferencia_documental.saldo_base_congelada }} u., cierre disponible
          {{ articuloSeleccionado.diferencia_documental.saldo_cierre_disponible }} u.
          El stock vivo no cambió; revisa la diferencia antes de ajustar.
        </p>
      </div>
      <section v-if="existenciasArea" class="context-box mt-4" aria-label="Existencias por ubicación">
        <h3>Existencias por área</h3>
        <p>Total institucional: <strong>{{ existenciasArea.total_institucional ?? 'Sin apertura' }} u.</strong></p>
        <p>Sin ubicación confirmada: <strong>{{ existenciasArea.sin_ubicacion_confirmada ?? 'Sin apertura' }} u.</strong></p>
        <p>En custodia externa: <strong>{{ existenciasArea.en_custodia_externa ?? 0 }} u.</strong></p>
        <ul v-if="existenciasArea.areas.length">
          <li v-for="area in existenciasArea.areas" :key="area.area_id">{{ area.area }}: {{ area.cantidad }} u.</li>
        </ul>
        <p v-if="!articuloSeleccionado.apertura && articuloSeleccionado.base_kardex">El saldo escaneado aún no se ha distribuido físicamente.</p>
        <form v-if="esAdmin && articuloSeleccionado.apertura && (existenciasArea.sin_ubicacion_confirmada ?? 0) > 0" @submit.prevent="asignarArea">
          <h4>Asignar ubicación con respaldo</h4>
          <div class="form-group mt-3">
            <label for="asignacion-area">Área física</label>
            <select id="asignacion-area" v-model.number="asignacionArea.area_id" required>
              <option disabled value="">Selecciona un área</option>
              <option v-for="area in areasOperativas" :key="area.id" :value="area.id">{{ area.nombre }}</option>
            </select>
          </div>
          <div class="form-group mt-3">
            <label for="asignacion-cantidad">Cantidad verificada</label>
            <input id="asignacion-cantidad" v-model.number="asignacionArea.cantidad" type="number" min="1" :max="existenciasArea.sin_ubicacion_confirmada ?? undefined" step="1" required />
          </div>
          <div class="form-group mt-3">
            <label for="asignacion-encargado">Encargado</label>
            <select id="asignacion-encargado" v-model.number="asignacionArea.encargado_id" required>
              <option disabled value="">Selecciona al encargado</option>
              <option v-for="persona in encargados" :key="persona.id" :value="persona.id">{{ persona.nombre }}</option>
            </select>
          </div>
          <div class="form-group mt-3">
            <label for="asignacion-documento">Acta o documento</label>
            <input id="asignacion-documento" v-model="asignacionArea.referencia_documento" minlength="3" maxlength="255" required />
          </div>
          <div class="form-group mt-3">
            <label for="asignacion-justificacion">Justificación</label>
            <textarea id="asignacion-justificacion" v-model="asignacionArea.justificacion" minlength="10" maxlength="2000" required></textarea>
          </div>
          <button class="btn-primary mt-3" type="submit" :disabled="asignandoArea">{{ asignandoArea ? 'Guardando...' : 'Asignar existencias al área' }}</button>
        </form>
        <p v-if="puedeOperar && articuloSeleccionado.apertura && areasOperativas.length < 2" class="text-muted">
          Para transferir unidades deben existir al menos dos áreas operativas activas.
        </p>
        <form v-if="puedeOperar && articuloSeleccionado.apertura && areasOperativas.length >= 2 && existenciasArea.areas.some(a => a.cantidad > 0)"
          aria-label="Transferir entre áreas" @submit.prevent="registrarTransferencia">
          <h4>Transferir entre áreas</h4>
          <p>El origen entrega y el destino recibe la misma cantidad. El total institucional permanece igual.</p>
          <div class="form-group mt-3">
            <label for="transferencia-origen">Área de origen</label>
            <select id="transferencia-origen" v-model.number="transferenciaForm.area_origen_id" required>
              <option disabled value="">Selecciona el origen</option>
              <option v-for="area in existenciasArea.areas.filter(a => a.cantidad > 0)" :key="area.area_id" :value="area.area_id">
                {{ area.area }} ({{ area.cantidad }} u.)
              </option>
            </select>
          </div>
          <div class="form-group mt-3">
            <label for="transferencia-destino">Área de destino</label>
            <select id="transferencia-destino" v-model.number="transferenciaForm.area_destino_id" required>
              <option disabled value="">Selecciona el destino</option>
              <option v-for="area in areasOperativas.filter(a => a.id !== transferenciaForm.area_origen_id)" :key="area.id" :value="area.id">{{ area.nombre }}</option>
            </select>
          </div>
          <div class="form-group mt-3">
            <label for="transferencia-cantidad">Cantidad</label>
            <input id="transferencia-cantidad" v-model.number="transferenciaForm.cantidad" type="number" min="1" step="1"
              :max="existenciasArea.areas.find(a => a.area_id === transferenciaForm.area_origen_id)?.cantidad ?? undefined" required />
          </div>
          <div class="form-group mt-3">
            <label for="transferencia-encargado">Encargado</label>
            <select id="transferencia-encargado" v-model.number="transferenciaForm.encargado_id" required>
              <option disabled value="">Selecciona al encargado</option>
              <option v-for="persona in encargados" :key="persona.id" :value="persona.id">{{ persona.nombre }}</option>
            </select>
          </div>
          <div class="form-group mt-3">
            <label for="transferencia-fecha">Fecha y hora de la transferencia (Bolivia)</label>
            <input id="transferencia-fecha" v-model="transferenciaForm.fecha_operacion_local" type="datetime-local" step="1" required />
          </div>
          <div class="form-group mt-3">
            <label for="transferencia-documento">Acta o documento</label>
            <input id="transferencia-documento" v-model="transferenciaForm.referencia_documento" minlength="3" maxlength="200" required />
          </div>
          <div class="form-group mt-3">
            <label for="transferencia-observaciones">Observaciones</label>
            <textarea id="transferencia-observaciones" v-model="transferenciaForm.observaciones" maxlength="1000"></textarea>
          </div>
          <div v-if="alertasTransferencia.length" class="alertas-control mt-3" role="alert">
            <strong>Revisa estos avisos antes de transferir:</strong>
            <ul><li v-for="a in alertasTransferencia" :key="a.codigo">{{ a.mensaje }}</li></ul>
            <label for="transferencia-motivo-alertas">Justificación</label>
            <textarea id="transferencia-motivo-alertas" v-model="motivoTransferencia" minlength="10" maxlength="1000" rows="3"></textarea>
          </div>
          <button class="btn-primary mt-3" type="submit" :disabled="guardandoTransferencia">
            {{ guardandoTransferencia ? 'Transfiriendo...' : alertasTransferencia.length ? 'Confirmar transferencia justificada' : 'Registrar transferencia' }}
          </button>
        </form>
        <div v-if="transferenciasArea.length" aria-label="Historial de transferencias">
          <h4>Historial de transferencias</h4>
          <ul><li v-for="transferencia in transferenciasArea" :key="transferencia.id">
            #{{ transferencia.id }} · {{ fechaRegistro(transferencia.ocurrido_en) }} ·
            {{ transferencia.cantidad }} u. de {{ transferencia.area_origen }} a {{ transferencia.area_destino }} ·
            Documento: {{ transferencia.referencia_documento }} · Encargado #{{ transferencia.encargado_id }} ·
            Registrado por #{{ transferencia.registrado_por }} ({{ fechaRegistro(transferencia.registrado_en) }})
            <div v-for="a in transferencia.alertas_control || []" :key="a.codigo" class="aviso-historial">{{ a.mensaje }}</div>
            <div v-if="transferencia.justificacion_alertas">Justificación: {{ transferencia.justificacion_alertas }}</div>
          </li></ul>
        </div>
      </section>
      <section v-if="existenciasArea" class="context-box mt-4" aria-label="Custodia externa">
        <h3>Ferias y consignaciones</h3>
        <p>Las unidades entregadas siguen siendo institucionales mientras estén fuera. Solo una venta documentada reduce el total; el retorno las incorpora al área receptora.</p>
        <form v-if="puedeOperar && articuloSeleccionado.apertura && existenciasArea.areas.some(a => a.cantidad > 0)"
          aria-label="Registrar entrega externa" @submit.prevent="registrarEntregaExterna">
          <h4>Registrar entrega externa</h4>
          <div class="form-group mt-3">
            <label for="custodia-tipo">Modalidad</label>
            <select id="custodia-tipo" v-model="entregaExternaForm.tipo" required>
              <option value="FERIA">Feria</option><option value="CONSIGNACION">Consignación</option>
            </select>
          </div>
          <div class="form-group mt-3">
            <label for="custodia-origen">Área que entrega</label>
            <select id="custodia-origen" v-model.number="entregaExternaForm.area_origen_id" required>
              <option disabled value="">Selecciona el origen</option>
              <option v-for="area in existenciasArea.areas.filter(a => a.cantidad > 0)" :key="area.area_id" :value="area.area_id">{{ area.area }} ({{ area.cantidad }} u.)</option>
            </select>
          </div>
          <div class="form-group mt-3">
            <label for="custodia-receptor">Persona o institución que recibe</label>
            <input id="custodia-receptor" v-model="entregaExternaForm.receptor_nombre" minlength="3" maxlength="200" required />
            <select id="custodia-receptor-tipo" v-model="entregaExternaForm.receptor_tipo" required>
              <option value="INSTITUCION">Institución</option><option value="PERSONA">Persona</option>
            </select>
          </div>
          <div class="form-group mt-3">
            <label for="custodia-ubicacion">Ubicación externa o nombre de la feria</label>
            <input id="custodia-ubicacion" v-model="entregaExternaForm.ubicacion_externa" minlength="3" maxlength="200" required />
          </div>
          <div v-if="entregaExternaForm.tipo === 'FERIA'" class="form-group mt-3">
            <label for="custodia-ciudad">Ciudad de la feria</label>
            <input id="custodia-ciudad" v-model="entregaExternaForm.ciudad" maxlength="100" required />
          </div>
          <div class="form-group mt-3">
            <label for="custodia-cantidad">Cantidad entregada</label>
            <input id="custodia-cantidad" v-model.number="entregaExternaForm.cantidad" type="number" min="1" step="1"
              :max="existenciasArea.areas.find(a => a.area_id === entregaExternaForm.area_origen_id)?.cantidad ?? undefined" required />
          </div>
          <div class="form-group mt-3">
            <label for="custodia-encargado">Encargado de la entrega</label>
            <select id="custodia-encargado" v-model.number="entregaExternaForm.encargado_id" required>
              <option disabled value="">Selecciona al encargado</option>
              <option v-for="persona in encargados" :key="persona.id" :value="persona.id">{{ persona.nombre }}</option>
            </select>
          </div>
          <div class="form-group mt-3">
            <label for="custodia-fecha">Fecha y hora de la entrega (Bolivia)</label>
            <input id="custodia-fecha" v-model="entregaExternaForm.fecha_operacion_local" type="datetime-local" step="1" required />
          </div>
          <div class="form-group mt-3">
            <label for="custodia-documento">Acta de entrega</label>
            <input id="custodia-documento" v-model="entregaExternaForm.referencia_documento" minlength="3" maxlength="200" required />
          </div>
          <div class="form-group mt-3">
            <label for="custodia-observaciones">Observaciones</label>
            <textarea id="custodia-observaciones" v-model="entregaExternaForm.observaciones" maxlength="1000"></textarea>
          </div>
          <div v-if="alertasEntregaExterna.length" class="alertas-control mt-3" role="alert">
            <strong>Revisa estos avisos antes de entregar:</strong>
            <ul><li v-for="aviso in alertasEntregaExterna" :key="aviso.codigo">{{ aviso.mensaje }}</li></ul>
            <label for="custodia-motivo-alertas">Justificación:</label>
            <textarea id="custodia-motivo-alertas" v-model="motivoEntregaExterna" minlength="10" maxlength="1000" rows="3"></textarea>
          </div>
          <button type="submit" class="btn-primary mt-3" :disabled="guardandoCustodia">{{ guardandoCustodia ? 'Guardando...' : 'Registrar entrega' }}</button>
        </form>
        <p v-else-if="puedeOperar && articuloSeleccionado.apertura" class="text-muted">Asigna primero unidades verificadas a un área para registrar una entrega externa.</p>
        <div v-if="custodiasExternas.length" aria-label="Entregas externas registradas" class="mt-4">
          <h4>Entregas registradas</h4>
          <div v-for="custodia in custodiasExternas" :key="custodia.id" class="context-box mt-3">
            <strong>#{{ custodia.id }} · {{ custodia.tipo === 'FERIA' ? 'Feria' : 'Consignación' }} · {{ custodia.estado }}</strong>
            <p>{{ custodia.receptor_nombre }} · {{ custodia.ubicacion_externa }}<span v-if="custodia.ciudad">, {{ custodia.ciudad }}</span> · origen: {{ custodia.area_origen }}.</p>
            <p>Entregadas: {{ custodia.cantidad_entregada }} u. · Fuera: <strong>{{ custodia.cantidad_fuera }} u.</strong> · Vendidas: {{ custodia.cantidad_vendida }} u. · Devueltas: {{ custodia.cantidad_devuelta }} u.</p>
            <p>{{ fechaRegistro(custodia.ocurrido_en) }} · Acta: {{ custodia.referencia_documento }} · Encargado #{{ custodia.encargado_id }} · Registrado por #{{ custodia.registrado_por }} ({{ fechaRegistro(custodia.registrado_en) }})</p>
            <p v-for="a in custodia.alertas_control || []" :key="a.codigo" class="aviso-historial">{{ a.mensaje }}</p>
            <p v-if="custodia.justificacion_alertas">Justificación: {{ custodia.justificacion_alertas }}</p>
            <ul v-if="custodia.eventos.length"><li v-for="evento in custodia.eventos" :key="evento.id">
              {{ evento.tipo === 'VENTA' ? 'Venta' : 'Retorno' }} #{{ evento.id }} · {{ evento.cantidad }} u. · {{ evento.comprador || evento.area_destino }} · {{ evento.referencia_documento }} · {{ fechaRegistro(evento.ocurrido_en) }}
              <div v-for="a in evento.alertas_control || []" :key="a.codigo" class="aviso-historial">{{ a.mensaje }}</div>
              <div v-if="evento.justificacion_alertas">Justificación: {{ evento.justificacion_alertas }}</div>
            </li></ul>
            <form v-if="puedeOperar && custodia.cantidad_fuera > 0 && eventoCustodiaForms[custodia.id]"
              :aria-label="`Registrar venta o retorno de entrega ${custodia.id}`" @submit.prevent="registrarEventoCustodia(custodia)">
              <h5>Registrar venta o retorno</h5>
              <div class="form-group mt-3">
                <label :for="`evento-tipo-${custodia.id}`">Resultado</label>
                <select :id="`evento-tipo-${custodia.id}`" v-model="eventoCustodiaForms[custodia.id].tipo" required>
                  <option value="RETORNO">Retorno al área</option><option value="VENTA">Venta definitiva</option>
                </select>
              </div>
              <div class="form-group mt-3">
                <label :for="`evento-cantidad-${custodia.id}`">Cantidad</label>
                <input :id="`evento-cantidad-${custodia.id}`" v-model.number="eventoCustodiaForms[custodia.id].cantidad"
                  type="number" min="1" :max="custodia.cantidad_fuera" step="1" required />
              </div>
              <div v-if="eventoCustodiaForms[custodia.id].tipo === 'RETORNO'" class="form-group mt-3">
                <label :for="`evento-area-${custodia.id}`">Área que recibe</label>
                <select :id="`evento-area-${custodia.id}`" v-model.number="eventoCustodiaForms[custodia.id].area_destino_id" required>
                  <option disabled value="">Selecciona el área</option>
                  <option v-for="area in areasOperativas" :key="area.id" :value="area.id">{{ area.nombre }}</option>
                </select>
              </div>
              <div v-else class="form-group mt-3">
                <label :for="`evento-comprador-${custodia.id}`">Comprador</label>
                <input :id="`evento-comprador-${custodia.id}`" v-model="eventoCustodiaForms[custodia.id].comprador" maxlength="200" required />
              </div>
              <div class="form-group mt-3">
                <label :for="`evento-encargado-${custodia.id}`">Encargado</label>
                <select :id="`evento-encargado-${custodia.id}`" v-model.number="eventoCustodiaForms[custodia.id].encargado_id" required>
                  <option disabled value="">Selecciona al encargado</option>
                  <option v-for="persona in encargados" :key="persona.id" :value="persona.id">{{ persona.nombre }}</option>
                </select>
              </div>
              <div class="form-group mt-3">
                <label :for="`evento-fecha-${custodia.id}`">Fecha y hora de la operación (Bolivia)</label>
                <input :id="`evento-fecha-${custodia.id}`" v-model="eventoCustodiaForms[custodia.id].fecha_operacion_local" type="datetime-local" step="1" required />
              </div>
              <div class="form-group mt-3">
                <label :for="`evento-documento-${custodia.id}`">{{ eventoCustodiaForms[custodia.id].tipo === 'VENTA' ? 'Factura o comprobante' : 'Acta de retorno' }}</label>
                <input :id="`evento-documento-${custodia.id}`" v-model="eventoCustodiaForms[custodia.id].referencia_documento" minlength="3" maxlength="200" required />
              </div>
              <div class="form-group mt-3">
                <label :for="`evento-observaciones-${custodia.id}`">Observaciones</label>
                <textarea :id="`evento-observaciones-${custodia.id}`" v-model="eventoCustodiaForms[custodia.id].observaciones" maxlength="1000"></textarea>
              </div>
              <div v-if="alertasEventosCustodia[custodia.id]?.length" class="alertas-control mt-3" role="alert">
                <strong>Revisa estos avisos antes de guardar:</strong>
                <ul><li v-for="aviso in alertasEventosCustodia[custodia.id]" :key="aviso.codigo">{{ aviso.mensaje }}</li></ul>
                <label :for="`evento-motivo-alertas-${custodia.id}`">Justificación:</label>
                <textarea :id="`evento-motivo-alertas-${custodia.id}`" v-model="motivosEventosCustodia[custodia.id]" minlength="10" maxlength="1000" rows="3"></textarea>
              </div>
              <button class="btn-primary mt-3" type="submit" :disabled="guardandoEventoCustodia !== null">{{ guardandoEventoCustodia === custodia.id ? 'Guardando...' : 'Registrar resultado' }}</button>
            </form>
          </div>
        </div>
      </section>
      <section v-if="conciliacionInicial" class="context-box mt-4" aria-label="Conciliación inicial">
        <h3>Conciliación inicial por conteo físico</h3>
        <div v-if="conciliacionInicial.estado === 'REGISTRADA' && conciliacionInicial.registro">
          <p>Conteo del {{ conciliacionInicial.registro.fecha_conteo }}: <strong>{{ conciliacionInicial.registro.cantidad_fisica }} u.</strong>
            Base anterior: {{ conciliacionInicial.registro.cantidad_base }} u.; diferencia:
            {{ conciliacionInicial.registro.diferencia > 0 ? '+' : '' }}{{ conciliacionInicial.registro.diferencia }} u.</p>
          <p>Documento: {{ conciliacionInicial.registro.referencia_documento }}.
            {{ conciliacionInicial.registro.justificacion }}</p>
          <p v-if="conciliacionInicial.registro.ajuste_movimiento_id">Ajuste registrado como movimiento #{{ conciliacionInicial.registro.ajuste_movimiento_id }}.</p>
          <ul><li v-for="area in conciliacionInicial.registro.areas" :key="area.area_id">{{ area.area }}: {{ area.cantidad }} u.</li></ul>
        </div>
        <p v-else-if="conciliacionInicial.estado === 'NO_DISPONIBLE'">{{ conciliacionInicial.motivo }}</p>
        <template v-else>
          <p>Base previa: {{ conciliacionInicial.cantidad_base }} u. Esta acción requiere haber contado todas las ubicaciones físicas del artículo. Conserva el saldo previo y registra la diferencia como ajuste; no reemplaza el Kárdex escaneado.</p>
          <form v-if="esAdmin && areasOperativas.length" @submit.prevent="registrarConciliacion">
            <div class="form-group mt-3">
              <label for="conteo-fecha">Fecha del conteo</label>
              <input id="conteo-fecha" v-model="conciliacionForm.fecha_conteo" type="date" required />
            </div>
            <div v-for="area in areasOperativas" :key="area.id" class="form-group mt-3">
              <label :for="`conteo-area-${area.id}`">{{ area.nombre }} (unidades contadas)</label>
              <input :id="`conteo-area-${area.id}`" v-model.number="conteosArea[area.id]" type="number" min="0" max="2147483647" step="1" required />
            </div>
            <p>Total contado: <strong>{{ totalContado }} u.</strong> · Diferencia respecto a la base:
              {{ totalContado - Number(conciliacionInicial.cantidad_base ?? 0) }} u.</p>
            <div class="form-group mt-3">
              <label for="conteo-encargado">Encargado del conteo</label>
              <select id="conteo-encargado" v-model.number="conciliacionForm.encargado_id" required>
                <option disabled value="">Selecciona al encargado</option>
                <option v-for="persona in encargados" :key="persona.id" :value="persona.id">{{ persona.nombre }}</option>
              </select>
            </div>
            <div class="form-group mt-3">
              <label for="conteo-documento">Referencia del acta o documento</label>
              <input id="conteo-documento" v-model="conciliacionForm.referencia_documento" minlength="3" maxlength="200" required />
            </div>
            <div class="form-group mt-3">
              <label for="conteo-justificacion">Explicación del conteo y la diferencia</label>
              <textarea id="conteo-justificacion" v-model="conciliacionForm.justificacion" minlength="10" maxlength="2000" required></textarea>
            </div>
            <p><label><input v-model="conciliacionForm.alcance_total" type="checkbox" required /> Confirmo que el conteo cubre todas las ubicaciones físicas de este artículo.</label></p>
            <p><label><input v-model="conciliacionForm.conteo_verificado" type="checkbox" required /> Confirmo que contrasté las cantidades con el acta y que el conteo es correcto.</label></p>
            <button class="btn-primary" type="submit" :disabled="guardandoConciliacion || !conciliacionForm.alcance_total || !conciliacionForm.conteo_verificado">
              {{ guardandoConciliacion ? 'Registrando...' : 'Conciliar saldo inicial' }}
            </button>
          </form>
          <p v-else-if="!areasOperativas.length">No hay áreas activas para registrar un conteo por ubicación.</p>
          <p v-else>Un administrador debe registrar el conteo físico.</p>
        </template>
      </section>
      <button v-if="puedeOperar && (articuloSeleccionado.apertura || articuloSeleccionado.base_kardex?.operable)" class="btn-primary mt-4" @click="iniciarTransaccion">
        + Nueva Transacción
      </button>
      <section v-if="kardexDigital" class="context-box mt-4" aria-label="Kárdex digital por artículo">
        <h3>Kárdex digital por artículo</h3>
        <p v-if="!kardexDigital.base">Aún no hay saldo de apertura ni cierre documental disponible.</p>
        <template v-else>
          <p>Base: <strong>{{ kardexDigital.base.cantidad }} u.</strong> ·
            {{ kardexDigital.base.origen === 'KARDEX_HISTORICO' ? 'Cierre del Kárdex escaneado' : 'Conteo físico aprobado' }}
            <span v-if="kardexDigital.base.lote_historico_id"> · Lote #{{ kardexDigital.base.lote_historico_id }}, movimiento #{{ kardexDigital.base.movimiento_historico_id }}</span>
            <span v-if="kardexDigital.base.fecha_corte"> · Corte: {{ fechaRegistro(kardexDigital.base.fecha_corte) }}</span>
          </p>
          <p v-if="kardexDigital.base.referencia_documento">Documento de apertura: {{ kardexDigital.base.referencia_documento }}</p>
          <p v-if="kardexDigital.estado === 'BASE_DOCUMENTAL_SIN_CORTE'" class="text-muted">
            Esta es una base documental provisional. Aún no hay operaciones digitales posteriores al corte.
          </p>
          <p v-if="kardexDigital.integridad === false" role="alert" class="hint hint-danger">
            La secuencia digital no coincide con el saldo actual. Detén nuevas operaciones y solicita revisión.
          </p>
          <p v-if="kardexDigital.estado === 'OPERATIVO'">Saldo calculado: <strong>{{ kardexDigital.saldo_final }} u.</strong></p>
          <button class="btn-primary" type="button" :disabled="descargandoKardex" @click="descargarKardexDigital">
            {{ descargandoKardex ? 'Preparando CSV...' : 'Descargar Kárdex digital (CSV)' }}
          </button>
          <p v-if="!kardexDigital.eventos.length" class="text-muted">Sin operaciones digitales posteriores al corte.</p>
          <div v-else class="tabla-scroll"><table class="tabla-movimientos">
            <thead><tr><th>Registro</th><th>Hecho</th><th>Operación</th><th>Ubicación</th><th>Ingreso</th><th>Salida</th><th>Saldo</th><th>Documento</th></tr></thead>
            <tbody><tr v-for="evento in kardexDigital.eventos" :key="`${evento.clase}-${evento.id}`">
              <td>{{ fechaRegistro(evento.fecha_registro) }}</td>
              <td>{{ evento.fecha_operacion ? fechaRegistro(evento.fecha_operacion) : (evento.fecha_documental || 'No informada') }}</td>
              <td>{{ evento.descripcion }}
                <small v-if="evento.movimiento_origen_id" class="text-muted">Entrega original #{{ evento.movimiento_origen_id }} · devuelve {{ evento.devuelto_por }}</small>
                <small v-if="evento.corrige_movimiento_id" class="text-muted">Rectifica #{{ evento.corrige_movimiento_id }}: {{ evento.cantidad_anterior }} → {{ evento.cantidad_corregida }} u. · {{ evento.motivo_correccion }}</small>
                <small v-if="evento.custodia_id" class="text-muted">Custodia #{{ evento.custodia_id }} · {{ evento.receptor || evento.cantidad_transferida + ' u. trasladadas' }}</small>
                <small v-if="evento.estado === 'ANULADO'" class="text-muted">Anulado · cantidad original {{ evento.cantidad_original }} u.</small>
                <small v-for="aviso in evento.alertas_control || []" :key="aviso.codigo">{{ aviso.codigo }}: {{ aviso.mensaje }}</small>
                <small v-if="evento.justificacion_alertas">Justificación: {{ evento.justificacion_alertas }}</small>
              </td>
              <td>{{ evento.area_origen || '—' }}<span v-if="evento.area_destino"> → {{ evento.area_destino }}</span><small v-if="evento.clase === 'TRANSFERENCIA'">{{ evento.cantidad_transferida }} u. trasladadas</small></td>
              <td class="num ingreso">{{ evento.ingreso || '—' }}</td>
              <td class="num salida">{{ evento.salida || '—' }}</td>
              <td class="num saldo">{{ evento.saldo_institucional }}</td>
              <td>{{ evento.documento || 'Sin referencia histórica' }}</td>
            </tr></tbody>
          </table></div>
        </template>
      </section>
      
      <section class="context-box mt-4" aria-label="Consultar trazabilidad">
        <button type="button" :aria-expanded="mostrarTrazabilidad" @click="mostrarTrazabilidad = !mostrarTrazabilidad">{{ mostrarTrazabilidad ? 'Cerrar trazabilidad' : 'Ver grafo y respaldos del artículo' }}</button>
        <TrazabilidadArticulo v-if="mostrarTrazabilidad" :key="articuloSeleccionado.id" :articulo-id="articuloSeleccionado.id" />
      </section>
      <h3 class="mt-4">Historial de Operaciones (Modernas)</h3>
      <p v-if="cargandoHistorial" class="text-muted">Cargando...</p>
      <p v-else-if="movimientosModernos.length === 0" class="text-muted">
        Aún no hay operaciones modernas registradas para este artículo.
      </p>
      <div v-else class="tabla-scroll"><table class="tabla-movimientos">
        <thead>
          <tr>
            <th>Fecha de operación / registro</th>
            <th>Operación</th>
            <th>Detalle</th>
            <th>Ingreso</th>
            <th>Salida</th>
            <th>Saldo</th>
            <th>Encargado</th>
            <th>Registrado por</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in movimientosModernos" :key="m.id" :class="{'fila-anulada': m.estado === 'ANULADO'}">
            <td>
              <div>Ocurrió: {{ m.ocurrido_en ? fechaRegistro(m.ocurrido_en) : m.fecha_movimiento }}</div>
              <small class="text-muted">Registrado: {{ fechaRegistro(m.registrado_en) }}</small>
            </td>
            <td>
              <strong>{{ m.tipo_operacion || m.nodo_grafo || '-' }}</strong>
              <small v-if="!articuloSeleccionado.apertura || m.id <= articuloSeleccionado.apertura.ultimo_moderno_id" class="text-muted">Antecedente: no afecta al stock actual</small>
              <span v-if="m.estado === 'ANULADO'" class="badge-anulado">ANULADO</span>
            </td>
            <td>
              <div v-if="m.receptor">Receptor: {{ m.receptor }}</div>
              <div v-if="m.movimiento_origen_id">Devuelve {{ m.devuelto_por }} · entrega original #{{ m.movimiento_origen_id }}</div>
              <div v-if="m.corrige_movimiento_id">Rectifica movimiento #{{ m.corrige_movimiento_id }}: {{ m.cantidad_anterior }} → {{ m.cantidad_corregida }} u.</div>
              <div v-if="m.motivo_correccion">Motivo: {{ m.motivo_correccion }} · Autorizó cuenta #{{ m.autorizado_por_id }}</div>
              <div v-if="m.receptor_tipo">Tipo de receptor: {{ m.receptor_tipo }}</div>
              <div>Ubicación: {{ m.area_operativa_id ? (areasOperativas.find(a => a.id === m.area_operativa_id)?.nombre || `Área #${m.area_operativa_id}`) : 'Sin ubicación confirmada' }}</div>
              <div v-if="m.ciudad_feria">Feria: {{ m.ciudad_feria }}</div>
              <div v-if="m.referencia_documento">Documento: {{ m.referencia_documento }}</div>
              <div class="text-muted">{{ m.observaciones || m.detalle }}</div>
              <div v-for="aviso in m.alertas_control || []" :key="aviso.codigo" class="aviso-historial">⚠️ {{ aviso.mensaje }}</div>
              <div v-if="m.justificacion_alertas"><strong>Justificación:</strong> {{ m.justificacion_alertas }}</div>
            </td>
            <td class="num ingreso">{{ m.estado === 'ANULADO' ? '-' : (m.ingresos ?? '') }}</td>
            <td class="num salida">{{ m.estado === 'ANULADO' ? '-' : (m.salidas ?? '') }}</td>
            <td class="num saldo">{{ m.saldo_registrado }}</td>
            <td><small>{{ m.encargado_nombre || 'No registrado' }}</small></td>
            <td><small>{{ m.usuario_operador || '-' }}</small></td>
            <td>
              <button v-if="esAdmin && articuloSeleccionado.apertura && m.id > articuloSeleccionado.apertura.ultimo_moderno_id && m.estado === 'ACTIVO' && !m.corrige_movimiento_id && !['Ajuste de Conciliación Inicial', 'Ajuste operativo'].includes(m.tipo_operacion || '')"
                type="button" class="btn-icon" :aria-label="`Rectificar movimiento ${m.id}`"
                @click="seleccionarRectificacion(m)">Rectificar</button>
            </td>
          </tr>
        </tbody>
      </table></div>
      <section v-if="esAdmin && articuloSeleccionado.apertura" class="context-box mt-4" aria-label="Correcciones y ajustes operativos">
        <h3>Correcciones y ajustes operativos</h3>
        <p>Una rectificación crea un asiento vinculado y conserva el movimiento original. Si un conteo detecta una diferencia sin movimiento concreto, registra un ajuste con acta y motivo.</p>
        <form v-if="movimientoRectificado" aria-label="Rectificar cantidad registrada" @submit.prevent="guardarRectificacion">
          <h4>Rectificar movimiento #{{ movimientoRectificado }}</h4>
          <div class="form-group mt-3"><label for="correccion-cantidad">Cantidad correcta (0 para revertirla)</label>
            <input id="correccion-cantidad" v-model.number="correccionForm.cantidad_corregida" type="number" min="0" step="1" required /></div>
          <div class="form-group mt-3"><label for="correccion-motivo">Motivo verificado</label>
            <textarea id="correccion-motivo" v-model="correccionForm.motivo" minlength="10" maxlength="2000" required></textarea></div>
          <div class="form-group mt-3"><label for="correccion-documento">Acta o documento de autorización</label>
            <input id="correccion-documento" v-model="correccionForm.referencia_documento" minlength="3" maxlength="200" required /></div>
          <button class="btn-primary mt-3" type="submit" :disabled="guardandoCorreccion">{{ guardandoCorreccion ? 'Guardando...' : 'Guardar rectificación' }}</button>
          <button class="btn-icon" type="button" @click="movimientoRectificado = null">Cancelar</button>
        </form>
        <form aria-label="Registrar ajuste operativo" class="mt-4" @submit.prevent="guardarAjuste">
          <h4>Ajuste por diferencia verificada</h4>
          <div class="form-group mt-3"><label for="ajuste-direccion">Efecto</label>
            <select id="ajuste-direccion" v-model="ajusteForm.direccion"><option value="ingreso">Aumentar existencias</option><option value="salida">Disminuir existencias</option></select></div>
          <div class="form-group mt-3"><label for="ajuste-cantidad">Cantidad</label>
            <input id="ajuste-cantidad" v-model.number="ajusteForm.cantidad" type="number" min="1" step="1" required /></div>
          <div class="form-group mt-3"><label for="ajuste-area">Área comprobada</label>
            <select id="ajuste-area" v-model.number="ajusteForm.area_id"><option value="">Sin ubicación confirmada</option>
              <option v-for="area in areasOperativas" :key="area.id" :value="area.id">{{ area.nombre }}</option></select></div>
          <div class="form-group mt-3"><label for="ajuste-encargado">Encargado</label>
            <select id="ajuste-encargado" v-model.number="ajusteForm.encargado_id" required><option disabled value="">Selecciona</option>
              <option v-for="persona in encargados" :key="persona.id" :value="persona.id">{{ persona.nombre }}</option></select></div>
          <div class="form-group mt-3"><label for="ajuste-motivo">Motivo y resultado del conteo</label>
            <textarea id="ajuste-motivo" v-model="ajusteForm.motivo" minlength="10" maxlength="2000" required></textarea></div>
          <div class="form-group mt-3"><label for="ajuste-documento">Acta o documento de autorización</label>
            <input id="ajuste-documento" v-model="ajusteForm.referencia_documento" minlength="3" maxlength="200" required /></div>
          <button class="btn-primary mt-3" type="submit" :disabled="guardandoAjuste">{{ guardandoAjuste ? 'Guardando...' : 'Registrar ajuste' }}</button>
        </form>
      </section>
    </div>

    <!-- PANTALLA NUEVO PRODUCTO -->
    <div v-if="vistaActual === 'nuevo_producto'" class="form-container">
      <h3>Alta de Nuevo Producto</h3>
      <p class="subtitle">Ingresa un producto nuevo que no proviene del kárdex físico antiguo.</p>
      
      <div class="form-group">
        <label>Nombre del Producto:</label>
        <input type="text" v-model="nuevoProducto.nombre" placeholder="Ej: Libro de Arte Moderno" class="w-full" />
      </div>
      
      <p>Después de crear el producto, el administrador podrá aprobar su saldo de apertura a partir de un conteo físico.</p>

      <div class="actions mt-4">
        <button class="btn-primary" @click="guardarNuevoProducto" :disabled="creandoProducto">
          {{ creandoProducto ? 'Guardando...' : 'Crear Producto' }}
        </button>
      </div>
    </div>

    <!-- PANTALLA TRANSACCIÓN -->
    <div v-if="vistaActual === 'transaccion' && articuloSeleccionado" class="form-container">
      <h3>Registrar Transacción</h3>
      <div class="context-box">
        <div class="context-row">
          <div><strong>Activo:</strong> {{ articuloSeleccionado.nombre }}</div>
          <div class="stock-badge stock-ok"><strong>Stock: {{ articuloSeleccionado.stock_actual }} u.</strong></div>
        </div>
      </div>
      
      <div class="form-group mt-3">
        <label>Tipo de Operación:</label>
        <select v-model="tx.tipo_operacion" class="w-full">
          <option disabled value="">Selecciona el tipo...</option>
          <option v-for="op in operacionesCatalogo" :key="op.valor" :value="op.valor" :disabled="!op.habilitada">{{ op.valor }}{{ !op.habilitada ? (op.valor === 'Transferencia Interna' ? ' (usa el formulario por áreas)' : ' (pendiente)') : '' }}</option>
        </select>
        <p v-for="op in operacionesCatalogo.filter(o => !o.habilitada)" :key="op.valor" class="text-muted">{{ op.valor }}: {{ op.motivo_pendiente }}</p>
      </div>

      <div class="form-group mt-3">
        <label>Dirección:</label>
        <select v-model="tx.tipo" class="w-full" :disabled="direccionEsperada !== null">
          <option value="salida">Salida (Disminuye inventario)</option>
          <option value="ingreso">Ingreso (Aumenta inventario)</option>
        </select>
        <p v-if="direccionEsperada" class="text-muted">La dirección se determina por la operación seleccionada.</p>
      </div>
      
      <div class="form-group mt-3">
        <label>Cantidad:</label>
        <input type="number" step="1" v-model.number="tx.cantidad" min="1" class="w-full" />
        <p v-if="tx.tipo === 'salida' && tx.cantidad > (articuloSeleccionado.stock_actual ?? 0)" class="hint hint-danger">
          ⚠️ La cantidad supera el stock disponible ({{ articuloSeleccionado.stock_actual }} u.)
        </p>
      </div>

      <div class="form-group mt-3">
        <label for="movimiento-fecha-operacion">Fecha y hora de la operación (Bolivia):</label>
        <input id="movimiento-fecha-operacion" v-model="tx.fecha_operacion_local" type="datetime-local" step="1" required class="w-full" @input="fechaOperacionEditada = true" />
        <p class="text-muted">Si ocurrió antes de registrar, corrige esta fecha. La hora de registro se guarda automáticamente. No puede ser anterior al corte de apertura.</p>
      </div>

      <div class="form-group mt-3">
        <label for="movimiento-area-operativa">Ubicación física {{ tx.tipo === 'salida' ? 'que entrega' : 'que recibe' }}:</label>
        <select id="movimiento-area-operativa" v-model.number="tx.area_operativa_id" class="w-full">
          <option value="">Sin ubicación confirmada</option>
          <option v-for="area in areasOperativas" :key="area.id" :value="area.id">{{ area.nombre }}</option>
        </select>
        <p class="text-muted">Las salidas descuentan únicamente de la ubicación elegida. Si aún no se verificó el área, se descuentan del saldo sin ubicación.</p>
      </div>

      <div class="form-group mt-3">
        <label for="movimiento-encargado">Encargado del movimiento:</label>
        <select id="movimiento-encargado" v-model.number="tx.encargado_id" class="w-full" required>
          <option disabled value="">Selecciona al encargado...</option>
          <option v-for="persona in encargados" :key="persona.id" :value="persona.id">{{ persona.nombre }}</option>
        </select>
        <p class="text-muted">El usuario que registra se guarda automáticamente con su sesión.</p>
      </div>

      <!-- CAMPOS CONDICIONALES -->
      
      <div v-if="tx.tipo_operacion === 'Transferencia Interna'" class="form-group mt-3">
        <label>Área Destino:</label>
        <select v-model="tx.area_destino" class="w-full">
          <option disabled value="">Selecciona área...</option>
          <option v-for="a in areasCatalogo" :key="a.valor" :value="a.valor">{{ a.etiqueta }}</option>
        </select>
      </div>

      <div v-if="operacionesCatalogo.find(o => o.valor === tx.tipo_operacion)?.requiere_receptor" class="form-group mt-3">
        <label for="receptor-operacion">Persona o institución que recibe:</label>
        <input id="receptor-operacion" type="text" v-model="tx.receptor" placeholder="Nombre del cliente, institución o responsable de la feria" class="w-full" maxlength="200" />
        <label for="tipo-receptor-operacion">Tipo de receptor:</label>
        <select id="tipo-receptor-operacion" v-model="tx.receptor_tipo" class="w-full">
          <option disabled value="">Selecciona el tipo...</option>
          <option value="PERSONA">Persona</option>
          <option value="INSTITUCION">Institución</option>
          <option v-if="tx.tipo_operacion === 'Ventas'" value="PUBLICO_GENERAL">Público general (con documento)</option>
        </select>
      </div>

      <div v-if="tx.tipo_operacion === 'Feria' || tx.tipo_operacion === 'Salida a Feria'" class="form-group mt-3">
        <label>Feria (Opcional):</label>
        <select v-model="tx.feria_id" class="w-full">
          <option value="">Otra / No listada</option>
          <option v-for="f in ferias" :key="f.id" :value="f.id">{{ f.nombre }} ({{ f.ciudad }})</option>
        </select>
      </div>

      <div v-if="tx.tipo_operacion === 'Feria' || tx.tipo_operacion === 'Salida a Feria'" class="form-group mt-3">
        <label>Ciudad de Feria:</label>
        <input type="text" v-model="tx.ciudad_feria" placeholder="Ej: Sucre..." class="w-full" />
      </div>

      <div v-if="tx.tipo_operacion === 'Ventas'" class="form-group mt-3">
        <label>Canal de Venta:</label>
        <select v-model="tx.canal_venta" class="w-full">
          <option value="Venta Directa">Venta Directa</option>
          <option value="Feria">En Feria</option>
          <option value="Librería">Librería externa</option>
        </select>
      </div>

      <div v-if="tx.tipo_operacion === 'Baja / Pérdida'" class="form-group mt-3">
        <label>Motivo de Baja:</label>
        <select v-model="tx.motivo_baja" class="w-full">
          <option disabled value="">Selecciona motivo...</option>
          <option value="Deterioro">Deterioro / Daño</option>
          <option value="Extravío">Extravío / Robo</option>
          <option value="Obsolescencia">Obsolescencia</option>
        </select>
      </div>
      
      <!-- COMUNES -->
      
      <div class="form-group mt-3">
        <label for="movimiento-referencia">Referencia / Documento:</label>
        <input id="movimiento-referencia" type="text" v-model="tx.referencia" placeholder="Nro Memorándum, Factura, Acta..." class="w-full" minlength="3" maxlength="200" required />
      </div>

      <div class="form-group mt-3">
        <label>Observaciones:</label>
        <input type="text" v-model="tx.observaciones" placeholder="Detalles extra de la operación..." class="w-full" />
      </div>

      <div v-if="tx.tipo_operacion === 'Devolución'" class="form-group mt-3">
        <label for="devolucion-origen">Entrega original:</label>
        <select id="devolucion-origen" v-model.number="tx.movimiento_origen_id" class="w-full" required :disabled="cargandoSalidasDevolvibles || errorSalidasDevolvibles">
          <option disabled value="">Selecciona la salida...</option>
          <option v-for="salida in salidasDevolvibles" :key="salida.id" :value="salida.id">
            #{{ salida.id }} · {{ salida.tipo_operacion }} · {{ salida.receptor || 'Sin receptor' }} · {{ salida.cantidad_pendiente }} de {{ salida.cantidad_original }} u. pendientes
          </option>
        </select>
        <p v-if="cargandoSalidasDevolvibles" class="text-muted">Buscando entregas pendientes...</p>
        <p v-else-if="errorSalidasDevolvibles" class="hint-danger">No se pudieron consultar las entregas. Vuelve al detalle y abre de nuevo la transacción.</p>
        <p v-else-if="!salidasDevolvibles.length" class="text-muted">No hay ventas ni donaciones vigentes con unidades pendientes de devolución.</p>
        <label for="devolucion-persona">Persona o institución que devuelve:</label>
        <input id="devolucion-persona" v-model="tx.devuelto_por" class="w-full" maxlength="200" placeholder="Nombre de quien devuelve" />
        <p class="text-muted">La ubicación que recibe y el encargado se indican arriba. El documento de recepción se registra abajo.</p>
      </div>

      <div v-if="alertasPendientes.length" class="alertas-control mt-3" role="alert">
        <strong>Revisa estos avisos antes de guardar:</strong>
        <ul><li v-for="aviso in alertasPendientes" :key="aviso.codigo">{{ aviso.mensaje }}</li></ul>
        <label for="motivo-alertas">Justificación de la operación:</label>
        <textarea id="motivo-alertas" v-model="motivoAlertas" minlength="10" maxlength="1000" rows="3" class="w-full" placeholder="Explica por qué corresponde realizarla..."></textarea>
      </div>

      <div class="actions mt-4">
        <button class="btn-primary" @click="registrarTransaccion" :disabled="creandoTransaccion">
          {{ creandoTransaccion ? 'Registrando...' : (alertasPendientes.length ? 'Confirmar operación alertada' : 'Registrar transacción') }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.inventario-actual-view { background: var(--bg-color); padding: 2.5rem; border-radius: var(--radius); box-shadow: var(--shadow-sm); max-width: 1000px; margin: 2.5rem auto; }
.btn-back { font-size: 1rem; color: var(--text-secondary); text-decoration: none; display: inline-flex; align-items: center; gap: 0.5rem; background:none; border:none; cursor:pointer;}
.btn-back:hover { color: var(--primary); }
.header-nav { display: flex; align-items: center; margin-bottom: 2rem; border-bottom: 1px solid var(--border-color); padding-bottom: 1.5rem; gap: 1rem;}
.header-nav h1 { margin: 0; }
.subtitle { color: var(--text-secondary); margin-bottom: 1.5rem; }
.lista-articulos { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; }
.articulo-card { border: 1px solid var(--border-color); padding: 1.25rem; border-radius: var(--radius); cursor: pointer; transition: all 0.2s; background: var(--bg-body); }
.articulo-card:hover { border-color: var(--primary); background: var(--bg-subtle); transform: translateY(-2px); }
.art-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
.art-codigo { font-size: 0.8rem; color: var(--text-secondary); font-weight: 600; }
.art-nombre { font-size: 1.1rem; font-weight: 500; color: var(--text-primary); }

/* Stock badges */
.stock-badge { padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600; }
.stock-ok { background: #ecfdf5; color: #065f46; }
.stock-zero { background: #fef2f2; color: #991b1b; }
.alertas-control { border: 1px solid #d97706; border-radius: var(--radius); background: #fffbeb; color: #78350f; padding: 1rem; }
.aviso-historial { color: #92400e; font-size: 0.85rem; }
.stock-review { background: #fffbeb; color: #92400e; }

/* Detalle */
.pantalla-detalle { }
.detalle-header { display: flex; justify-content: space-between; align-items: center; padding: 1.5rem; background: var(--bg-subtle); border: 1px solid var(--border-color); border-radius: var(--radius); }
.detalle-header h2 { margin: 0 0 0.3rem 0; }
.stock-display { text-align: center; }
.stock-numero { font-size: 2.5rem; font-weight: 700; color: #065f46; line-height: 1; }
.stock-label { font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.3rem; }

/* Tabla movimientos */
.tabla-movimientos { width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.9rem; }
.tabla-movimientos th { background: var(--bg-subtle); padding: 0.7rem; text-align: left; border-bottom: 2px solid var(--border-color); font-weight: 600; }
.tabla-movimientos td { padding: 0.6rem 0.7rem; border-bottom: 1px solid var(--border-color); }
.tabla-movimientos .num { text-align: right; font-family: monospace; }
.tabla-movimientos .ingreso { color: #065f46; }
.tabla-movimientos .salida { color: #991b1b; }
.tabla-movimientos .saldo { font-weight: 600; }

/* Forms */
.form-container { max-width: 600px; margin: 0 auto; background: var(--bg-body); padding: 2rem; border: 1px solid var(--border-color); border-radius: var(--radius); }
.form-group { display: flex; flex-direction: column; gap: 0.5rem; }
.context-box { background: #f8fafc; padding: 1rem; border-radius: var(--radius); border: 1px dashed var(--border-color); }
.context-row { display: flex; justify-content: space-between; align-items: center; }
.w-full { width: 100%; }
.mt-3 { margin-top: 1rem; }
.mt-4 { margin-top: 1.5rem; }
.hint { font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem; }
.hint-danger { color: #dc2626; font-weight: 500; }
.text-muted { color: var(--text-secondary); font-style: italic; }
.alert { padding: 1rem; border-radius: 6px; margin-bottom: 1.5rem; }
.alert-error { background-color: #fdf2f2; color: #991b1b; }
.alert-success { background-color: #ecfdf5; color: #065f46; }

.fila-anulada { opacity: 0.6; background-color: #fee2e2 !important; text-decoration: line-through; }
.fila-anulada td.saldo { background: transparent; text-decoration: none; }
.badge-anulado { font-size: 0.7rem; background: #dc2626; color: white; padding: 2px 6px; border-radius: 4px; margin-left: 8px; vertical-align: middle;}
.btn-icon { background: none; border: none; cursor: pointer; font-size: 1.1rem; padding: 0.2rem; filter: grayscale(100%); transition: filter 0.2s; }
.btn-icon:hover { filter: grayscale(0%); }

.tabla-scroll { max-width: 100%; overflow-x: auto; }
.detalle-header { gap: 1rem; }
.detalle-header > div { min-width: 0; overflow-wrap: anywhere; }
.form-container, .context-box { overflow-wrap: anywhere; }
@media (max-width: 640px) {
  .inventario-actual-view { padding: 1rem; margin: 1rem auto; min-width: 0; }
  .header-nav, .detalle-header, .context-row { flex-direction: column; align-items: flex-start; }
  .header-nav h1 { font-size: 1.4rem; }
  .form-container { padding: 1rem; }
  .lista-articulos { grid-template-columns: minmax(0, 1fr); }
  .art-header { flex-wrap: wrap; gap: .5rem; }
}
</style>
