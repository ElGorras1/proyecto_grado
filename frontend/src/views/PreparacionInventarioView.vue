<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, nextTick } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
interface Articulo {
  articulo_id: number; articulo: string; codigo: string; apertura: boolean; origen: string | null
  indicio_prueba: boolean
  saldo_operativo: number | null; saldo_documental: number | null; motivo_bloqueo: string | null
  sin_ubicacion: number | null; en_areas: number | null; en_custodia: number | null
  integridad: boolean | null; conciliacion_registrada: boolean; conteo_aprobado: boolean
  referencia_base: string | null; fecha_base: string | null; registros_posteriores: number
  fuente_cierre: string | null; pendientes: string[]; acciones: string[]
}
interface Preparacion {
  generado_en: string; gestion: number; periodo_abierto: boolean; alcance: string
  resumen: { articulos: number; aperturas: number; conciliaciones: number; unidades_sin_ubicacion: number
    articulos_con_unidades_sin_ubicacion: number; bases_bloqueadas: number; fuentes_sin_confirmar: number; pendientes_por_tipo: Record<string, number>
    unidades_sin_ubicacion_con_indicio_prueba: number; unidades_sin_ubicacion_sin_indicio_prueba: number }
  areas_activas: { id: number; nombre: string }[]; transferencias_entre_areas_disponibles: boolean
  articulos: Articulo[]
}
const auth = useAuthStore()
const datos = ref<Preparacion | null>(null), cargando = ref(false), error = ref('')
const busqueda = ref(''), soloAperturas = ref(true), filtro = ref(''), pagina = ref(1)
const seleccionado = ref<number | null>(null)
const etiquetas: Record<string, string> = { INTEGRIDAD_PENDIENTE: 'Revisar integridad', UBICACION_PENDIENTE: 'Ubicación pendiente',
  CONTEO_POSTERIOR: 'Conteo posterior y ajuste', CONCILIACION_INICIAL: 'Conciliación inicial pendiente',
  BASE_BLOQUEADA: 'Base documental bloqueada', SIN_BASE: 'Sin base', CONTEO_INICIAL: 'Conteo inicial pendiente',
  FUENTE_DOCUMENTAL_PENDIENTE: 'Fuente histórica sin confirmar' }
etiquetas.REVISAR_REGISTRO_PRUEBA = 'Revisar posible registro de prueba'
const filtrados = computed(() => (datos.value?.articulos ?? []).filter(a =>
  (!soloAperturas.value || a.apertura) && (!filtro.value || a.pendientes.includes(filtro.value)) &&
  [a.articulo, a.codigo, String(a.articulo_id)].join(' ').toLocaleLowerCase().includes(busqueda.value.trim().toLocaleLowerCase())))
const visibles = computed(() => filtrados.value.slice((pagina.value - 1) * 20, pagina.value * 20))
const ficha = computed(() => datos.value?.articulos.find(a => a.articulo_id === seleccionado.value))
let consulta = 0
onUnmounted(() => { consulta++ })
async function cargar() {
  const turno = ++consulta
  cargando.value = true; error.value = ''
  try {
    const r = await api.get('/inventario/preparacion')
    if (turno === consulta) { datos.value = r.data; pagina.value = 1 }
  } catch { if (turno === consulta) error.value = 'No se pudo cargar la preparación del inventario. Puedes volver a intentar.' }
  finally { if (turno === consulta) cargando.value = false }
}
function cambiarFiltro() { pagina.value = 1 }
function cantidad(n: number | null) { return n === null ? 'Sin base operativa' : n + ' u.' }
async function prepararFicha(id: number) {
  seleccionado.value = id
  await nextTick()
  document.getElementById('ficha-conteo')?.scrollIntoView?.({ block: 'start', behavior: 'smooth' })
}
function imprimir() { window.print() }
onMounted(cargar)
</script>

<template>
  <main class="preparacion">
    <div class="no-imprimir">
      <nav><router-link :to="{ name: 'dashboard' }">← Inicio</router-link>
        <router-link v-if="auth.rol !== 'Operador'" :to="{ name: 'areasCatalogos' }">Áreas y catálogos</router-link>
      </nav>
      <header><div><h1>Preparación del inventario</h1><p>Prioridades para cotejar, contar y ubicar existencias.</p></div>
        <button class="btn-outline" :disabled="cargando" @click="cargar">Actualizar</button>
      </header>
      <p v-if="cargando" role="status">Consultando saldos y pendientes…</p>
      <p v-if="error" role="alert" class="alert alert-error">{{ error }}</p>
      <template v-if="datos">
        <p>{{ datos.alcance }}</p>
        <div class="resumen">
          <div><strong>{{ datos.resumen.aperturas }}</strong><span>Aperturas registradas</span></div>
          <div><strong>{{ datos.resumen.unidades_sin_ubicacion }}</strong><span>Unidades sin ubicación confirmada</span></div>
          <div><strong>{{ datos.resumen.conciliaciones }}</strong><span>Conciliaciones registradas</span></div>
          <div><strong>{{ datos.areas_activas.length }}</strong><span>Áreas activas</span></div>
        </div>
        <p v-if="!datos.periodo_abierto" role="status" class="alert alert-warning">La gestión está cerrada. Las operaciones requieren reapertura autorizada.</p>
        <p v-if="datos.resumen.unidades_sin_ubicacion_con_indicio_prueba" class="aviso">
          De las {{ datos.resumen.unidades_sin_ubicacion }} unidades sin ubicación,
          {{ datos.resumen.unidades_sin_ubicacion_con_indicio_prueba }} pertenecen a registros con indicios de prueba y
          {{ datos.resumen.unidades_sin_ubicacion_sin_indicio_prueba }} a otros registros.
          Cotejar los casos marcados antes de incluir sus cantidades en el inventario institucional.
        </p>
        <p v-if="!datos.transferencias_entre_areas_disponibles" class="aviso">Para transferir entre áreas se necesitan al menos dos ubicaciones operativas activas.</p>
        <p>Archivo histórico: {{ datos.resumen.fuentes_sin_confirmar }} fuentes sin confirmar y {{ datos.resumen.bases_bloqueadas }} bases con bloqueo. El cotejo documental se realiza en Cobertura.</p>
        <div class="filtros">
          <label>Buscar artículo<input v-model="busqueda" type="search" @input="cambiarFiltro" /></label>
          <label>Pendiente<select v-model="filtro" @change="cambiarFiltro"><option value="">Todos</option>
            <option v-for="(texto, codigo) in etiquetas" :key="codigo" :value="codigo">{{ texto }}</option>
          </select></label>
          <label class="check"><input v-model="soloAperturas" type="checkbox" @change="cambiarFiltro" /> Solo artículos con apertura</label>
        </div>
        <p>{{ filtrados.length }} de {{ datos.resumen.articulos }} artículos.</p>
        <p class="ayuda-tabla">Desliza la tabla horizontalmente para consultar todas las columnas.</p>
        <div class="tabla-scroll" tabindex="0" aria-label="Artículos y preparación">
          <table><thead><tr><th>Artículo</th><th>Saldo operativo</th><th>Distribución registrada</th><th>Pendientes</th><th>Preparar revisión</th></tr></thead>
            <tbody><tr v-for="a in visibles" :key="a.articulo_id">
              <td><strong>{{ a.articulo }}</strong><br /><small>{{ a.codigo }} · #{{ a.articulo_id }}</small></td>
              <td>{{ cantidad(a.saldo_operativo) }}<br /><small v-if="!a.apertura && a.saldo_documental !== null">Documento histórico: {{ a.saldo_documental }} u.</small></td>
              <td v-if="a.apertura">En áreas: {{ a.en_areas }} · externa: {{ a.en_custodia }}<br />Sin ubicación: {{ a.sin_ubicacion }}</td><td v-else>Sin distribución operativa</td>
              <td><span v-for="pendiente in a.pendientes" :key="pendiente" class="marca">{{ etiquetas[pendiente] }}</span><span v-if="!a.pendientes.length">Sin pendientes de este listado</span></td>
              <td><router-link :to="{ path: '/inventario-vivo', query: { articulo_id: a.articulo_id } }">Abrir artículo</router-link>
                <button class="btn-outline btn-small" @click="prepararFicha(a.articulo_id)">Preparar ficha</button></td>
            </tr><tr v-if="!visibles.length"><td colspan="5">No hay artículos para estos filtros.</td></tr></tbody>
          </table>
        </div>
        <div v-if="filtrados.length > 20" class="paginacion"><button class="btn-outline" :disabled="pagina <= 1" @click="pagina--">Anterior</button>
          <span>Página {{ pagina }} de {{ Math.ceil(filtrados.length / 20) }}</span>
          <button class="btn-outline" :disabled="pagina * 20 >= filtrados.length" @click="pagina++">Siguiente</button></div>
      </template>
    </div>
    <section v-if="ficha && datos" id="ficha-conteo" class="ficha" aria-label="Ficha de cotejo">
      <h2>Ficha para cotejo y conteo físico</h2>
      <p><strong>{{ ficha.articulo }}</strong> · {{ ficha.codigo }} · artículo #{{ ficha.articulo_id }}</p>
      <p>Preparada con registros del {{ new Date(datos.generado_en).toLocaleString('es-BO', { timeZone: 'America/La_Paz' }) }}.</p>
      <p>Saldo operativo registrado: <strong>{{ cantidad(ficha.saldo_operativo) }}</strong><span v-if="ficha.saldo_documental !== null"> · saldo documental: {{ ficha.saldo_documental }} u.</span></p>
      <p v-if="ficha.apertura">Sin ubicación confirmada: {{ ficha.sin_ubicacion }} u. · En áreas: {{ ficha.en_areas }} u. · En custodia externa: {{ ficha.en_custodia }} u.</p>
      <p v-if="ficha.referencia_base">Referencia de la base: {{ ficha.referencia_base }}</p>
      <p v-if="ficha.indicio_prueba" class="aviso">Revisar la condición del registro: su nombre contiene una marca de prueba. Esta detección no elimina ni excluye cantidades automáticamente.</p>
      <p v-if="ficha.motivo_bloqueo">{{ ficha.motivo_bloqueo }}</p>
      <h3>Acciones para este artículo</h3><ul><li v-for="accion in ficha.acciones" :key="accion">{{ accion }}</li></ul>
      <h3>Completar durante el cotejo</h3>
      <p>Fecha y hora del conteo: ____________________________________</p>
      <p>Persona que cuenta: _______________________________________</p>
      <p>Persona que verifica: ______________________________________</p>
      <p>Documento / acta de respaldo: ________________________________</p>
      <table class="conteo"><thead><tr><th>Ubicación observada</th><th>Cantidad contada</th><th>Observación / respaldo</th></tr></thead>
        <tbody><tr v-for="area in datos.areas_activas" :key="area.id"><td>{{ area.nombre }}</td><td>________________</td><td>______________________</td></tr>
          <tr><td>Otra ubicación: __________________</td><td>________________</td><td>______________________</td></tr>
          <tr><td>Custodia externa cotejada</td><td>________________</td><td>______________________</td></tr>
        </tbody>
      </table>
      <p>Total físico cotejado: __________ · Diferencia documentada: __________</p>
      <p>Decisión y observaciones: __________________________________________________</p>
      <p>______________________________________________________________________</p>
      <p>Firmas de quien cuenta y verifica: ___________________________________________</p>
      <p class="nota">Esta ficha preparada no confirma un conteo. Registrar después la decisión y su referencia mediante apertura, conciliación, ubicación o ajuste autorizado según corresponda.</p>
      <div class="no-imprimir acciones"><button class="btn-primary" @click="imprimir">Imprimir ficha</button>
        <router-link :to="{ path: '/inventario-vivo', query: { articulo_id: ficha.articulo_id } }">Abrir artículo en inventario</router-link>
        <router-link :to="{ path: '/kardex-digital', query: { articulo_id: ficha.articulo_id } }">Revisar documentos históricos</router-link>
      </div>
    </section>
  </main>
</template>

<style scoped>
.preparacion { max-width: 1200px; margin: auto; padding: 1.5rem; }
nav, header, .filtros, .acciones, .paginacion { display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; }
header { margin: 1.5rem 0; justify-content: space-between; } h1 { margin: 0; }
p, li { line-height: 1.6; } small, .nota { color: var(--text-secondary); }
.resumen { display: grid; grid-template-columns: repeat(auto-fit,minmax(180px,1fr)); gap: 1rem; margin: 1.5rem 0; }
.resumen div { padding: 1rem; border: 1px solid var(--border-color); border-radius: .5rem; background: white; }
.resumen strong, .resumen span { display: block; } .resumen strong { font-size: 1.7rem; }
.aviso { padding: .8rem; background: #fff4dc; border-radius: .4rem; }
label { display: grid; gap: .4rem; } input, select { padding: .6rem; font: inherit; border: 1px solid var(--border-color); border-radius: .4rem; }
.check { display: flex; align-items: center; gap: .5rem; }
.tabla-scroll { overflow-x: auto; } table { width: 100%; border-collapse: collapse; text-align: left; }
.tabla-scroll table { min-width: 860px; } th, td { padding: .8rem; border: 1px solid var(--border-color); }
.marca { display: block; font-size: .84rem; padding: .25rem; }
.paginacion { justify-content: center; margin: 1rem; } .ayuda-tabla { display: none; }
.ficha { background: white; border: 1px solid var(--border-color); padding: 1.5rem; margin-top: 2rem; border-radius: .5rem; overflow-wrap: anywhere; }
.conteo { font-size: .9rem; } .nota { font-size: .85rem; }
@media (max-width: 720px) { .ayuda-tabla { display: block; } .ficha { padding: .8rem; } .conteo { display: block; overflow-x: auto; } }
@media print {
  .no-imprimir { display: none !important; } .preparacion { max-width: none; padding: 0; }
  .ficha { border: 0; margin: 0; padding: 0; font-size: 10pt; } h2 { font-size: 15pt; }
  .conteo { display: table; overflow: visible; } th, td { border: 1px solid #555; padding: .4rem; }
  .nota { color: #333; } p, li { line-height: 1.35; }
}
</style>
