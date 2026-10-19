<script setup lang="ts">
import { ref, watch } from 'vue'
import api from '@/services/api'
interface Estado { observado: boolean; excluir_entrenamiento: boolean; motivo: string }
const props = defineProps<{ articuloId: number; estado?: Estado | null; editable: boolean }>()
const emit = defineEmits<{ guardado: [estado: Estado] }>()
const form = ref<Estado>({ observado: false, excluir_entrenamiento: false, motivo: '' })
const guardando = ref(false), error = ref('')
watch(() => props.estado, estado => {
  form.value = { observado: estado?.observado ?? false, excluir_entrenamiento: estado?.excluir_entrenamiento ?? false, motivo: estado?.motivo ?? '' }
}, { immediate: true })
watch(() => form.value.observado, valor => { if (!valor) form.value.excluir_entrenamiento = false })
async function guardar() {
  if (guardando.value || !props.editable) return
  if (form.value.motivo.trim().length < 8) { error.value = 'Describe el motivo y la evidencia de la decisión.'; return }
  guardando.value = true; error.value = ''
  try {
    const { data } = await api.put<Estado>('/kardex/articulos/' + props.articuloId + '/observacion-hil', form.value)
    emit('guardado', data)
  } catch (e: any) {
    error.value = typeof e.response?.data?.detail === 'string' ? e.response.data.detail : 'No se pudo guardar la observación.'
  } finally { guardando.value = false }
}
</script>
<template>
  <section class="observacion-documental">
    <h4>Observación documental y entrenamiento</h4>
    <p v-if="estado?.observado"><strong>Artículo observado.</strong> {{ estado.motivo }}<span v-if="estado.excluir_entrenamiento"> Excluido del entrenamiento histórico.</span></p>
    <p v-else>Sin observación especial registrada. Esto no certifica todas sus filas.</p>
    <p>Las operaciones actuales conservan sus controles de apertura y stock, aunque el histórico esté observado.</p>
    <form v-if="editable" @submit.prevent="guardar">
      <label><input v-model="form.observado" type="checkbox"> Mantener el artículo observado</label>
      <label><input v-model="form.excluir_entrenamiento" type="checkbox" :disabled="!form.observado"> Excluir del entrenamiento histórico mientras se aclara</label>
      <label>Motivo y evidencia<textarea v-model="form.motivo" required minlength="8" maxlength="2000" rows="3" /></label>
      <p v-if="error" role="alert">{{ error }}</p>
      <button :disabled="guardando">{{ guardando ? 'Guardando…' : 'Guardar decisión con historial' }}</button>
    </form>
  </section>
</template>
<style scoped>
.observacion-documental{padding:1rem;border:1px solid var(--border-color);border-radius:8px;margin:1rem 0}
label{display:block;margin:.6rem 0}textarea{display:block;width:100%;margin-top:.3rem}
</style>

