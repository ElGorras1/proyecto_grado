<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { isAxiosError } from 'axios'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
interface Modelo {
  id: string
  estado: string
  activo: boolean
  creado_en: string
  umbral: number | null
  error: string | null
  metricas: { entrenamiento: number; calibracion: number; advertencia: string } | null
}
interface Perfil {
  total: number
  minimo: number
  minimo_dias: number
  faltantes: number
  suficientes: boolean
  motivo_insuficiencia: string | null
  controles_deterministicos_activos: boolean
  modelo_disponible: boolean
  modelo_activo: Modelo | null
  advertencia: string
}
interface Resultado {
  id: number
  modelo_id: string
  recurso: string
  articulo: string
  score: number
  alerta: boolean
  snapshot: { cantidad: number; tipo: string; registrado_en: string }
  contexto: { referencias: number; mediana: number; hora_local: number; demora_horas: number }
}
const auth = useAuthStore()
const administrador = computed(() => auth.rol === 'Administrador')
const perfil = ref<Perfil | null>(null),
  modelos = ref<Modelo[]>([]),
  resultados = ref<Resultado[]>([])
const pagina = ref(1),
  paginaModelos = ref(1),
  total = ref(0),
  totalModelos = ref(0)
const filtros = ref({ gestion: '' as number | '', articulo_id: '', alertas: true })
const aplicados = ref({ ...filtros.value })
const filtrosPendientes = computed(
  () => JSON.stringify(filtros.value) !== JSON.stringify(aplicados.value),
)
const catalogo = ref<{ id: number; nombre: string }[]>([])
const errorCatalogo = ref('')
const ocupado = ref(false),
  error = ref(''),
  motivo = ref('')
let solicitud = 0
onUnmounted(() => {
  solicitud++
})
function fecha(v: string) {
  return new Date(v).toLocaleString('es-BO', { timeZone: 'America/La_Paz' })
}
function fallo(e: unknown) {
  const d = isAxiosError(e) ? e.response?.data?.detail : null
  error.value =
    typeof d === 'string' ? d : 'No se pudo completar la operación. Actualiza y revisa el estado.'
}
async function cargar(p = 1) {
  const n = ++solicitud
  ocupado.value = true
  error.value = ''
  try {
    const [a, b, c] = await Promise.all([
      api.get<Perfil>('/analitica-operativa/perfil'),
      api.get('/analitica-operativa/modelos', { params: { pagina: paginaModelos.value } }),
      api.get('/analitica-operativa/resultados', {
        params: {
          pagina: p,
          alertas: aplicados.value.alertas,
          gestion: aplicados.value.gestion || undefined,
          articulo_id: aplicados.value.articulo_id || undefined,
        },
      }),
    ])
    if (n !== solicitud) return
    perfil.value = a.data
    modelos.value = b.data.filas
    totalModelos.value = b.data.total
    resultados.value = c.data.filas
    total.value = c.data.total
    pagina.value = p
  } catch (e) {
    if (n === solicitud) {
      resultados.value = []
      total.value = 0
      fallo(e)
    }
  } finally {
    if (n === solicitud) ocupado.value = false
  }
}
async function aplicarFiltros() {
  if (ocupado.value) return
  aplicados.value = { ...filtros.value }
  await cargar()
}
async function limpiarFiltros() {
  if (ocupado.value) return
  filtros.value = { gestion: '', articulo_id: '', alertas: true }
  await aplicarFiltros()
}
async function entrenar() {
  if (ocupado.value) return
  ocupado.value = true
  error.value = ''
  try {
    await api.post('/analitica-operativa/entrenar', {})
    paginaModelos.value = 1
    await cargar()
  } catch (e) {
    fallo(e)
  } finally {
    ocupado.value = false
  }
}
async function cambiar(m: Modelo) {
  if (ocupado.value || motivo.value.trim().length < 10) return
  ocupado.value = true
  error.value = ''
  try {
    await api.post(`/analitica-operativa/modelos/${m.id}/${m.activo ? 'desactivar' : 'activar'}`, {
      motivo: motivo.value,
    })
    motivo.value = ''
    await cargar()
  } catch (e) {
    fallo(e)
  } finally {
    ocupado.value = false
  }
}
async function paginarModelos(d: number) {
  paginaModelos.value += d
  await cargar(pagina.value)
}
onMounted(() => {
  void cargar()
  void api
    .get('/kardex/articulos')
    .then(({ data }) => {
      catalogo.value = data
    })
    .catch(() => {
      errorCatalogo.value =
        'No se pudo cargar el catálogo de artículos. Recarga esta página para usar ese filtro.'
    })
})
</script>

<template>
  <main class="operativa">
    <router-link to="/">← Inicio</router-link>
    <header>
      <div>
        <p>INVENTARIO ACTUAL</p>
        <h1>Analítica de operaciones digitales</h1>
      </div>
      <button :disabled="ocupado" @click="cargar()">Actualizar</button>
    </header>
    <p v-if="error" role="alert" class="error">{{ error }}</p>
    <p v-if="errorCatalogo" role="alert" class="error">{{ errorCatalogo }}</p>
    <section v-if="perfil" class="panel">
      <h2>Datos y controles disponibles</h2>
      <p>
        <strong>{{ perfil.total }}</strong> operaciones elegibles · mínimo
        {{ perfil.minimo }} registros de al menos {{ perfil.minimo_dias }} días.
      </p>
      <p v-if="perfil.controles_deterministicos_activos">
        Los controles inmediatos de stock, cantidad, horario y repetición están activos.
      </p>
      <p v-if="!perfil.suficientes" class="nota">
        {{ perfil.motivo_insuficiencia }} Faltan {{ perfil.faltantes }} registros para el mínimo
        técnico.
      </p>
      <p v-if="perfil.modelo_activo && !perfil.modelo_disponible" role="alert" class="error">
        El modelo activo no está disponible. Los controles inmediatos siguen funcionando; revisa el
        respaldo del modelo.
      </p>
      <p v-else-if="perfil.modelo_disponible">
        Modelo provisional activo: {{ perfil.modelo_activo?.id.slice(0, 8) }}. Sus avisos se revisan
        en la bandeja.
      </p>
      <p v-else>Actualmente no hay un modelo operativo activo.</p>
      <p>{{ perfil.advertencia }}</p>
      <button v-if="administrador" :disabled="ocupado || !perfil.suficientes" @click="entrenar">
        Preparar nueva versión
      </button>
    </section>
    <section class="panel">
      <h2>Versiones operativas</h2>
      <p v-if="!modelos.length">
        Todavía no hay versiones. Las operaciones se registran con los controles inmediatos.
      </p>
      <label v-if="administrador && modelos.length"
        >Motivo para activar o desactivar<textarea
          v-model="motivo"
          minlength="10"
          maxlength="2000"
        />
      </label>
      <article v-for="m in modelos" :key="m.id">
        <h3>{{ m.id.slice(0, 8) }} · {{ m.estado }}{{ m.activo ? ' · Activo' : '' }}</h3>
        <p>{{ fecha(m.creado_en) }}</p>
        <p v-if="m.metricas">
          {{ m.metricas.entrenamiento }} entrenamiento / {{ m.metricas.calibracion }} calibración.
          {{ m.metricas.advertencia }}
        </p>
        <p v-if="m.error" class="error">{{ m.error }}</p>
        <button
          v-if="administrador && m.estado === 'COMPLETADO'"
          :disabled="ocupado || motivo.trim().length < 10"
          @click="cambiar(m)"
        >
          {{ m.activo ? 'Desactivar versión' : 'Activar versión provisional' }}
        </button>
      </article>
      <nav v-if="totalModelos > 20" class="paginacion">
        <button :disabled="ocupado || paginaModelos === 1" @click="paginarModelos(-1)">
          Anteriores</button
        ><span>Página {{ paginaModelos }}</span
        ><button
          :disabled="ocupado || paginaModelos * 20 >= totalModelos"
          @click="paginarModelos(1)"
        >
          Más versiones
        </button>
      </nav>
    </section>
    <section class="panel">
      <h2>Puntuaciones posteriores al registro</h2>
      <form class="filtros" aria-label="Filtrar puntuaciones" @submit.prevent="aplicarFiltros">
        <label
          >Gestión de registro
          <input
            v-model.number="filtros.gestion"
            type="number"
            min="1900"
            max="9998"
            step="1"
            placeholder="Todas"
            aria-label="Gestión de registro"
            :disabled="ocupado"
          />
        </label>
        <label
          >Artículo
          <select v-model="filtros.articulo_id" aria-label="Artículo" :disabled="ocupado">
            <option value="">Todos</option>
            <option v-for="a in catalogo" :key="a.id" :value="String(a.id)">{{ a.nombre }}</option>
          </select>
        </label>
        <label
          ><input v-model="filtros.alertas" type="checkbox" :disabled="ocupado" /> Solo casos con
          alerta</label
        >
        <button :disabled="ocupado">Aplicar filtros</button>
        <button type="button" :disabled="ocupado" @click="limpiarFiltros">Limpiar filtros</button>
      </form>
      <p>
        La gestión corresponde al registro original de la operación en Bolivia, aunque se haya
        evaluado después.
      </p>
      <p v-if="filtrosPendientes" role="status">
        Hay cambios sin aplicar. Pulsa «Aplicar filtros».
      </p>
      <p>
        Las puntuaciones indican rareza; no son probabilidades ni una conclusión sobre la operación.
      </p>
      <router-link to="/alertas-inventario">Revisar alertas y evidencia documental</router-link>
      <p v-if="ocupado" role="status">Consultando puntuaciones…</p>
      <p v-else-if="!error && !resultados.length">
        No hay puntuaciones para esta selección. Solo aparecen operaciones evaluadas con un modelo
        operativo activo.
      </p>
      <div v-else class="tabla">
        <table>
          <thead>
            <tr>
              <th>Artículo</th>
              <th>Operación</th>
              <th>Cantidad</th>
              <th>Puntuación</th>
              <th>Modelo</th>
              <th>Contexto</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in resultados" :key="r.id">
              <td>{{ r.articulo }}</td>
              <td>
                {{ r.snapshot.tipo
                }}<small>{{ r.recurso }} · {{ fecha(r.snapshot.registrado_en) }}</small>
              </td>
              <td>{{ r.snapshot.cantidad }}</td>
              <td>{{ r.score.toFixed(4) }} · {{ r.alerta ? 'Revisar' : 'Sin alerta' }}</td>
              <td>{{ r.modelo_id.slice(0, 8) }}</td>
              <td>
                {{ r.contexto.referencias }} referencias; mediana {{ r.contexto.mediana
                }}<small
                  >{{ r.contexto.demora_horas.toFixed(1) }} horas entre hecho y registro</small
                >
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="!ocupado && !error">{{ total }} puntuaciones en esta selección.</p>
      <nav v-if="total > 30" class="paginacion">
        <button :disabled="ocupado || pagina === 1" @click="cargar(pagina - 1)">Anterior</button
        ><span>Página {{ pagina }}</span
        ><button :disabled="ocupado || pagina * 30 >= total" @click="cargar(pagina + 1)">
          Siguiente
        </button>
      </nav>
    </section>
  </main>
</template>
<style scoped>
.operativa {
  max-width: 1200px;
  margin: auto;
  padding: 2rem 1rem;
}
header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
}
h1 {
  font-size: 1.8rem;
}
.panel {
  background: white;
  border: 1px solid #dce4eb;
  border-radius: 12px;
  padding: 1.4rem;
  margin: 1.3rem 0;
}
p {
  line-height: 1.6;
}
.nota {
  padding: 0.8rem;
  background: #fff5da;
}
.error {
  color: #962b29;
}
button {
  padding: 0.7rem 1rem;
  border: 1px solid #abbfcc;
  border-radius: 6px;
  background: white;
  cursor: pointer;
}
button:disabled {
  opacity: 0.5;
  cursor: default;
}
label,
small {
  display: block;
}
textarea {
  display: block;
  width: 100%;
  max-width: 600px;
  min-height: 80px;
  margin: 0.6rem 0;
}
article {
  border-top: 1px solid #dce4eb;
  padding: 1rem 0;
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
  border-bottom: 1px solid #dce4eb;
  padding: 0.8rem;
}
small {
  color: #596d7b;
}
.paginacion {
  display: flex;
  gap: 1rem;
  justify-content: space-between;
  margin-top: 1rem;
}
.filtros {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: end;
}
.filtros input:not([type='checkbox']),
.filtros select {
  display: block;
  max-width: 100%;
  box-sizing: border-box;
  padding: 0.5rem;
}
.filtros label {
  min-width: 0;
  max-width: 100%;
}
@media (max-width: 600px) {
  header {
    align-items: start;
    flex-direction: column;
  }
  h1 {
    font-size: 1.4rem;
  }
  .panel {
    padding: 1rem;
  }
}
</style>
