<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import api from '@/services/api'

interface Articulo {
  id: number
  nombre: string
  codigo: string
  alertas_rojas: number
  alertas_amarillas: number
  stock_actual: number
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
  tipo_operacion: string | null
  receptor: string | null
  ciudad_feria: string | null
  canal_venta: string | null
  motivo_baja: string | null
  referencia_documento: string | null
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

const articulos = ref<Articulo[]>([])
const buscarTexto = ref('')
const errorMsg = ref('')
const mensajeExito = ref('')

const vistaActual = ref<'buscar' | 'detalle' | 'transaccion' | 'nuevo_producto'>('buscar')
const articuloSeleccionado = ref<Articulo | null>(null)

// Datos para Nuevo Producto
const nuevoProducto = ref({ nombre: '', saldo_inicial: 0 })
const creandoProducto = ref(false)

// Catálogos
const nodosDisponibles = ref<NodoCatalogo[]>([])
const ferias = ref<Feria[]>([])

// Datos para Transacción Enriquecida
const creandoTransaccion = ref(false)
const tx = ref({
  tipo: 'salida', 
  cantidad: 1, 
  tipo_operacion: '', 
  area_destino: '',
  receptor: '',
  feria_id: '' as number | '',
  ciudad_feria: '',
  canal_venta: '',
  motivo_baja: '',
  referencia: '',
  observaciones: ''
})

// Historial moderno
const movimientosModernos = ref<Movimiento[]>([])
const cargandoHistorial = ref(false)

const articulosFiltrados = computed(() => {
  if (!buscarTexto.value) return articulos.value
  const t = buscarTexto.value.toLowerCase()
  return articulos.value.filter(a => a.nombre.toLowerCase().includes(t) || a.codigo.toLowerCase().includes(t))
})

const areasCatalogo = computed(() => nodosDisponibles.value.filter(n => n.grupo === 'Departamentos'))
const operacionesCatalogo = computed(() => nodosDisponibles.value.filter(n => n.grupo === 'Tipo de Operación'))

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
})

async function cargarArticulos() {
  try {
    const res = await api.get('/kardex/articulos')
    articulos.value = res.data
  } catch (err: any) {
    errorMsg.value = "Error al cargar el catálogo."
  }
}

async function cargarCatalogos() {
  try {
    const resNodos = await api.get('/kardex/nodos')
    nodosDisponibles.value = resNodos.data
    const resFerias = await api.get('/kardex/ferias')
    ferias.value = resFerias.data
  } catch (err) {
    console.error("Error al cargar catálogos", err)
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

function verDetalle(art: Articulo) {
  articuloSeleccionado.value = art
  vistaActual.value = 'detalle'
  errorMsg.value = ''
  mensajeExito.value = ''
  cargarHistorialModerno()
}

function iniciarTransaccion() {
  vistaActual.value = 'transaccion'
  tx.value = {
    tipo: 'salida', cantidad: 1, tipo_operacion: '', area_destino: '',
    receptor: '', feria_id: '', ciudad_feria: '', canal_venta: '',
    motivo_baja: '', referencia: '', observaciones: ''
  }
  errorMsg.value = ''
  mensajeExito.value = ''
}

function irANuevoProducto() {
  vistaActual.value = 'nuevo_producto'
  nuevoProducto.value = { nombre: '', saldo_inicial: 0 }
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
  errorMsg.value = ''
  mensajeExito.value = ''
  cargarArticulos()
  cargarHistorialModerno()
}

async function guardarNuevoProducto() {
  if (!nuevoProducto.value.nombre.trim()) return (errorMsg.value = "El nombre es obligatorio.")
  creandoProducto.value = true
  errorMsg.value = ''
  try {
    const res = await api.post('/kardex/articulos', { nombre: nuevoProducto.value.nombre })
    const artId = res.data.id
    
    if (nuevoProducto.value.saldo_inicial > 0) {
      await api.post('/kardex/movimiento-actual', {
        articulo_id: artId,
        tipo: 'ingreso',
        cantidad: nuevoProducto.value.saldo_inicial,
        nodo_grafo: 'Entrada: Inventario Inicial',
        observaciones: 'Alta en sistema moderno'
      })
    }
    
    mensajeExito.value = "Producto creado y saldo inicial registrado."
    setTimeout(volver, 2000)
  } catch (err) {
    errorMsg.value = "Error al crear el producto."
  } finally {
    creandoProducto.value = false
  }
}

async function registrarTransaccion() {
  if (!articuloSeleccionado.value) return
  if (!tx.value.tipo_operacion) return (errorMsg.value = "Selecciona el Tipo de Operación.")
  if (tx.value.cantidad <= 0) return (errorMsg.value = "La cantidad debe ser mayor a 0.")
  
  // Validaciones condicionales
  if (tx.value.tipo_operacion === 'Transferencia Interna' && !tx.value.area_destino) return (errorMsg.value = "Selecciona el área de destino.")
  if (tx.value.tipo_operacion === 'Obsequios y Donaciones' && !tx.value.receptor) return (errorMsg.value = "Ingresa el nombre del receptor.")
  if (tx.value.tipo_operacion === 'Salida a Feria' && !tx.value.feria_id && !tx.value.ciudad_feria) return (errorMsg.value = "Ingresa la feria y/o ciudad.")
  if (tx.value.tipo_operacion === 'Baja / Pérdida' && !tx.value.motivo_baja) return (errorMsg.value = "Selecciona el motivo de baja.")

  creandoTransaccion.value = true
  errorMsg.value = ''
  
  // Determinar nodo grafo según la operación
  let nodo = tx.value.tipo_operacion
  if (nodo === 'Transferencia Interna') nodo = tx.value.area_destino
  if (nodo === 'Salida a Feria') nodo = 'Feria'
  
  try {
    await api.post('/kardex/movimiento-actual', {
      articulo_id: articuloSeleccionado.value.id,
      tipo: tx.value.tipo,
      cantidad: tx.value.cantidad,
      nodo_grafo: nodo,
      tipo_operacion: tx.value.tipo_operacion,
      receptor: tx.value.receptor,
      feria_id: tx.value.feria_id || null,
      ciudad_feria: tx.value.ciudad_feria,
      canal_venta: tx.value.canal_venta,
      motivo_baja: tx.value.motivo_baja,
      referencia_documento: tx.value.referencia,
      observaciones: tx.value.observaciones
    })
    mensajeExito.value = "Transacción registrada correctamente."
    const delta = tx.value.tipo === 'ingreso' ? tx.value.cantidad : -tx.value.cantidad
    articuloSeleccionado.value!.stock_actual += delta
    setTimeout(volverADetalle, 1500)
  } catch (err: any) {
    if (err.response?.status === 400) {
      errorMsg.value = err.response.data.detail
    } else {
      errorMsg.value = "Error al registrar la transacción."
    }
  } finally {
    creandoTransaccion.value = false
  }
}

async function anularTransaccion(movId: number) {
  if (!confirm("¿Estás seguro de anular esta transacción? Se recalcularán los saldos posteriores automáticamente.")) return
  
  try {
    await api.post(`/kardex/movimiento-actual/${movId}/anular`)
    alert("Transacción anulada con éxito.")
    cargarHistorialModerno()
    // Volver a cargar el artículo para que actualice el saldo_actual arriba
    const res = await api.get('/kardex/articulos')
    articulos.value = res.data
    const art = articulos.value.find(a => a.id === articuloSeleccionado.value?.id)
    if (art) articuloSeleccionado.value = art
  } catch (err: any) {
    alert("Error al anular: " + (err.response?.data?.detail || err.message))
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
      
      <button v-if="vistaActual === 'buscar'" class="btn-primary" @click="irANuevoProducto">
        + Nuevo Producto
      </button>
    </div>
    
    <p v-if="errorMsg" class="alert alert-error">{{ errorMsg }}</p>
    <p v-if="mensajeExito" class="alert alert-success">{{ mensajeExito }}</p>

    <!-- PANTALLA BUSCAR -->
    <div v-if="vistaActual === 'buscar'" class="pantalla-buscar">
      <p class="subtitle">Selecciona un artículo para ver su stock actual y registrar operaciones en vivo.</p>
      <div class="search-box">
        <i class="pi pi-search search-icon"></i>
        <input type="text" v-model="buscarTexto" placeholder="Buscar producto..." class="search-input"/>
      </div>

      <div class="lista-articulos">
        <div v-for="art in articulosFiltrados" :key="art.id" class="articulo-card" @click="verDetalle(art)">
          <div class="art-header">
            <div class="art-codigo">{{ art.codigo }}</div>
            <div class="stock-badge" :class="art.stock_actual > 0 ? 'stock-ok' : 'stock-zero'">
              {{ art.stock_actual }} u.
            </div>
          </div>
          <div class="art-nombre">{{ art.nombre }}</div>
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
          <div class="stock-numero">{{ articuloSeleccionado.stock_actual }}</div>
          <div class="stock-label">Stock Actual</div>
        </div>
      </div>

      <button class="btn-primary mt-4" @click="iniciarTransaccion">
        + Nueva Transacción
      </button>
      
      <h3 class="mt-4">Historial de Operaciones (Modernas)</h3>
      <p v-if="cargandoHistorial" class="text-muted">Cargando...</p>
      <p v-else-if="movimientosModernos.length === 0" class="text-muted">
        Aún no hay operaciones modernas registradas para este artículo. El stock proviene del último Kárdex escaneado.
      </p>
      <table v-else class="tabla-movimientos">
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Operación</th>
            <th>Detalle</th>
            <th>Ingreso</th>
            <th>Salida</th>
            <th>Saldo</th>
            <th>Operador</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in movimientosModernos" :key="m.id" :class="{'fila-anulada': m.estado === 'ANULADO'}">
            <td>{{ m.fecha_movimiento }}</td>
            <td>
              <strong>{{ m.tipo_operacion || m.nodo_grafo || '-' }}</strong>
              <span v-if="m.estado === 'ANULADO'" class="badge-anulado">ANULADO</span>
            </td>
            <td>
              <div v-if="m.receptor">Receptor: {{ m.receptor }}</div>
              <div v-if="m.ciudad_feria">Feria: {{ m.ciudad_feria }}</div>
              <div class="text-muted">{{ m.observaciones || m.detalle }}</div>
            </td>
            <td class="num ingreso">{{ m.estado === 'ANULADO' ? '-' : (m.ingresos ?? '') }}</td>
            <td class="num salida">{{ m.estado === 'ANULADO' ? '-' : (m.salidas ?? '') }}</td>
            <td class="num saldo">{{ m.saldo_registrado }}</td>
            <td><small>{{ m.usuario_operador || '-' }}</small></td>
            <td>
              <button 
                v-if="m.estado !== 'ANULADO'" 
                @click="anularTransaccion(m.id)" 
                class="btn-icon" 
                title="Anular Transacción"
              >
                🚫
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- PANTALLA NUEVO PRODUCTO -->
    <div v-if="vistaActual === 'nuevo_producto'" class="form-container">
      <h3>Alta de Nuevo Producto</h3>
      <p class="subtitle">Ingresa un producto nuevo que no proviene del kárdex físico antiguo.</p>
      
      <div class="form-group">
        <label>Nombre del Producto:</label>
        <input type="text" v-model="nuevoProducto.nombre" placeholder="Ej: Libro de Arte Moderno" class="w-full" />
      </div>
      
      <div class="form-group mt-3">
        <label>Saldo / Cantidad Inicial:</label>
        <input type="number" v-model="nuevoProducto.saldo_inicial" min="0" class="w-full" />
      </div>

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
          <option v-for="op in operacionesCatalogo" :key="op.valor" :value="op.valor">{{ op.etiqueta }}</option>
        </select>
      </div>

      <div class="form-group mt-3">
        <label>Dirección:</label>
        <select v-model="tx.tipo" class="w-full">
          <option value="salida">Salida (Disminuye inventario)</option>
          <option value="ingreso">Ingreso (Aumenta inventario)</option>
        </select>
      </div>
      
      <div class="form-group mt-3">
        <label>Cantidad:</label>
        <input type="number" step="1" v-model.number="tx.cantidad" min="1" class="w-full" />
        <p v-if="tx.tipo === 'salida' && tx.cantidad > articuloSeleccionado.stock_actual" class="hint hint-danger">
          ⚠️ La cantidad supera el stock disponible ({{ articuloSeleccionado.stock_actual }} u.)
        </p>
      </div>

      <!-- CAMPOS CONDICIONALES -->
      
      <div v-if="tx.tipo_operacion === 'Transferencia Interna'" class="form-group mt-3">
        <label>Área Destino:</label>
        <select v-model="tx.area_destino" class="w-full">
          <option disabled value="">Selecciona área...</option>
          <option v-for="a in areasCatalogo" :key="a.valor" :value="a.valor">{{ a.etiqueta }}</option>
        </select>
      </div>

      <div v-if="tx.tipo_operacion === 'Transferencia Interna' || tx.tipo_operacion === 'Obsequios y Donaciones' || tx.tipo_operacion === 'Consignación'" class="form-group mt-3">
        <label>Receptor / Persona de Contacto:</label>
        <input type="text" v-model="tx.receptor" placeholder="Nombre de quien recibe..." class="w-full" />
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
        <label>Referencia / Documento:</label>
        <input type="text" v-model="tx.referencia" placeholder="Nro Memorándum, Factura, Acta..." class="w-full" />
      </div>

      <div class="form-group mt-3">
        <label>Observaciones:</label>
        <input type="text" v-model="tx.observaciones" placeholder="Detalles extra de la operación..." class="w-full" />
      </div>

      <div class="actions mt-4">
        <button class="btn-primary" @click="registrarTransaccion" :disabled="creandoTransaccion">
          {{ creandoTransaccion ? 'Registrando...' : 'Confirmar Transacción' }}
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
.search-box { position: relative; margin-bottom: 2rem; }
.search-icon { position: absolute; left: 1rem; top: 50%; transform: translateY(-50%); color: var(--text-muted); }
.search-input { padding-left: 2.5rem !important; font-size: 1.1rem !important; padding-top: 1rem !important; padding-bottom: 1rem !important; width: 100%;}
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

</style>
