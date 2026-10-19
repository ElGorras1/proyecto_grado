<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'

type Origen = 'todos' | 'historico' | 'moderno'
type Direccion = 'todas' | 'ingreso' | 'salida'
type Revision = 'todas' | 'pendiente' | 'sin_alertas'
interface Filtros {
  gestion: number
  mes: number | ''
  articulo: string
  origen: Origen
  direccion: Direccion
  nodo: string
  revision: Revision
}
interface Fila {
  id: number
  fecha: string
  fecha_original: string | null
  fecha_estado: string
  origen_fecha?: string
  origen_saldo?: string
  tipos_alerta: string[]
  articulo: string
  codigo: string
  origen: string
  lote_id: number | null
  pagina: number | null
  orden_fila: number | null
  detalle: string
  referencia: string | null
  area_original: string | null
  nodo: string | null
  tipo_operacion: string | null
  ingresos: number
  salidas: number
  pendiente_hil: boolean
}
interface Reporte {
  gestion: number
  resumen: {
    movimientos: number
    articulos: number
    ingresos: number
    salidas: number
    pendientes_hil: number
    historicos: number
    modernos: number
  }
  mensual: { mes: number; movimientos: number; ingresos: number; salidas: number }[]
  pagina: number
  limite: number
  filas: Fila[]
}

const nombresMes = [
  'Ene',
  'Feb',
  'Mar',
  'Abr',
  'May',
  'Jun',
  'Jul',
  'Ago',
  'Sep',
  'Oct',
  'Nov',
  'Dic',
]
const route = useRoute()
const gestionEnlace = Number(route.query.gestion)
const gestionSolicitada =
  Number.isInteger(gestionEnlace) && gestionEnlace >= 1900 && gestionEnlace <= 9998
    ? gestionEnlace
    : null
const origenSolicitado =
  route.query.origen === 'historico' || route.query.origen === 'moderno'
    ? route.query.origen
    : 'todos'
const gestiones = ref<number[]>([])
const nodos = ref<string[]>([])
const filtros = ref<Filtros>({
  gestion: gestionSolicitada ?? new Date().getFullYear(),
  mes: '',
  articulo: '',
  origen: origenSolicitado,
  direccion: 'todas',
  nodo: '',
  revision: 'todas',
})
const aplicados = ref<Filtros | null>(null)
const reporte = ref<Reporte | null>(null)
const cargando = ref(false)
const exportando = ref(false)
const error = ref('')
const maximoMensual = computed(() =>
  Math.max(1, ...(reporte.value?.mensual.map((m) => Math.max(m.ingresos, m.salidas)) ?? [])),
)
const totalPaginas = computed(() =>
  reporte.value ? Math.ceil(reporte.value.resumen.movimientos / reporte.value.limite) : 0,
)

function parametros(f: Filtros): Record<string, string | number> {
  const p: Record<string, string | number> = {
    gestion: f.gestion,
    origen: f.origen,
    direccion: f.direccion,
    revision: f.revision,
  }
  if (f.mes) p.mes = f.mes
  if (f.articulo.trim()) p.articulo = f.articulo.trim()
  if (f.nodo) p.nodo = f.nodo
  return p
}

async function cargarReporte(pagina = 1, nuevosFiltros = false) {
  if (cargando.value) return
  const seleccion = nuevosFiltros || !aplicados.value ? { ...filtros.value } : aplicados.value
  cargando.value = true
  error.value = ''
  try {
    const { data } = await api.get<Reporte>('/reportes/inventario', {
      params: { ...parametros(seleccion), pagina, limite: 50 },
    })
    reporte.value = data
    aplicados.value = seleccion
  } catch {
    error.value = 'No se pudo generar el reporte. Revisa la conexión e inténtalo de nuevo.'
  } finally {
    cargando.value = false
  }
}

async function descargarCsv() {
  if (!aplicados.value || exportando.value) return
  exportando.value = true
  error.value = ''
  try {
    const { data } = await api.get('/reportes/inventario.csv', {
      params: parametros(aplicados.value),
      responseType: 'blob',
    })
    const url = URL.createObjectURL(new Blob([data], { type: 'text/csv;charset=utf-8' }))
    const enlace = document.createElement('a')
    enlace.href = url
    enlace.download = `reporte_inventario_${aplicados.value.gestion}.csv`
    document.body.appendChild(enlace)
    enlace.click()
    enlace.remove()
    URL.revokeObjectURL(url)
  } catch {
    error.value = 'No se pudo descargar el CSV. Vuelve a intentarlo.'
  } finally {
    exportando.value = false
  }
}

onMounted(async () => {
  try {
    const { data } = await api.get<{ gestiones: number[]; nodos: string[] }>(
      '/reportes/inventario/opciones',
    )
    gestiones.value = data.gestiones
    nodos.value = data.nodos
    if (gestionSolicitada !== null) {
      if (!gestiones.value.includes(gestionSolicitada))
        gestiones.value = [...gestiones.value, gestionSolicitada].sort((a, b) => b - a)
    } else if (gestiones.value.length) filtros.value.gestion = gestiones.value[0]
    await cargarReporte(1, true)
  } catch {
    error.value = 'No se pudieron cargar las gestiones disponibles.'
  }
})

const numero = (n: number) => new Intl.NumberFormat('es-BO').format(n)
</script>

<template>
  <main class="reporte-view">
    <header class="encabezado">
      <div>
        <router-link to="/" class="volver">← Panel principal</router-link>
        <h1>Reportes de inventario por gestión</h1>
        <p>Consulta los movimientos registrados en cada año y descarga el detalle filtrado.</p>
      </div>
      <button class="exportar" :disabled="!reporte || exportando" @click="descargarCsv">
        {{ exportando ? 'Preparando CSV…' : '↓ Descargar CSV' }}
      </button>
      <router-link
        :to="{ name: 'analitica', query: { gestion: aplicados?.gestion ?? filtros.gestion } }"
        >Analizar esta gestión</router-link
      >
    </header>

    <form class="filtros" @submit.prevent="cargarReporte(1, true)">
      <label
        >Gestión
        <select v-model.number="filtros.gestion" required aria-label="Gestión">
          <option v-for="g in gestiones" :key="g" :value="g">{{ g }}</option>
          <option v-if="!gestiones.length" :value="filtros.gestion">{{ filtros.gestion }}</option>
        </select>
      </label>
      <label
        >Mes
        <select v-model="filtros.mes">
          <option value="">Todo el año</option>
          <option v-for="(nombre, index) in nombresMes" :key="index" :value="index + 1">
            {{ nombre }}
          </option>
        </select>
      </label>
      <label
        >Artículo o código
        <input
          v-model="filtros.articulo"
          type="search"
          placeholder="Buscar artículo…"
          maxlength="150"
        />
      </label>
      <label
        >Origen
        <select v-model="filtros.origen" aria-label="Origen">
          <option value="todos">Histórico y moderno</option>
          <option value="historico">Kárdex escaneado</option>
          <option value="moderno">Operaciones modernas</option>
        </select>
      </label>
      <label
        >Dirección
        <select v-model="filtros.direccion">
          <option value="todas">Ingresos y salidas</option>
          <option value="ingreso">Solo ingresos</option>
          <option value="salida">Solo salidas</option>
        </select>
      </label>
      <label
        >Nodo / destino
        <select v-model="filtros.nodo">
          <option value="">Todos los nodos</option>
          <option v-for="n in nodos" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label
        >Revisión
        <select v-model="filtros.revision">
          <option value="todas">Todos</option>
          <option value="pendiente">Pendientes HIL</option>
          <option value="sin_alertas">Sin alertas HIL</option>
        </select>
      </label>
      <button type="submit" class="consultar" :disabled="cargando">
        {{ cargando ? 'Consultando…' : 'Aplicar filtros' }}
      </button>
    </form>

    <p class="nota">
      La gestión se determina por la <strong>fecha de consulta del movimiento</strong>: inicialmente
      es la escrita en el Kárdex, y puede corregirse con evidencia conservando la fecha original.
      Este reporte suma movimientos; no representa existencias al cierre de año. Las fechas
      pendientes de HIL se identifican en el detalle.
    </p>
    <p v-if="error" role="alert" class="error">{{ error }}</p>

    <template v-if="reporte">
      <section class="metricas" aria-label="Resumen del reporte">
        <div>
          <span>Movimientos</span><strong>{{ numero(reporte.resumen.movimientos) }}</strong
          ><small
            >{{ numero(reporte.resumen.historicos) }} históricos ·
            {{ numero(reporte.resumen.modernos) }} modernos</small
          >
        </div>
        <div>
          <span>Artículos</span><strong>{{ numero(reporte.resumen.articulos) }}</strong
          ><small>Con movimientos en el filtro</small>
        </div>
        <div>
          <span>Ingresos</span><strong class="verde">+{{ numero(reporte.resumen.ingresos) }}</strong
          ><small>Unidades registradas</small>
        </div>
        <div>
          <span>Salidas</span><strong class="ambar">−{{ numero(reporte.resumen.salidas) }}</strong
          ><small>Unidades registradas</small>
        </div>
        <div>
          <span>Pendientes HIL</span
          ><strong class="rojo">{{ numero(reporte.resumen.pendientes_hil) }}</strong
          ><small>Filas que requieren revisión</small>
        </div>
      </section>

      <section class="panel" aria-label="Distribución mensual">
        <div class="panel-titulo">
          <h2>Movimiento mensual · {{ reporte.gestion }}</h2>
          <span
            ><i class="leyenda ingreso"></i> Ingresos <i class="leyenda salida"></i> Salidas</span
          >
        </div>
        <div class="grafico-mensual">
          <div
            v-for="m in reporte.mensual"
            :key="m.mes"
            class="mes"
            :title="`${nombresMes[m.mes - 1]}: ${numero(m.ingresos)} ingresos, ${numero(m.salidas)} salidas`"
          >
            <div class="barras">
              <div
                class="barra ingreso"
                :style="{ height: `${(100 * m.ingresos) / maximoMensual}%` }"
              ></div>
              <div
                class="barra salida"
                :style="{ height: `${(100 * m.salidas) / maximoMensual}%` }"
              ></div>
            </div>
            <span>{{ nombresMes[m.mes - 1] }}</span>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="panel-titulo">
          <h2>Detalle de movimientos</h2>
          <span>{{ numero(reporte.resumen.movimientos) }} resultados · 50 por página</span>
        </div>
        <div v-if="!reporte.filas.length" class="vacio">
          No hay movimientos para los filtros aplicados.
        </div>
        <div v-else class="tabla-wrap">
          <table>
            <thead>
              <tr>
                <th>Fecha registrada</th>
                <th>Artículo</th>
                <th>Origen</th>
                <th>Detalle / ubicación</th>
                <th>Ingreso</th>
                <th>Salida</th>
                <th>Revisión</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="fila in reporte.filas" :key="fila.id">
                <td class="sin-salto">
                  {{ fila.fecha
                  }}<small v-if="fila.fecha_estado === 'ESTIMADA_HIL'">Fecha estimada · {{ fila.origen_fecha }}</small><small v-else-if="fila.fecha_estado === 'PENDIENTE_HIL'">Fecha pendiente HIL</small
                  ><small v-else-if="fila.fecha_estado === 'CONFIRMADA_DOCUMENTO'"
                    >Confirmada en documento</small
                  ><small v-if="fila.fecha_original && fila.fecha_original !== fila.fecha"
                    >Original: {{ fila.fecha_original }}</small
                  >
                </td>
                <td>
                  <strong>{{ fila.articulo }}</strong
                  ><small>{{ fila.codigo }}</small>
                </td>
                <td>
                  <span class="etiqueta">{{ fila.origen }}</span
                  ><small v-if="fila.lote_id"
                    >Lote {{ fila.lote_id }} · pág. {{ fila.pagina ?? '?' }} · fila
                    {{ fila.orden_fila ?? '?' }}</small
                  >
                </td>
                <td>
                  <strong>{{ fila.tipo_operacion || fila.detalle }}</strong
                  ><small
                    >Nodo: {{ fila.nodo || 'No registrado'
                    }}<template v-if="fila.referencia">
                      · Ref.: {{ fila.referencia }}</template
                    ></small
                  >
                </td>
                <td class="numero verde">
                  {{ fila.ingresos ? `+${numero(fila.ingresos)}` : '—' }}
                </td>
                <td class="numero ambar">{{ fila.salidas ? `−${numero(fila.salidas)}` : '—' }}</td>
                <td>
                  <span :class="fila.pendiente_hil ? 'estado pendiente' : 'estado limpio'">{{
                    fila.pendiente_hil ? 'Pendiente HIL' : 'Sin alertas'
                  }}</span
                  ><small v-if="fila.pendiente_hil">{{ fila.tipos_alerta?.join(', ') }}</small>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="totalPaginas > 1" class="paginacion">
          <button
            :disabled="cargando || reporte.pagina <= 1"
            @click="cargarReporte(reporte.pagina - 1)"
          >
            Anterior
          </button>
          <span>Página {{ reporte.pagina }} de {{ totalPaginas }}</span>
          <button
            :disabled="cargando || reporte.pagina >= totalPaginas"
            @click="cargarReporte(reporte.pagina + 1)"
          >
            Siguiente
          </button>
        </div>
      </section>
    </template>
  </main>
</template>

<style scoped>
.reporte-view {
  max-width: 1440px;
  margin: 0 auto;
  padding: 2rem;
  color: #203047;
}
.encabezado {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: end;
  margin-bottom: 1.5rem;
}
.encabezado h1 {
  margin: 0.6rem 0 0.25rem;
  font-size: clamp(1.5rem, 3vw, 2.2rem);
}
.encabezado p,
.panel-titulo span {
  color: #64748b;
  margin: 0;
}
.volver {
  color: #235e86;
  text-decoration: none;
  font-weight: 600;
}
.filtros {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 0.9rem;
  padding: 1.2rem;
  border: 1px solid #dbe3ed;
  border-radius: 14px;
  background: white;
  box-shadow: 0 6px 25px #213f5d0b;
}
.filtros label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.82rem;
  font-weight: 650;
}
.filtros input,
.filtros select {
  width: 100%;
  min-width: 0;
  padding: 0.65rem 0.7rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  color: #203047;
  font: inherit;
}
button {
  cursor: pointer;
  font: inherit;
}
button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}
.consultar,
.exportar {
  border: 0;
  border-radius: 8px;
  padding: 0.7rem 1rem;
  font-weight: 700;
}
.consultar {
  align-self: end;
  background: #17587c;
  color: white;
}
.exportar {
  background: #e6f3ee;
  color: #17644a;
  white-space: nowrap;
}
.nota {
  margin: 1rem 0 1.4rem;
  padding: 0.85rem 1rem;
  border-left: 4px solid #d39c34;
  background: #fff8e9;
  color: #70511c;
  font-size: 0.9rem;
}
.error {
  color: #9f2424;
  background: #fff0f0;
  padding: 0.8rem;
  border-radius: 8px;
}
.metricas {
  display: grid;
  grid-template-columns: repeat(5, minmax(145px, 1fr));
  gap: 0.9rem;
  margin: 1.4rem 0;
}
.metricas > div {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 1rem;
  border: 1px solid #dbe3ed;
  border-radius: 12px;
  background: white;
}
.metricas span {
  color: #617187;
  font-size: 0.86rem;
}
.metricas strong {
  font-size: 1.8rem;
  line-height: 1.2;
}
.metricas small,
td small {
  color: #64748b;
  font-size: 0.78rem;
}
.verde {
  color: #138064;
}
.ambar {
  color: #b16718;
}
.rojo {
  color: #b24242;
}
.panel {
  margin: 1.2rem 0;
  border: 1px solid #dbe3ed;
  border-radius: 14px;
  background: white;
  overflow: hidden;
}
.panel-titulo {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 1rem 1.2rem;
  border-bottom: 1px solid #e8edf3;
}
.panel h2 {
  margin: 0;
  font-size: 1.05rem;
}
.leyenda {
  display: inline-block;
  width: 0.65rem;
  height: 0.65rem;
  border-radius: 2px;
  margin-left: 0.8rem;
}
.grafico-mensual {
  display: grid;
  grid-template-columns: repeat(12, minmax(35px, 1fr));
  height: 220px;
  gap: 0.5rem;
  padding: 1rem;
}
.mes {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  color: #64748b;
}
.barras {
  flex: 1;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: end;
  gap: 3px;
  border-bottom: 1px solid #dbe3ed;
}
.barra {
  width: 40%;
  max-width: 26px;
  min-height: 0;
  border-radius: 4px 4px 0 0;
}
.ingreso {
  background: #2d9e7d;
}
.salida {
  background: #e3a348;
}
.tabla-wrap {
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}
th,
td {
  padding: 0.85rem 0.75rem;
  border-bottom: 1px solid #edf0f4;
  text-align: left;
  vertical-align: top;
}
th {
  color: #526176;
  background: #f8fafc;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
td strong,
td small {
  display: block;
}
td strong {
  font-weight: 600;
}
td small {
  margin-top: 0.25rem;
}
.sin-salto,
.numero {
  white-space: nowrap;
}
.numero {
  text-align: right;
  font-weight: 700;
}
.etiqueta,
.estado {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 6px;
  white-space: nowrap;
  font-size: 0.75rem;
  font-weight: 700;
}
.etiqueta {
  background: #eaf0f8;
  color: #415879;
}
.pendiente {
  background: #fff0df;
  color: #995314;
}
.limpio {
  background: #e7f5ed;
  color: #247054;
}
.vacio {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}
.paginacion {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
}
.paginacion button {
  border: 1px solid #cbd5e1;
  border-radius: 7px;
  padding: 0.4rem 0.8rem;
  background: white;
}
@media (max-width: 850px) {
  .metricas {
    grid-template-columns: repeat(2, 1fr);
  }
  .encabezado {
    align-items: start;
    flex-direction: column;
  }
  .grafico-mensual {
    gap: 0.15rem;
    padding: 0.8rem 0.4rem;
  }
}
@media print {
  .filtros,
  .exportar,
  .paginacion,
  .volver {
    display: none;
  }
  .reporte-view {
    padding: 0;
  }
}
</style>
