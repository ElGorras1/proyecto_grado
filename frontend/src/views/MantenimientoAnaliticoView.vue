<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
interface Estado { configurada: boolean; habilitada: boolean; modelo_base_id: string | null; preparar_candidatos?: boolean; gestion_hasta?: number; intervalo_segundos?: number; revision_dias?: number; ultimo_analisis?: string | null; proxima_revision?: string | null; ultimo_error?: string | null; ultimo_informe?: { elegibles: number; nuevos_resultados: number; nuevos_avisos: number; mantenimiento: { estado: string; mensaje?: string } } | null; huella_politica: string | null; candidato?: { id: string; estado: string; error: string | null } | null; alcance?: string }
const auth = useAuthStore(), administrador = computed(() => auth.rol === 'Administrador')
type EstadoConSeguimiento = Estado & { resultados_seguimiento?: number }
const datos = ref<EstadoConSeguimiento | null>(null), modelos = ref<{ id: string; creado_en: string; estado: string }[]>([])
const cargando = ref(false), guardando = ref(false), error = ref(''), mensaje = ref('')
const config = ref({ modelo_base_id: '', habilitada: true, preparar_candidatos: true, gestion_hasta: 2025, minutos: 5, revision_dias: 30, motivo: '' })
function fecha(valor?: string | null) { return valor ? new Date(valor).toLocaleString('es-BO', { timeZone: 'America/La_Paz' }) : 'Pendiente' }
function fallo(e: unknown) { const d = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail; return typeof d === 'string' ? d : 'No se pudo completar la consulta. Puedes volver a intentar.' }
async function cargar() {
  cargando.value = true; error.value = ''
  try {
    const [e, m] = await Promise.all([api.get<EstadoConSeguimiento>('/automatizacion/estado'), administrador.value ? api.get('/analitica/modelos', { params: { limite: 100 } }) : Promise.resolve({ data: { filas: [] } })])
    datos.value = e.data; modelos.value = m.data.filas.filter((v: { estado: string }) => v.estado === 'COMPLETADO')
    config.value = { modelo_base_id: e.data.modelo_base_id ?? '', habilitada: e.data.configurada ? e.data.habilitada : true, preparar_candidatos: e.data.preparar_candidatos ?? true, gestion_hasta: e.data.gestion_hasta ?? 2025, minutos: (e.data.intervalo_segundos ?? 300) / 60, revision_dias: e.data.revision_dias ?? 30, motivo: '' }
  } catch (e) { error.value = fallo(e) } finally { cargando.value = false }
}
async function guardar() {
  if (!administrador.value || guardando.value || !datos.value) return
  guardando.value = true; error.value = ''; mensaje.value = ''
  try {
    const { minutos, motivo, ...campos } = config.value
    await api.put('/automatizacion/politica', { ...campos, intervalo_segundos: minutos * 60, motivo: motivo.trim(), huella_esperada: datos.value.huella_politica })
    await cargar(); mensaje.value = 'Configuración guardada. El servidor realizará las comprobaciones programadas.'
  } catch (e) { error.value = fallo(e) } finally { guardando.value = false }
}
onMounted(cargar)
</script>
<template>
  <main class="mantenimiento"><header><div><h1>Mantenimiento del análisis</h1><p>El personal revisa los avisos; el servidor comprueba los datos y mantiene el análisis disponible.</p></div><button class="btn-outline" :disabled="cargando || guardando" @click="cargar">Actualizar estado</button></header>
    <p v-if="cargando" role="status">Consultando estado…</p><p v-if="error" role="alert" class="error">{{ error }}</p><p v-if="mensaje" role="status">{{ mensaje }}</p>
    <section v-if="datos" class="panel" aria-label="Estado de la automatización"><h2>{{ datos.configurada && datos.habilitada ? 'Automatización habilitada' : datos.configurada ? 'Automatización pausada' : 'Configuración pendiente' }}</h2>
      <template v-if="datos.configurada"><p>Comprobación de datos nuevos: cada {{ (datos.intervalo_segundos ?? 300) / 60 }} minutos · Archivo hasta {{ datos.gestion_hasta }}.</p><p>Revisión de necesidad de actualización: cada {{ datos.revision_dias }} días.</p><p>Último intento de análisis: {{ fecha(datos.ultimo_analisis) }} · Próxima revisión de actualización: {{ fecha(datos.proxima_revision) }}.</p>
        <p v-if="datos.ultimo_error" role="alert" class="error">{{ datos.ultimo_error }}</p>
        <template v-if="datos.ultimo_informe"><p>Último análisis registrado: {{ datos.ultimo_informe.elegibles }} movimientos elegibles · {{ datos.ultimo_informe.nuevos_resultados }} resultados nuevos · {{ datos.ultimo_informe.nuevos_avisos }} avisos nuevos.</p><p>{{ datos.ultimo_informe.mantenimiento.mensaje || (datos.ultimo_informe.mantenimiento.estado === 'PROGRAMADO' ? 'La revisión se realizará en la fecha programada.' : 'Consulta el estado de mantenimiento.') }}</p></template>
        <p v-if="datos.resultados_seguimiento !== undefined">Seguimiento conservado: {{ datos.resultados_seguimiento }} resultados. La bandeja muestra únicamente los avisos pendientes.</p>
        <p v-if="datos.candidato">Versión preparada para evaluación: {{ datos.candidato.estado }}. El modelo en uso se conserva.<span v-if="datos.candidato.error"> {{ datos.candidato.error }}</span></p>
        <router-link v-if="datos.candidato?.estado === 'COMPLETADO'" :to="{ name: 'analitica', query: { modelo: datos.candidato.id, avanzado: '1' } }">Revisar la versión preparada</router-link>
      </template>
      <p>{{ datos.alcance || 'La configuración inicial se realiza una vez desde mantenimiento.' }}</p><p>Las tareas se ejecutan mientras el servidor está iniciado. Las comprobaciones pendientes se retoman al volver a iniciarlo.</p>
    </section>
    <details v-if="administrador && datos"><summary>Configuración avanzada</summary><p>Una nueva versión debe superar las comprobaciones técnicas antes de seleccionarla como referencia. Los estudios y resultados anteriores se conservan.</p>
      <form @submit.prevent="guardar"><label>Modelo de referencia<select v-model="config.modelo_base_id" required><option value="" disabled>Seleccionar versión completada</option><option v-for="m in modelos" :key="m.id" :value="m.id">{{ fecha(m.creado_en) }} · {{ m.id.slice(0, 8) }}</option></select></label><label>Última gestión documental<input v-model.number="config.gestion_hasta" type="number" min="1900" max="9998" required /></label><label>Comprobar datos cada (minutos)<input v-model.number="config.minutos" type="number" min="1" max="1440" step="1" required /></label><label>Comprobar actualización cada (días)<input v-model.number="config.revision_dias" type="number" min="1" max="365" required /></label><label class="check"><input v-model="config.habilitada" type="checkbox" /> Habilitar análisis automático</label><label class="check"><input v-model="config.preparar_candidatos" type="checkbox" /> Preparar candidatos cuando existan cambios suficientes</label><label>Motivo del cambio<textarea v-model="config.motivo" required minlength="10" maxlength="2000" /></label><button class="btn-primary" :disabled="cargando || guardando || config.motivo.trim().length < 10">Guardar configuración</button></form>
    </details>
  </main>
</template>
<style scoped>
.mantenimiento { max-width: 1050px; margin: auto; padding: 1.5rem 1.25rem; } header { display: flex; justify-content: space-between; flex-wrap: wrap; align-items: center; gap: 1rem; } .panel { border: 1px solid var(--border-color); border-radius: 8px; padding: 1.25rem; margin: 1rem 0; } p { line-height: 1.65; } summary { padding: 1rem 0; cursor: pointer; font-weight: 600; } form { display: grid; grid-template-columns: repeat(auto-fit,minmax(min(100%,250px),1fr)); gap: 1rem; } label { display: flex; flex-direction: column; gap: .4rem; } input,select,textarea { padding: .6rem; border: 1px solid var(--border-color); border-radius: 6px; width: 100%; } .check { flex-direction: row; align-items: center; } .check input { width: auto; } .error { color: #a12222; }
</style>
