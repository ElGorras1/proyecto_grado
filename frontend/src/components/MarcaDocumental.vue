<script setup lang="ts">
import type { TratamientoHil } from '@/services/tratamientoHil'
defineProps<{ revision: {
  motivo?: string; criterios?: string[]; hallazgos?: string[]; origen_fecha?: string;
  origen_saldo?: string; saldo_documental?: number | null; diferencia_saldo_documental?: number;
  diferencia_con_cadena_previa?: number; tipo_fila?: string; fecha_documental?: string | null
  origen_cantidades?: string; recuperacion_clave?: string
} | null | undefined; tratamiento?: TratamientoHil | null }>()
</script>
<template>
  <details v-if="revision" class="marca-documental">
    <summary>
      Revisión documental
      <span v-if="tratamiento?.estado === 'CATEGORIZADO_CON_MARCA'"> · categorizado con marca</span>
      <span v-else-if="tratamiento?.estado === 'REQUIERE_RECATEGORIZAR'"> · revisar categoría tras cambios</span>
      <span v-if="['HIPOTESIS', 'SECUENCIA_AJUSTADA'].includes(revision.origen_fecha || '')"> · fecha estimada</span>
      <span v-if="revision.origen_saldo === 'HIPOTESIS'"> · saldo hipotético</span>
      <span v-else-if="revision.origen_saldo === 'RECONSTRUIDO'"> · saldo reconstruido</span>
      <span v-if="revision.tipo_fila === 'ANULADO'"> · anulado en el papel</span>
      <span v-if="revision.tipo_fila === 'RECUENTO'"> · recuento físico</span>
      <span v-if="revision.origen_cantidades === 'HIPOTESIS'"> · cantidad hipotética</span>
      <span v-if="revision.recuperacion_clave"> · fila recuperada desde la foto</span>
      <span v-if="['NOTA', 'DESGLOSE', 'CONTINUACION'].includes(revision.tipo_fila || '')"> · nota sin efecto en el saldo</span>
    </summary>
    <div v-if="tratamiento?.estado === 'CATEGORIZADO_CON_MARCA'" class="tratamiento-hil">
      <p><strong>Tratamiento registrado según los criterios de revisión.</strong> Las marcas conservadas no equivalen a datos confirmados ni habilitan el entrenamiento.</p>
      <ul><li v-for="decision in tratamiento.decisiones" :key="decision.campo">
        <strong>{{ decision.campo }} · {{ decision.etiqueta }}:</strong> {{ decision.motivo }}
      </li></ul>
      <small v-if="tratamiento.autor">{{ tratamiento.autor }}</small>
    </div>
    <p v-else-if="tratamiento?.estado === 'REQUIERE_RECATEGORIZAR'">El dato cambió después de categorizarse. Debe revisarse el tratamiento anterior.</p>
    <p>{{ revision.motivo }}</p>
    <p v-if="revision.saldo_documental !== undefined">Saldo escrito cotejado: {{ revision.saldo_documental ?? 'vacío o no legible' }}</p>
    <p v-if="revision.fecha_documental !== undefined">Fecha escrita cotejada: {{ revision.fecha_documental || 'ausente o no legible' }}</p>
    <p v-if="revision.diferencia_saldo_documental">Diferencia del saldo escrito con la cadena reconstruida: {{ revision.diferencia_saldo_documental }} u.</p>
    <p v-if="revision.diferencia_con_cadena_previa">Diferencia reconocida al fijar la nueva base: {{ revision.diferencia_con_cadena_previa }} u.</p>
    <p v-if="revision.hallazgos?.length">Hallazgos conservados: {{ revision.hallazgos.join(', ') }}</p>
    <small v-if="revision.criterios?.length">Criterios: {{ revision.criterios.join(', ') }}.
      {{ revision.recuperacion_clave ? 'Esta fila fue omitida por el OCR y se recuperó desde la foto conservada.' : 'La extracción original y la foto permanecen en la evidencia.' }}
    </small>
  </details>
</template>
<style scoped>
.marca-documental{font-size:.8rem;margin-top:.4rem;color:#705114;border-left:3px solid #ccaa61;padding:.35rem .55rem;background:#fff8e6}
summary{cursor:pointer;font-weight:600}p{margin:.35rem 0}small{display:block}
</style>

