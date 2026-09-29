<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import api from '@/services/api'

interface MovimientoRevision {
  id: number; fecha_movimiento: string; fecha_original?: string | null; fecha_estado: string
  ingresos: number | null; salidas: number | null; saldo_registrado: number
  detalle: string; referencia: string | null; area: string | null; nodo_grafo: string | null
  referencia_estado: string; ruta_imagen_respaldo: string | null
  datos_originales?: Record<string, unknown> | null
}
const props = defineProps<{ movimiento: MovimientoRevision }>()
const emit = defineEmits<{ guardar: []; cerrar: [] }>()
const m = props.movimiento
const form = ref({ ingresos: m.ingresos, salidas: m.salidas, saldo_registrado: m.saldo_registrado,
  nodo_grafo: m.nodo_grafo, referencia: m.referencia, referencia_estado: m.referencia_estado,
  fecha_movimiento: m.fecha_movimiento, decision_fecha: '', motivo: '' })
const guardando = ref(false)
const error = ref('')
const revisiones = ref<{ id: number; fecha: string; usuario: string; detalle: { motivo?: string; previo?: unknown; nuevo?: unknown } }[]>([])
const nodos = ref<{ valor: string; etiqueta: string }[]>([])
const dialogo = ref<HTMLElement | null>(null)
let focoAnterior: HTMLElement | null = null
function atraparFoco(evento: KeyboardEvent) {
  const elementos = Array.from(dialogo.value?.querySelectorAll<HTMLElement>('a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), summary') ?? [])
  const primero = elementos[0], ultimo = elementos[elementos.length - 1]
  if (evento.shiftKey && document.activeElement === primero) { evento.preventDefault(); ultimo?.focus() }
  else if (!evento.shiftKey && document.activeElement === ultimo) { evento.preventDefault(); primero?.focus() }
}
const foto = computed(() => m.ruta_imagen_respaldo
  ? new URL('/' + m.ruta_imagen_respaldo.replace(/\\/g, '/'), new URL(api.defaults.baseURL ?? '/api/v1', window.location.origin).origin).href : '')

async function guardar() {
  if (guardando.value) return
  if (!form.value.motivo.trim()) { error.value = 'Describe qué comprobaste en la evidencia y el motivo de la decisión.'; return }
  guardando.value = true; error.value = ''
  const { fecha_movimiento, decision_fecha, ...datos } = form.value
  try {
    await api.put(`/kardex/movimiento/${m.id}`, { ...datos,
      ingresos: datos.ingresos || null, salidas: datos.salidas || null,
      ...(decision_fecha ? { decision_fecha } : {}),
      ...(decision_fecha === 'corregir' ? { fecha_movimiento } : {}),
    })
    emit('guardar')
  } catch (e: any) {
    error.value = typeof e.response?.data?.detail === 'string' ? e.response.data.detail : 'No se pudo guardar. Revisa los campos y vuelve a intentarlo.'
  } finally { guardando.value = false }
}
onMounted(async () => {
  focoAnterior = document.activeElement as HTMLElement | null
  dialogo.value?.querySelector<HTMLButtonElement>('button')?.focus()
  try {
    const [historial, catalogo] = await Promise.all([api.get(`/kardex/movimiento/${m.id}/revisiones`), api.get('/kardex/nodos')])
    revisiones.value = historial.data; nodos.value = catalogo.data
  } catch { error.value = 'No se pudo cargar el historial de revisiones o el catálogo. Puedes reintentar cerrando y abriendo la revisión.' }
})
onBeforeUnmount(() => { if (focoAnterior?.isConnected) focoAnterior.focus() })
</script>

<template>
  <div class="fondo-revision" @keydown.esc="!guardando && emit('cerrar')">
    <section ref="dialogo" class="revision" role="dialog" aria-modal="true" aria-labelledby="revision-titulo" @keydown.tab="atraparFoco">
      <header><div><h2 id="revision-titulo">Revisión humana · movimiento #{{ m.id }}</h2><p>La evidencia original se conserva. Las fechas no cambian el orden físico.</p></div><button :disabled="guardando" @click="emit('cerrar')" aria-label="Cerrar revisión">✕</button></header>
      <div class="revision-contenido">
        <aside class="evidencia"><a v-if="foto" :href="foto" target="_blank" rel="noopener">Abrir fotografía en tamaño completo ↗</a><img v-if="foto" :src="foto" alt="Página original del Kárdex" /><p v-else>No hay fotografía asociada.</p>
          <details><summary>Datos originales conservados</summary><pre>{{ m.datos_originales ?? 'No hay extracción original conservada; se preservará una línea base antes de esta corrección.' }}</pre></details>
        </aside>
        <form @submit.prevent="guardar">
          <p><strong>Detalle:</strong> {{ m.detalle }}<br /><strong>Área escrita:</strong> {{ m.area || 'Ausente' }}</p>
          <fieldset><legend>Fecha · {{ m.fecha_estado }}</legend><p>Original: {{ m.fecha_original || m.fecha_movimiento }} · Actual: {{ m.fecha_movimiento }}</p>
            <label>Decisión<select v-model="form.decision_fecha"><option value="">Sin decisión sobre la fecha</option><option value="confirmar_documento">Confirmar: así está escrita en el documento</option><option value="corregir">Corregir fecha de consulta con evidencia</option></select></label>
            <label v-if="form.decision_fecha === 'corregir'">Fecha corregida<input v-model="form.fecha_movimiento" type="date" required /></label>
            <small v-if="form.decision_fecha === 'confirmar_documento'">Se conserva la anomalía cronológica como hallazgo documentado, pero deja de estar pendiente de revisión.</small>
          </fieldset>
          <fieldset><legend>Cantidades y saldo</legend><div class="numeros"><label>Ingreso<input v-model.number="form.ingresos" type="number" min="0" step="1" /></label><label>Salida<input v-model.number="form.salidas" type="number" min="0" step="1" /></label><label>Saldo escrito<input v-model.number="form.saldo_registrado" type="number" step="1" required /></label></div></fieldset>
          <fieldset><legend>Área / nodo y referencia</legend>
            <label>Nodo clasificado<input v-model="form.nodo_grafo" list="nodos-hil" maxlength="100" /><datalist id="nodos-hil"><option v-for="n in nodos" :key="n.valor" :value="n.valor">{{ n.etiqueta }}</option></datalist></label>
            <small>Un área ausente no es una referencia ilegible. Mantén cada decisión independiente.</small>
            <label>Referencia<input v-model="form.referencia" maxlength="100" /></label>
            <label>Estado de referencia<select v-model="form.referencia_estado"><option value="PRESENTE">Presente y legible</option><option value="AUSENTE">Ausente en el documento</option><option value="ILEGIBLE">Ilegible</option><option value="INCIERTA">Incierta</option></select></label>
          </fieldset>
          <label>Motivo y evidencia de la revisión<textarea v-model="form.motivo" required maxlength="1000" rows="3" placeholder="Ej.: la fotografía confirma la fecha anotada, aunque sea anterior a la fila precedente."></textarea></label>
          <p v-if="error" role="alert" class="error">{{ error }}</p>
          <div class="acciones"><button type="button" :disabled="guardando" @click="emit('cerrar')">Cancelar</button><button class="guardar" :disabled="guardando">{{ guardando ? 'Guardando…' : 'Guardar revisión auditable' }}</button></div>
          <details><summary>Historial de revisiones ({{ revisiones.length }})</summary><p v-if="!revisiones.length">Sin revisiones anteriores.</p><article v-for="r in revisiones" :key="r.id"><strong>{{ r.usuario }}</strong> · {{ r.fecha }}<p>{{ r.detalle?.motivo || 'Revisión anterior sin motivo estructurado' }}</p><details><summary>Valores anteriores y nuevos</summary><pre>{{ r.detalle }}</pre></details></article></details>
        </form>
      </div>
    </section>
  </div>
</template>

<style scoped>
.fondo-revision { position: fixed; inset: 0; z-index: 1100; background: #14263d99; display: flex; align-items: center; justify-content: center; padding: 1rem; }
.revision { background: white; border-radius: 14px; width: min(1400px, 100%); max-height: 94vh; display: flex; flex-direction: column; color: #24364b; box-shadow: 0 20px 80px #0004; }
header { display: flex; justify-content: space-between; gap: 1rem; padding: 1rem 1.5rem; border-bottom: 1px solid #dde4ec; } header h2 { margin: 0; font-size: 1.2rem; } header p { margin: .3rem 0 0; font-size: .85rem; color: #64748b; }
.revision-contenido { overflow: auto; display: grid; grid-template-columns: 1.1fr 1fr; gap: 1.3rem; padding: 1.2rem; } .evidencia { min-width: 0; background: #f1f5f9; padding: .8rem; border-radius: 10px; } .evidencia img { width: 100%; margin: 1rem 0; } .evidencia a { color: #17587c; }
form { min-width: 0; } fieldset { border: 1px solid #d7e0eb; border-radius: 9px; margin: .8rem 0; padding: .8rem; } legend { font-weight: 700; font-size: .85rem; } label { display: flex; flex-direction: column; gap: .3rem; font-size: .85rem; margin: .5rem 0; }
input, select, textarea { width: 100%; min-width: 0; border: 1px solid #bfcddd; border-radius: 7px; padding: .55rem; font: inherit; box-sizing: border-box; } small { display: block; color: #66768a; } .numeros { display: grid; grid-template-columns: repeat(3, 1fr); gap: .6rem; }
button { border: 1px solid #c8d3df; border-radius: 7px; padding: .55rem .8rem; cursor: pointer; background: white; } button:disabled { opacity: .6; cursor: wait; } .guardar { background: #17587c; color: white; border: 0; } .acciones { display: flex; justify-content: end; gap: .7rem; margin: 1rem 0; } .error { color: #a32d2d; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; font-size: .75rem; } details { margin-top: .8rem; } summary { cursor: pointer; font-weight: 600; } article { border-bottom: 1px solid #d7e0eb; padding: .6rem 0; font-size: .85rem; }
@media (max-width: 850px) { .revision-contenido { grid-template-columns: 1fr; } .evidencia img { max-height: 50vh; object-fit: contain; } }
</style>
