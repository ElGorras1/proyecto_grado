<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import { use } from 'echarts/core'
import { SankeyChart } from 'echarts/charts'
import { TooltipComponent, TitleComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import api from '@/services/api'

use([SankeyChart, TooltipComponent, TitleComponent, CanvasRenderer])

// Tipos
interface Articulo {
  id: number
  nombre: string
  codigo: string
  alertas_rojas: number
  alertas_amarillas: number
}

interface Movimiento {
  id: number
  fecha_movimiento: string
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
}

// Estados Globales
const articulos = ref<Articulo[]>([])
const articuloSeleccionado = ref<Articulo | null>(null)
const buscarTexto = ref('')
const errorMsg = ref('')
const mensajeExito = ref('')

// Vistas
const vistaActual = ref<'buscar' | 'crear' | 'historial' | 'subir_lote'>('buscar')
const subPestaña = ref<'historial' | 'hil' | 'grafo'>('historial')

// Historial y Errores
const movimientos = ref<Movimiento[]>([])
const erroresHIL = ref<Movimiento[]>([])
const cargandoHistorial = ref(false)

// Subida de Lote
const archivos = ref<File[]>([])
const subiendo = ref(false)

// Crear Artículo
const nuevoArticuloNombre = ref('')
const creandoArticulo = ref(false)

// Auditoría y Edición (HIL)
const filaEditando = ref<number | null>(null)
const editForm = ref({ ingresos: 0 as number | null, salidas: 0 as number | null, saldo_registrado: 0, nodo_grafo: '' as string | null })
const imagenAuditoria = ref<string | null>(null)

// ECharts Sankey Option
const sankeyOption = ref<any>(null)

// Computed
const articulosFiltrados = computed(() => {
  if (!buscarTexto.value) return articulos.value
  const t = buscarTexto.value.toLowerCase()
  return articulos.value.filter(a => a.nombre.toLowerCase().includes(t) || a.codigo.toLowerCase().includes(t))
})

onMounted(async () => {
  await cargarArticulos()
})

async function cargarArticulos() {
  try {
    const res = await api.get('/kardex/articulos')
    articulos.value = res.data
  } catch (err: any) {
    errorMsg.value = "Error al cargar el catálogo de artículos."
  }
}

function seleccionarArticulo(art: Articulo) {
  articuloSeleccionado.value = art
  vistaActual.value = 'historial'
  subPestaña.value = 'historial'
  cargarHistorial()
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
  archivos.value = []
  vistaActual.value = 'subir_lote'
  mensajeExito.value = ''
  errorMsg.value = ''
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

async function cargarGrafoVisual() {
  if (!articuloSeleccionado.value) return
  try {
    const res = await api.get(`/kardex/grafo/${articuloSeleccionado.value.id}`)
    
    // Configuración para el Diagrama Sankey
    sankeyOption.value = {
      title: {
        text: `Flujo Físico: ${articuloSeleccionado.value.nombre}`,
        left: 'center',
        top: 10,
        textStyle: { color: '#332d29', fontWeight: '500' }
      },
      tooltip: {
        trigger: 'item',
        triggerOn: 'mousemove',
        formatter: '{b}: {c} unidades'
      },
      series: [
        {
          type: 'sankey',
          layout: 'none',
          emphasis: { focus: 'adjacency' },
          data: res.data.nodes,
          links: res.data.links,
          lineStyle: {
            color: 'source',
            curveness: 0.5,
            opacity: 0.4
          },
          itemStyle: {
            borderWidth: 1,
            borderColor: '#333'
          },
          label: {
            color: '#333',
            fontSize: 13,
            fontWeight: 'bold'
          }
        }
      ]
    }
  } catch (err) {
    errorMsg.value = "Error al dibujar el grafo visual."
  }
}

function cambiarPestaña(tab: 'historial' | 'hil' | 'grafo') {
  subPestaña.value = tab
  if (tab === 'historial') cargarHistorial()
  if (tab === 'hil') cargarErroresHIL()
  if (tab === 'grafo') cargarGrafoVisual()
}

// Logica subida de lote
function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files) archivos.value = Array.from(target.files)
}

async function subirLote() {
  if (!articuloSeleccionado.value) return
  if (archivos.value.length === 0) return errorMsg.value = "Selecciona al menos una imagen."
  
  subiendo.value = true
  errorMsg.value = ''; mensajeExito.value = ''
  
  const formData = new FormData()
  formData.append('articulo_id', articuloSeleccionado.value.id.toString())
  archivos.value.forEach(file => formData.append('archivos', file))

  try {
    await api.post('/kardex/upload-lote', formData, { timeout: 120000 })
    mensajeExito.value = "Lote escaneado exitosamente."
    archivos.value = []
    cambiarPestaña('historial')
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || "Error subiendo el lote a procesar."
  } finally {
    subiendo.value = false
  }
}

// Logica HIL
function iniciarEdicionHIL(mov: Movimiento) {
  filaEditando.value = mov.id
  editForm.value = {
    ingresos: mov.ingresos,
    salidas: mov.salidas,
    saldo_registrado: mov.saldo_registrado,
    nodo_grafo: mov.nodo_grafo
  }
  if (mov.ruta_imagen_respaldo) {
    imagenAuditoria.value = '/' + mov.ruta_imagen_respaldo.replace(/\\/g, '/')
  }
}

function cerrarEdicionHIL() {
  filaEditando.value = null
  imagenAuditoria.value = null
}

async function guardarEdicionHIL(mov: Movimiento) {
  try {
    await api.put(`/kardex/movimiento/${mov.id}`, editForm.value)
    mensajeExito.value = "Corrección aplicada. Saldos y nodos recalculados."
    cerrarEdicionHIL()
    await cargarErroresHIL() // refresh HIL list
    setTimeout(() => { mensajeExito.value = '' }, 3000)
  } catch(err: any) {
    errorMsg.value = "Error al corregir el registro."
  }
}

function verFoto(ruta: string | null) {
  if (ruta) imagenAuditoria.value = '/' + ruta.replace(/\\/g, '/')
}
</script>

<template>
  <div class="kardex-continuo-view">
    <div class="header-nav">
      <router-link v-if="vistaActual === 'buscar'" to="/" class="btn-back"><i class="pi pi-arrow-left"></i> Panel Principal</router-link>
      <button v-else class="btn-back" @click="irABuscar" style="background:none;border:none;cursor:pointer;"><i class="pi pi-arrow-left"></i> Volver al Catálogo</button>
      
      <h1>Kárdex Digital Continuo</h1>
      <div style="flex-grow:1"></div>
      
      <button v-if="vistaActual === 'buscar'" class="btn-primary" @click="irACrearArticulo">
        + Nuevo Artículo
      </button>
    </div>
    
    <p v-if="errorMsg" class="alert alert-error">{{ errorMsg }}</p>
    <p v-if="mensajeExito" class="alert alert-success">{{ mensajeExito }}</p>

    <!-- PANTALLA 1: BUSCADOR -->
    <div v-if="vistaActual === 'buscar'" class="pantalla-buscar">
      <div class="search-box">
        <i class="pi pi-search search-icon"></i>
        <input type="text" v-model="buscarTexto" placeholder="Buscar artículos ya escaneados por nombre o código..." class="search-input"/>
      </div>

      <div class="lista-articulos">
        <div v-for="art in articulosFiltrados" :key="art.id" class="articulo-card" @click="seleccionarArticulo(art)">
          <div class="art-header">
            <div class="art-codigo">{{ art.codigo }}</div>
            <div class="art-badges">
              <span v-if="art.alertas_rojas > 0" class="badge-alert red" title="Errores Matemáticos">🔴 {{ art.alertas_rojas }}</span>
              <span v-if="art.alertas_amarillas > 0" class="badge-alert yellow" title="Clasificaciones Dudosas">🟡 {{ art.alertas_amarillas }}</span>
              <span v-if="art.alertas_rojas === 0 && art.alertas_amarillas === 0" class="badge-alert green" title="Kárdex Sano">✅ Al día</span>
            </div>
          </div>
          <div class="art-nombre">{{ art.nombre }}</div>
        </div>
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
        <h3>Subir Fotografías del Kárdex</h3>
        <div class="upload-controls">
          <input type="file" multiple accept="image/*" @change="handleFileChange" class="file-input"/>
          <button class="btn-primary" @click="subirLote" :disabled="subiendo || archivos.length === 0">
            {{ subiendo ? 'Extrayendo con IA...' : 'Procesar Imágenes' }}
          </button>
        </div>
        <p class="hint" v-if="archivos.length > 0">{{ archivos.length }} archivo(s) seleccionado(s).</p>
      </div>
    </div>

    <!-- PANTALLA 4: VISTA DE ARTÍCULO (TABS) -->
    <div v-if="vistaActual === 'historial' && articuloSeleccionado" class="pantalla-historial">
      <div class="context-header with-action">
        <div>
          <span class="label">Activo:</span>
          <span class="value">[{{ articuloSeleccionado.codigo }}] {{ articuloSeleccionado.nombre }}</span>
        </div>
        <button class="btn-outline btn-small" @click="irASubirLote">+ Escanear más páginas</button>
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
          <i class="pi pi-share-alt"></i> Grafo de Flujo
        </button>
      </div>

      <div v-if="cargandoHistorial" class="loading-state">Cargando datos...</div>
      
      <!-- TAB 1: HISTORIAL -->
      <div v-else-if="subPestaña === 'historial'">
        <table v-if="movimientos.length > 0" class="tabla-kardex">
          <thead>
            <tr>
              <th>Fecha</th><th>Detalle / Ref</th><th>Ingreso</th><th>Salida</th><th>Saldo</th><th>Nodo Clasificado</th><th>Auditoría</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="mov in movimientos" :key="mov.id" :class="{'fila-error': mov.tiene_error_saldo, 'fila-dudosa': mov.requiere_auditoria_nodo}">
              <td>{{ mov.fecha_movimiento }}</td>
              <td>
                <strong>{{ mov.detalle }}</strong><br/>
                <span class="ref">Ref: {{ mov.referencia || '-' }} | Área: {{ mov.area || '-' }}</span>
              </td>
              <td>{{ mov.ingresos !== null ? mov.ingresos : '-' }}</td>
              <td>{{ mov.salidas !== null ? mov.salidas : '-' }}</td>
              <td><strong>{{ mov.saldo_registrado }}</strong></td>
              <td>{{ mov.nodo_grafo || '-' }}</td>
              <td>
                <button class="btn-outline btn-small" @click="verFoto(mov.ruta_imagen_respaldo)" title="Ver Foto">📸 Foto</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state">No hay registros. <button class="btn-primary" @click="irASubirLote">Comenzar a escanear</button></div>
      </div>

      <!-- TAB 2: AUDITORÍA HIL -->
      <div v-else-if="subPestaña === 'hil'">
        <div v-if="erroresHIL.length === 0" class="empty-state">
          <h3>¡Todo está perfecto!</h3>
          <p>No se encontraron inconsistencias en este artículo.</p>
        </div>
        <table v-else class="tabla-kardex tabla-errores">
          <thead>
            <tr>
              <th>Alerta</th><th>Fecha</th><th>Texto Original (OCR)</th><th>Ing/Sal</th><th>Saldo</th><th>Nodo Grafo Asignado</th><th>Acción HIL</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="err in erroresHIL" :key="err.id" :class="{'fila-editando': filaEditando === err.id}">
              <td style="font-size: 1.2rem; text-align: center;">
                <span v-if="err.tiene_error_saldo" title="Error Matemático">🔴</span>
                <span v-if="err.requiere_auditoria_nodo" title="Clasificación Dudosa">🟡</span>
              </td>
              <td>{{ err.fecha_movimiento }}</td>
              <td class="detalle-col">
                <strong>Detalle:</strong> {{ err.detalle || '-' }} <br/>
                <strong>Ref:</strong> {{ err.referencia || '-' }} | <strong>Área:</strong> {{ err.area || '-' }}
              </td>
              
              <template v-if="filaEditando === err.id">
                <td>
                  <input type="number" v-model="editForm.ingresos" class="inline-edit" placeholder="Ing"/>
                  <input type="number" v-model="editForm.salidas" class="inline-edit mt-1" placeholder="Sal"/>
                </td>
                <td><input type="number" v-model="editForm.saldo_registrado" class="inline-edit" placeholder="Saldo"/></td>
                <td><input type="text" v-model="editForm.nodo_grafo" class="inline-edit text-edit" placeholder="Nodo Grafo"/></td>
                <td>
                  <button class="btn-primary btn-small mb-1" @click="guardarEdicionHIL(err)">Guardar</button>
                  <button class="btn-outline btn-small" @click="cerrarEdicionHIL">Cancelar</button>
                </td>
              </template>
              
              <template v-else>
                <td>I: {{ err.ingresos !== null ? err.ingresos : '-' }}<br/>S: {{ err.salidas !== null ? err.salidas : '-' }}</td>
                <td>
                  <span :class="{'error-val': err.tiene_error_saldo}">Papel: {{ err.saldo_registrado }}</span><br/>
                  <span class="esperado-val" v-if="err.tiene_error_saldo">Calc: {{ err.saldo_calculado }}</span>
                </td>
                <td><span :class="{'nodo-dudoso': err.requiere_auditoria_nodo}">{{ err.nodo_grafo }}</span></td>
                <td><button class="btn-outline btn-small" @click="iniciarEdicionHIL(err)">Resolver <i class="pi pi-check-circle"></i></button></td>
              </template>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- TAB 3: GRAFO VISUAL -->
      <div v-else-if="subPestaña === 'grafo'">
        <div class="grafo-wrapper">
          <v-chart v-if="sankeyOption" class="chart" :option="sankeyOption" autoresize />
          <div v-else class="text-center mt-5 text-muted">Cargando diagrama Sankey...</div>
        </div>
      </div>
    </div>

    <!-- Visor de fotos HIL Modal -->
    <div v-if="imagenAuditoria" class="visor-evidencia">
      <div class="visor-header">
        <h4>Evidencia Física</h4>
        <button class="btn-close" @click="imagenAuditoria = null">✖</button>
      </div>
      <div class="visor-body">
        <img :src="`http://localhost:8000${imagenAuditoria}`" alt="Hoja de Kárdex" class="evidencia-img" />
      </div>
    </div>
  </div>
</template>

<style scoped>
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
.search-box { position: relative; margin-bottom: 2rem; }
.search-icon { position: absolute; left: 1rem; top: 50%; transform: translateY(-50%); color: var(--text-muted); }
.search-input { padding-left: 2.5rem !important; font-size: 1.1rem !important; padding-top: 1rem !important; padding-bottom: 1rem !important; }
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

/* Tabs */
.tabs { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border-color); }
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
.grafo-wrapper { width: 100%; height: 600px; border: 1px solid var(--border-color); border-radius: var(--radius); background: var(--bg-body); }
.chart { width: 100%; height: 100%; }

/* Generales */
.context-header { background: var(--bg-subtle); padding: 1rem 1.5rem; border-radius: var(--radius); margin-bottom: 1.5rem; border: 1px solid var(--border-color); }
.context-header.with-action { display: flex; justify-content: space-between; align-items: center; }
.empty-state { text-align: center; padding: 4rem; color: var(--text-secondary); background: #f8fafc; border-radius: var(--radius); border: 1px dashed var(--border-color); }
.alert { padding: 1rem; border-radius: 6px; margin-bottom: 1.5rem; }
.alert-error { background-color: #fdf2f2; color: #991b1b; }
.alert-success { background-color: #ecfdf5; color: #065f46; }
</style>
