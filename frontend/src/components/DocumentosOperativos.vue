<script setup lang="ts">
import { ref, watch } from 'vue'
import api from '@/services/api'
const props = defineProps<{ articuloId: number; puedeSubir: boolean }>()
interface Documento { id: number; nombre: string; referencia: string; sha256: string }
const documentos = ref<Documento[]>([])
const referencia = ref('')
const archivo = ref<File | null>(null)
const error = ref('')
const ocupado = ref(false)
const versionArchivo = ref(0)
let turno = 0
async function cargar() {
  const actual = ++turno
  documentos.value = []
  error.value = ''
  archivo.value = null
  versionArchivo.value++
  referencia.value = ''
  try {
    const { data } = await api.get(`/kardex/articulos/${props.articuloId}/documentos`)
    if (actual === turno) documentos.value = data
  } catch { if (actual === turno) error.value = 'No se pudieron cargar los documentos. Pulsa Actualizar.' }
}
watch(() => props.articuloId, cargar, { immediate: true })
function seleccionar(e: Event) { archivo.value = (e.target as HTMLInputElement).files?.[0] ?? null }
async function subir() {
  if (!archivo.value || ocupado.value) return
  if (archivo.value.size > 10 * 1024 * 1024) { error.value = 'El límite es 10 MB.'; return }
  ocupado.value = true
  error.value = ''
  const id = props.articuloId
  const datos = new FormData()
  datos.append('referencia', referencia.value)
  datos.append('archivo', archivo.value)
  try {
    await api.post(`/kardex/articulos/${id}/documentos`, datos)
    if (id === props.articuloId) await cargar()
  } catch { if (id === props.articuloId) error.value = 'No se pudo adjuntar. Revisa la referencia, el formato y el tamaño; actualiza la lista antes de repetir.' }
  finally { ocupado.value = false }
}
async function descargar(d: Documento) {
  error.value = ''
  try {
    const { data } = await api.get(`/kardex/articulos/${props.articuloId}/documentos/${d.id}/archivo`, { responseType: 'blob' })
    const url = URL.createObjectURL(data)
    const enlace = document.createElement('a')
    enlace.href = url; enlace.download = d.nombre; enlace.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch { error.value = 'No se pudo descargar o verificar el documento.' }
}
</script>

<template>
  <section id="ficha-documentos" class="context-box detalle-panel" aria-label="Documentos de respaldo">
    <h3>Actas y documentos de respaldo</h3>
    <p>Relaciona el documento con el artículo y la referencia utilizada en la operación. Adjuntarlo no confirma un conteo ni modifica existencias.</p>
    <button type="button" @click="cargar">Actualizar documentos</button>
    <p v-if="error" role="alert">{{ error }}</p>
    <ul v-if="documentos.length">
      <li v-for="d in documentos" :key="d.id">
        {{ d.referencia }} — <button type="button" @click="descargar(d)">{{ d.nombre }}</button>
      </li>
    </ul>
    <p v-else>Sin documentos adjuntos.</p>
    <form v-if="puedeSubir" @submit.prevent="subir">
      <label>Referencia del acta o factura
        <input v-model="referencia" required minlength="3" maxlength="200" :disabled="ocupado" />
      </label>
      <label>Documento (PDF, PNG, JPEG o WebP; máximo 10 MB)
        <input :key="`${articuloId}-${versionArchivo}`" type="file" accept="application/pdf,image/png,image/jpeg,image/webp" required :disabled="ocupado" @change="seleccionar" />
      </label>
      <button type="submit" :disabled="ocupado || !archivo">{{ ocupado ? 'Guardando…' : 'Adjuntar documento' }}</button>
    </form>
  </section>
</template>

<style scoped>
form, label { display: grid; gap: .5rem; }
form { margin-top: 1rem; gap: 1rem; }
input { max-width: 100%; min-width: 0; }
li { overflow-wrap: anywhere; margin-block: .5rem; }
</style>
