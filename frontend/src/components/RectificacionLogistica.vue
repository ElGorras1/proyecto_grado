<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import type { FuenteLogistica } from '@/services/rectificacionLogistica'
const props = defineProps<{ articuloId: number; fuente: FuenteLogistica; areas: { id: number; nombre: string }[]; encargados: { id: number; nombre: string }[] }>()
const emit = defineEmits<{ guardado: []; cerrar: []; recargar: [] }>()
const admin = computed(() => useAuthStore().rol === 'Administrador')
const form = ref({ ...props.fuente.datos })
const documento = ref(''), motivo = ref(''), cotejo = ref(false), guardando = ref(false), error = ref('')
const tipoEntrega = computed(() => props.fuente.clase === 'ENTREGA')
const tipoEvento = computed(() => props.fuente.clase === 'EVENTO_CUSTODIA')
let envio: { contenido: string; solicitud_id: string } | null = null, vigente = true
onUnmounted(() => { vigente = false })
async function guardar() {
  if (!admin.value || guardando.value || !cotejo.value) return
  const cambios = { ...form.value, clase: props.fuente.clase }
  if (tipoEvento.value) {
    cambios.area_destino_id = cambios.tipo === 'RETORNO' ? cambios.area_destino_id : null
    cambios.comprador = cambios.tipo === 'VENTA' ? cambios.comprador : null
  }
  const datos = { registro_id: props.fuente.registro_id, version_esperada: props.fuente.version,
    cambios, referencia_documento: documento.value, motivo: motivo.value, evidencia_revisada: cotejo.value }
  const contenido = JSON.stringify(datos)
  if (!envio || envio.contenido !== contenido) envio = { contenido, solicitud_id: crypto.randomUUID() }
  guardando.value = true; error.value = ''
  try {
    await api.post(`/kardex/articulos/${props.articuloId}/rectificaciones-logisticas`, { ...datos, solicitud_id: envio.solicitud_id })
    if (vigente) emit('guardado')
  } catch (e: any) {
    if (vigente) error.value = typeof e.response?.data?.detail === 'string' ? e.response.data.detail :
      'No se pudo confirmar el resultado. Consulta el historial o reintenta este mismo envío.'
  } finally { if (vigente) guardando.value = false }
}
</script>
<template>
  <section v-if="admin" id="rectificacion-logistica" class="rectificacion-logistica" aria-label="Rectificar logística">
    <h3>Rectificar {{ fuente.clase === 'TRANSFERENCIA' ? 'transferencia' : tipoEntrega ? 'entrega externa' : 'venta o retorno' }} #{{ fuente.registro_id }}</h3>
    <p>El registro original se conserva. La corrección crea una compensación vinculada y comprueba la disponibilidad actual.</p>
    <p v-if="error" role="alert" class="alert alert-error">{{ error }}</p>
    <form @submit.prevent="guardar"><fieldset :disabled="guardando">
      <label>Cantidad correcta<input v-model.number="form.cantidad" type="number" min="0" max="2147483647" step="1" required /></label>
      <small>Usa 0 para anular el efecto. La compensación se bloqueará si contradice hechos posteriores.</small>
      <label v-if="!tipoEvento">Área de origen<select v-model.number="form.area_origen_id" required>
        <option v-for="area in areas" :key="area.id" :value="area.id">{{ area.nombre }}</option>
      </select></label>
      <label v-if="fuente.clase === 'TRANSFERENCIA' || (tipoEvento && form.tipo === 'RETORNO')">Área de destino<select v-model.number="form.area_destino_id" required>
        <option v-for="area in areas" :key="area.id" :value="area.id">{{ area.nombre }}</option>
      </select></label>
      <label v-if="tipoEvento || tipoEntrega">Tipo corregido<select v-model="form.tipo" required>
        <template v-if="tipoEntrega"><option value="FERIA">Feria</option><option value="CONSIGNACION">Consignación</option></template>
        <template v-else><option value="VENTA">Venta</option><option value="RETORNO">Retorno</option></template>
      </select></label>
      <template v-if="tipoEntrega">
        <label>Receptor<input v-model="form.receptor_nombre" minlength="3" maxlength="200" required /></label>
        <label>Tipo de receptor<select v-model="form.receptor_tipo"><option value="PERSONA">Persona</option><option value="INSTITUCION">Institución</option></select></label>
        <label>Ubicación externa<input v-model="form.ubicacion_externa" minlength="3" maxlength="200" required /></label>
        <label>Ciudad<input v-model="form.ciudad" :required="form.tipo === 'FERIA'" maxlength="100" /></label>
      </template>
      <label v-if="tipoEvento && form.tipo === 'VENTA'">Comprador<input v-model="form.comprador" required maxlength="200" /></label>
      <label>Encargado correcto<select v-model.number="form.encargado_id" required><option v-for="u in encargados" :key="u.id" :value="u.id">{{ u.nombre }}</option></select></label>
      <label>Documento del hecho corregido<input v-model="form.referencia_documento" minlength="3" maxlength="200" required /></label>
      <label>Observaciones del hecho<textarea v-model="form.observaciones" maxlength="1000" /></label>
      <label>Acta o documento que respalda la rectificación<input v-model="documento" minlength="3" maxlength="200" required /></label>
      <label>Motivo de la rectificación<textarea v-model="motivo" minlength="10" maxlength="2000" required /></label>
      <label class="cotejo"><input v-model="cotejo" type="checkbox" required /> Cotejé los documentos y confirmo que se trata de un error de registro.</label>
      <div class="acciones"><button type="submit" class="btn-primary" :disabled="!cotejo">{{ guardando ? 'Guardando…' : 'Guardar rectificación' }}</button>
        <button type="button" class="btn-outline" @click="emit('cerrar')">Cancelar</button>
        <button v-if="error" type="button" class="btn-outline" @click="emit('recargar')">Actualizar registros</button>
      </div>
    </fieldset></form>
  </section>
</template>
<style scoped>
.rectificacion-logistica { background: white; border: 1px solid var(--border-color); border-radius: .6rem; padding: 1.25rem; margin: 1.5rem 0; max-width: 760px; }
fieldset { border: 0; padding: 0; min-width: 0; } label { display: grid; gap: .4rem; margin-top: 1rem; }
input, select, textarea { padding: .65rem; border: 1px solid var(--border-color); border-radius: .4rem; font: inherit; width: 100%; box-sizing: border-box; }
.cotejo { display: flex; align-items: flex-start; gap: .6rem; } .cotejo input { width: auto; }
.acciones { display: flex; flex-wrap: wrap; gap: .75rem; margin-top: 1rem; } small { color: var(--text-secondary); }
</style>
