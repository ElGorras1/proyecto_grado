<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

type Tab = 'operativas' | 'historico' | 'alias' | 'personas'
interface Fila {
  id: number; version: string; nombre?: string; nombre_oficial?: string; codigo?: string | null
  descripcion?: string | null; estado?: string; abreviatura?: string | null; tipo?: string
  activa?: boolean; texto_sucio?: string; area_oficial_id?: number; confirmado?: boolean
  area_id?: number | null; dependencias?: { stock: number; custodias_abiertas: number; usuarios_activos: number }
}
interface Revision { id: number; fecha: string; usuario: string; detalle: { previo: Record<string, unknown> | null; nuevo: Record<string, unknown>; motivo: string } }
const historial = ref<Revision[] | null>(null), tituloHistorial = ref(''), cargandoHistorial = ref(false)
const admin = computed(() => useAuthStore().rol === 'Administrador')
const tab = ref<Tab>('operativas')
const titulos: Record<Tab, string> = { operativas: 'Ubicaciones operativas', historico: 'Catálogo histórico', alias: 'Alias y siglas', personas: 'Personas y adscripción' }
const rutas: Record<Tab, string> = { operativas: '/administracion/areas', historico: '/administracion/areas/catalogo/historico', alias: '/administracion/areas/catalogo/alias', personas: '/administracion/areas/personas/adscripciones' }
const listas = ref<Record<Tab, Fila[]>>({ operativas: [], historico: [], alias: [], personas: [] })
const cargando = ref(false), guardando = ref(false), error = ref(''), mensaje = ref('')
const busqueda = ref(''), pagina = ref(1), abierto = ref(false), editando = ref<Fila | null>(null)
const form = ref(vacio())
function vacio() {
  return { nombre: '', codigo: '', descripcion: '', estado: 'activo', nombre_oficial: '',
    abreviatura: '', tipo: 'departamento', activa: true, texto_sucio: '', area_oficial_id: null as number | null,
    confirmado: false, evidencia_revisada: false, area_id: null as number | null, motivo: '' }
}
const filtradas = computed(() => listas.value[tab.value].filter(f =>
  [f.nombre, f.nombre_oficial, f.codigo, f.abreviatura, f.texto_sucio, f.estado,
    nombreCatalogo(f.area_oficial_id), nombreArea(f.area_id)].join(' ').toLocaleLowerCase().includes(busqueda.value.trim().toLocaleLowerCase())))
const filas = computed(() => filtradas.value.slice((pagina.value - 1) * 20, pagina.value * 20))
const areasActivas = computed(() => listas.value.operativas.filter(a => a.estado === 'activo'))
const areasDeBaja = computed(() => listas.value.operativas.filter(a => a.estado === 'baja'))
const aliasPorRevisar = computed(() => listas.value.alias.filter(a => a.activa && !a.confirmado).length)
const ubicacionesInconsistentes = computed(() => areasDeBaja.value.filter(a =>
  (a.dependencias?.stock ?? 0) > 0 || (a.dependencias?.custodias_abiertas ?? 0) > 0 || (a.dependencias?.usuarios_activos ?? 0) > 0))
watch([tab, busqueda], () => { pagina.value = 1 })
watch(tab, () => { abierto.value = false; error.value = ''; mensaje.value = ''; busqueda.value = ''; historial.value = null; consultaHistorial++; cargandoHistorial.value = false })
watch(() => [form.value.area_oficial_id, form.value.confirmado], () => { form.value.evidencia_revisada = false })
let consulta = 0, consultaHistorial = 0
onUnmounted(() => { consulta++; consultaHistorial++ })
async function verHistorial(fila: Fila) {
  const turno = ++consultaHistorial
  const recursos = { operativas: 'area', historico: 'catalogo_areas', alias: 'sinonimos_area', personas: 'usuario' }
  cargandoHistorial.value = true; historial.value = null; error.value = ''
  tituloHistorial.value = fila.nombre ?? fila.nombre_oficial ?? fila.texto_sucio ?? ''
  try {
    const r = await api.get('/administracion/areas/historial', { params: { recurso: recursos[tab.value], registro_id: fila.id } })
    if (turno === consultaHistorial) historial.value = r.data
  } catch { if (turno === consultaHistorial) error.value = 'No se pudo consultar el historial de cambios.' }
  finally { if (turno === consultaHistorial) cargandoHistorial.value = false }
}
function cambios(r: Revision) {
  const etiquetas: Record<string, string> = { nombre: 'Nombre', nombre_oficial: 'Nombre oficial', codigo: 'Código', descripcion: 'Descripción', estado: 'Estado', abreviatura: 'Sigla', tipo: 'Tipo', activa: 'Vigente', confirmado: 'Confirmado', texto_sucio: 'Lectura', area_oficial_id: 'Equivalencia', area_id: 'Adscripción' }
  function valor(campo: string, v: unknown): string {
    if (v == null) return 'Sin dato'
    if (campo === 'area_id') return nombreArea(Number(v))
    if (campo === 'area_oficial_id') return nombreCatalogo(Number(v)) || String(v)
    return typeof v === 'boolean' ? v ? 'Sí' : 'No' : String(v)
  }
  return Object.entries(r.detalle.nuevo).filter(([k, v]) => etiquetas[k] && r.detalle.previo?.[k] !== v)
    .map(([k, v]) => ({ campo: etiquetas[k], anterior: valor(k, r.detalle.previo?.[k]), nuevo: valor(k, v) }))
}
function nombreCatalogo(id?: number) {
  return listas.value.historico.find(a => a.id === id)?.nombre_oficial ?? ''
}
function nombreArea(id?: number | null) {
  return listas.value.operativas.find(a => a.id === id)?.nombre ?? 'Sin adscripción'
}
function detalle(e: any) {
  return typeof e?.response?.data?.detail === 'string' ? e.response.data.detail : 'No se pudo guardar. Revisa los campos y vuelve a intentar.'
}
async function cargar() {
  const turno = ++consulta
  cargando.value = true; error.value = ''
  try {
    const tabs = Object.keys(rutas) as Tab[]
    const respuestas = await Promise.all(tabs.map(t => api.get(rutas[t])))
    if (turno !== consulta) return
    listas.value = Object.fromEntries(tabs.map((t, i) => [t, respuestas[i].data])) as Record<Tab, Fila[]>
  } catch { if (turno === consulta) error.value = 'No se pudieron cargar las áreas y catálogos. Pulsa Actualizar para reintentar.' }
  finally { if (turno === consulta) cargando.value = false }
}
function editar(fila: Fila | null = null) {
  editando.value = fila
  form.value = { ...vacio(), ...(fila ?? {}), codigo: fila?.codigo ?? '', descripcion: fila?.descripcion ?? '',
    abreviatura: fila?.abreviatura ?? '', area_id: fila?.area_id ?? null, motivo: '', evidencia_revisada: false }
  abierto.value = true; error.value = ''; mensaje.value = ''
}
async function guardar() {
  if (!admin.value || guardando.value || cargando.value) return
  const f = form.value
  let datos: Record<string, unknown> = { motivo: f.motivo, version: editando.value?.version }
  if (tab.value === 'operativas') datos = { ...datos, nombre: f.nombre, codigo: f.codigo || null, descripcion: f.descripcion || null, estado: f.estado }
  if (tab.value === 'historico') datos = { ...datos, nombre_oficial: f.nombre_oficial, abreviatura: f.abreviatura || null, descripcion: f.descripcion || null, tipo: f.tipo, activa: f.activa }
  if (tab.value === 'alias') datos = { ...datos, texto_sucio: f.texto_sucio, area_oficial_id: f.area_oficial_id,
    confirmado: f.confirmado, activa: f.activa, evidencia_revisada: f.evidencia_revisada }
  if (tab.value === 'personas') datos = { ...datos, area_id: f.area_id }
  guardando.value = true; error.value = ''
  try {
    if (editando.value) await api.put(rutas[tab.value] + '/' + editando.value.id, datos)
    else await api.post(rutas[tab.value], datos)
    abierto.value = false; mensaje.value = 'Cambio guardado con su motivo y autoría.'
    await cargar()
  } catch (e) { error.value = detalle(e) }
  finally { guardando.value = false }
}
onMounted(cargar)
</script>

<template>
  <main class="catalogos">
    <nav class="volver"><router-link :to="{ name: 'dashboard' }">← Inicio</router-link>
      <router-link v-if="admin" :to="{ name: 'usuarios' }">Gestionar cuentas y roles</router-link>
    </nav>
    <header><div><h1>Áreas y catálogos</h1><p>Ubicaciones de inventario y lecturas del archivo histórico.</p></div>
      <button class="btn-outline" :disabled="cargando || guardando" @click="cargar">Actualizar</button>
    </header>
    <p v-if="error" role="alert" class="alert alert-error">{{ error }}</p>
    <p v-if="mensaje" role="status" class="alert alert-success">{{ mensaje }}</p>
    <section v-if="!cargando && !error" aria-label="Disponibilidad de áreas">
      <p><strong>{{ areasActivas.length }} {{ areasActivas.length === 1 ? 'ubicación activa' : 'ubicaciones activas' }}</strong> · {{ areasDeBaja.length }} de baja · {{ aliasPorRevisar }} equivalencias vigentes por revisar.</p>
      <p v-if="areasActivas.length < 2" role="status">Las transferencias entre áreas necesitan al menos dos ubicaciones activas. Revisa las bajas y habilita únicamente las áreas respaldadas para el alcance institucional.</p>
      <p v-else>Hay ubicaciones suficientes para transferir; cada operación también comprueba permisos y existencias.</p>
      <p v-if="ubicacionesInconsistentes.length" role="alert">Hay áreas de baja que conservan stock, custodias o usuarios activos. Revisa esas dependencias antes de continuar.</p>
    </section>
    <nav class="pestanas" aria-label="Administración de áreas">
      <button v-for="(titulo, clave) in titulos" :key="clave" :aria-current="tab === clave ? 'page' : undefined"
        :disabled="guardando" @click="tab = clave">{{ titulo }} ({{ listas[clave].length }})</button>
    </nav>
    <p v-if="tab === 'operativas'">Estas ubicaciones pueden recibir existencias. La baja exige resolver stock, custodias abiertas y usuarios activos adscritos.</p>
    <p v-if="tab === 'historico'">Las áreas antiguas se conservan para interpretar los documentos. Una entrada histórica no habilita una ubicación de inventario.</p>
    <p v-if="tab === 'alias'">Las equivalencias se aplican a nuevas lecturas. Guardarlas no corrige ni confirma automáticamente los movimientos históricos; esos casos se revisan con su foto en HIL.</p>
    <p v-if="tab === 'personas'">La adscripción identifica el área de una cuenta. El acceso actual se determina por rol y permite operar en las áreas habilitadas.</p>
    <div class="herramientas">
      <label>Buscar<input v-model="busqueda" type="search" /></label>
      <button v-if="admin && tab !== 'personas'" class="btn-primary" :disabled="cargando || guardando" @click="editar()">Nuevo registro</button>
      <span v-if="!admin">Consulta de solo lectura</span>
    </div>
    <p v-if="cargando" role="status">Cargando registros…</p>
    <p class="ayuda-tabla">Desliza la tabla horizontalmente para ver todas las columnas.</p>
    <div class="tabla-contenedor" tabindex="0" aria-label="Registros de áreas y catálogos">
      <table><thead><tr><th>Nombre / lectura</th><th>Datos</th><th>Estado</th><th>Acciones</th></tr></thead>
        <tbody><tr v-for="fila in filas" :key="fila.id">
          <td>{{ fila.nombre ?? fila.nombre_oficial ?? fila.texto_sucio }}</td>
          <td v-if="tab === 'operativas'">{{ fila.codigo || 'Sin código' }}<br />
            <small>Stock: {{ fila.dependencias?.stock ?? 0 }} · custodias: {{ fila.dependencias?.custodias_abiertas ?? 0 }} · usuarios activos: {{ fila.dependencias?.usuarios_activos ?? 0 }}</small></td>
          <td v-else-if="tab === 'historico'">{{ fila.abreviatura || 'Sin sigla' }} · {{ fila.tipo === 'departamento' ? 'Área documental' : 'Operación' }}</td>
          <td v-else-if="tab === 'alias'">{{ nombreCatalogo(fila.area_oficial_id) }} · {{ fila.confirmado ? 'Equivalencia confirmada' : 'Sugerencia sin confirmar' }}</td>
          <td v-else>{{ nombreArea(fila.area_id) }}</td>
          <td>{{ fila.estado ?? (fila.activa ? 'Vigente' : 'Histórica / de baja') }}</td>
          <td><button v-if="admin" class="btn-outline btn-small" :disabled="cargando || guardando" @click="editar(fila)">{{ tab === 'personas' ? 'Cambiar adscripción' : 'Editar' }}</button>
            <button class="btn-outline btn-small" :disabled="cargandoHistorial" @click="verHistorial(fila)">Ver cambios</button></td>
        </tr><tr v-if="!cargando && !filas.length"><td colspan="4">No hay registros para esta búsqueda.</td></tr></tbody>
      </table>
    </div>
    <p v-if="cargandoHistorial" role="status">Consultando cambios…</p>
    <section v-if="historial" aria-label="Historial de cambios" class="editor">
      <h2>Cambios · {{ tituloHistorial }}</h2>
      <p v-if="!historial.length">No hay cambios administrativos registrados.</p>
      <article v-for="revision in historial" :key="revision.id">
        <p><strong>{{ revision.usuario || 'Mantenimiento autorizado' }}</strong> · {{ new Date(revision.fecha).toLocaleString('es-BO') }}</p>
        <p>{{ revision.detalle.motivo }}</p>
        <ul><li v-for="cambio in cambios(revision)" :key="cambio.campo">{{ cambio.campo }}: {{ cambio.anterior }} → {{ cambio.nuevo }}</li></ul>
      </article>
      <p v-if="historial.length === 50">Se muestran los 50 cambios más recientes.</p>
    </section>
    <div v-if="filtradas.length > 20" class="paginacion">
      <button class="btn-outline" :disabled="pagina <= 1" @click="pagina--">Anterior</button>
      <span>Página {{ pagina }} de {{ Math.ceil(filtradas.length / 20) }}</span>
      <button class="btn-outline" :disabled="pagina * 20 >= filtradas.length" @click="pagina++">Siguiente</button>
    </div>
    <form v-if="admin && abierto" class="editor" @submit.prevent="guardar">
      <h2>{{ editando ? 'Editar' : 'Crear' }} · {{ titulos[tab] }}</h2>
      <fieldset :disabled="guardando || cargando">
        <template v-if="tab === 'operativas'">
          <label>Nombre<input v-model="form.nombre" required maxlength="120" /></label>
          <label>Código<input v-model="form.codigo" maxlength="30" /></label>
          <label>Estado<select v-model="form.estado"><option value="activo">Activa</option><option value="baja">De baja</option></select></label>
        </template>
        <template v-if="tab === 'historico'">
          <label>Nombre oficial<input v-model="form.nombre_oficial" required maxlength="100" /></label>
          <label>Sigla<input v-model="form.abreviatura" maxlength="30" /></label>
          <label>Tipo<select v-model="form.tipo"><option value="departamento">Área documental</option><option value="operacion">Operación</option></select></label>
        </template>
        <label v-if="tab === 'operativas' || tab === 'historico'">Descripción<textarea v-model="form.descripcion" :maxlength="tab === 'operativas' ? 255 : 2000" /></label>
        <template v-if="tab === 'alias'">
          <label>Lectura original<input v-model="form.texto_sucio" :readonly="!!editando" required maxlength="200" /></label>
          <label>Equivalencia propuesta<select v-model="form.area_oficial_id" required><option :value="null" disabled>Seleccionar entrada documental</option>
            <option v-for="area in listas.historico" :key="area.id" :value="area.id">{{ area.nombre_oficial }}{{ area.activa ? '' : ' · histórica/inactiva' }}</option>
          </select></label>
          <label class="check"><input v-model="form.confirmado" type="checkbox" /> Equivalencia confirmada</label>
          <label v-if="form.confirmado" class="check"><input v-model="form.evidencia_revisada" type="checkbox" required /> Cotejé evidencia que respalda esta equivalencia y la identifico en el motivo.</label>
        </template>
        <label v-if="tab === 'alias' || tab === 'historico'" class="check"><input v-model="form.activa" type="checkbox" /> Vigente{{ tab === 'alias' ? ' para nuevas lecturas' : ' en el catálogo documental' }}</label>
        <template v-if="tab === 'personas'">
          <p>{{ editando?.nombre }}</p>
          <label>Área de adscripción<select v-model="form.area_id"><option :value="null">Sin adscripción</option>
            <option v-if="form.area_id && !areasActivas.some(a => a.id === form.area_id)" :value="form.area_id" disabled>{{ nombreArea(form.area_id) }} · de baja</option>
            <option v-for="area in areasActivas" :key="area.id" :value="area.id">{{ area.nombre }}</option>
          </select></label>
        </template>
        <label>Motivo y referencia de la decisión<textarea v-model="form.motivo" required minlength="10" maxlength="2000" placeholder="Qué cambia y qué documento o revisión lo respalda" /></label>
        <div class="acciones"><button type="submit" class="btn-primary" :disabled="tab === 'alias' && form.confirmado && !form.evidencia_revisada">{{ guardando ? 'Guardando…' : 'Guardar cambio' }}</button>
          <button type="button" class="btn-outline" @click="abierto = false">Cancelar</button></div>
      </fieldset>
    </form>
  </main>
</template>

<style scoped>
.catalogos { max-width: 1180px; margin: auto; padding: 1.5rem; }
header, .volver, .herramientas, .paginacion, .acciones { display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; }
header { justify-content: space-between; margin: 1.5rem 0; }
h1 { margin: 0; } p { line-height: 1.6; }
.pestanas { display: flex; flex-wrap: wrap; gap: .5rem; border-bottom: 1px solid var(--border-color); padding-bottom: .75rem; }
.pestanas button { background: white; border: 1px solid var(--border-color); border-radius: .5rem; padding: .7rem; cursor: pointer; }
.pestanas button[aria-current] { color: #294f66; border-color: #50758b; background: #eaf1f5; font-weight: 600; }
.herramientas { justify-content: space-between; margin: 1.2rem 0; }
label { display: grid; gap: .4rem; margin-bottom: .8rem; }
input, select, textarea { padding: .65rem; border: 1px solid var(--border-color); border-radius: .4rem; font: inherit; max-width: 100%; box-sizing: border-box; }
.tabla-contenedor { overflow-x: auto; } table { width: 100%; min-width: 680px; border-collapse: collapse; text-align: left; }
th, td { padding: .85rem; border-bottom: 1px solid var(--border-color); overflow-wrap: anywhere; }
small { color: var(--text-secondary); } .paginacion { margin-top: 1rem; justify-content: center; }
.editor { max-width: 760px; padding: 1.5rem; margin-top: 1.5rem; border: 1px solid var(--border-color); border-radius: .6rem; background: white; }
fieldset { padding: 0; border: 0; min-width: 0; } .check { display: flex; align-items: flex-start; gap: .6rem; }
textarea { min-height: 5rem; } .acciones { margin-top: 1rem; }
.ayuda-tabla { display: none; color: var(--text-secondary); font-size: .85rem; }
@media (max-width: 720px) { .ayuda-tabla { display: block; } }
</style>
