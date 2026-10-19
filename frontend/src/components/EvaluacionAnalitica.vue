<script setup lang="ts">
import type { DiagnosticoAnalitica } from '@/services/analitica'

const props = defineProps<{ diagnostico: DiagnosticoAnalitica; cargando: boolean }>()
const emit = defineEmits<{ seleccionar: [seleccion: string] }>()
const selecciones = [
  { clave: 'modelo', titulo: 'Primeros casos del modelo', filtro: 'top_modelo' },
  { clave: 'regla', titulo: 'Comparación por cantidad', filtro: 'top_regla' },
  { clave: 'control', titulo: 'Muestra sin alerta', filtro: 'control' },
] as const
function proporcion(clave: 'modelo' | 'regla' | 'control') {
  const v = props.diagnostico.evaluacion[clave]
  return props.diagnostico.estado === 'CONSISTENTE' &&
    v.seleccion_integra &&
    v.precision_at_k !== null
    ? (v.precision_at_k * 100).toFixed(1) + '%'
    : 'Pendiente'
}
</script>

<template>
  <section class="evaluacion" aria-label="Evaluación independiente">
    <h3>Comprobación técnica</h3>
    <p v-if="diagnostico.estado === 'CONSISTENTE'" class="verificado">
      El corte y los resultados son consistentes. Esto todavía no demuestra precisión.
    </p>
    <p v-else-if="diagnostico.estado === 'INCONSISTENTE'" role="alert" class="problema">
      Se detectaron inconsistencias. La proporción relevante permanece pendiente hasta resolverlas.
    </p>
    <p v-else>Verificación pendiente: el modelo debe terminar antes de evaluar sus resultados.</p>
    <details>
      <summary>Ver comprobaciones del corte y resultados</summary>
      <div class="tabla">
        <table>
          <thead>
            <tr>
              <th>Comprobación</th>
              <th>Estado</th>
              <th>Detalle</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in diagnostico.comprobaciones" :key="c.codigo">
              <th scope="row">{{ c.titulo }}</th>
              <td>{{ c.estado === 'OK' ? 'Correcto' : 'Revisar' }}</td>
              <td>{{ c.detalle }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p>
        La reproducción de las puntuaciones del archivo privado se comprueba mediante el informe
        local.
      </p>
    </details>
    <h3>Utilidad para auditoría</h3>
    <p>
      Completa las conclusiones de estas tres selecciones. Cada selección abarca el conjunto
      reservado de esta versión.
    </p>
    <div class="tabla">
      <table>
        <thead>
          <tr>
            <th>Selección</th>
            <th>Conclusiones</th>
            <th>Pendientes</th>
            <th>Proporción relevante</th>
            <th>Revisión</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in selecciones" :key="s.clave">
            <th scope="row">{{ s.titulo }}</th>
            <td>
              {{ diagnostico.evaluacion[s.clave].revisados_concluyentes }}/{{
                diagnostico.evaluacion[s.clave].k
              }}
            </td>
            <td>
              {{ diagnostico.evaluacion[s.clave].pendientes }}
              <small v-if="diagnostico.evaluacion[s.clave].errores_documentales">
                {{ diagnostico.evaluacion[s.clave].errores_documentales }} con error documental
              </small>
              <small v-if="diagnostico.evaluacion[s.clave].sin_resultado">
                {{ diagnostico.evaluacion[s.clave].sin_resultado }} sin resultado
              </small>
            </td>
            <td>
              {{ proporcion(s.clave) }}
              <small v-if="!diagnostico.evaluacion[s.clave].seleccion_integra"
                >Revisar integridad</small
              >
            </td>
            <td>
              <button :disabled="cargando" @click="emit('seleccionar', s.filtro)">
                Revisar selección
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <p>
      Error documental y No concluyente siguen pendientes. La muestra sin alerta ayuda a buscar
      omisiones; su proporción relevante no mide recall ni detección de fraude.
    </p>
    <p v-if="diagnostico.cobertura.porcentaje_sin_referencia !== null" class="referencias">
      {{ diagnostico.cobertura.sin_referencia_propia }}/{{ diagnostico.cobertura.evaluacion }} casos
      de evaluación ({{ diagnostico.cobertura.porcentaje_sin_referencia.toFixed(1) }}%) no tienen
      referencia propia de artículo/dirección. Revisa su contexto documental al valorar el
      resultado.
    </p>
  </section>
</template>

<style scoped>
.evaluacion {
  margin: 1rem 0;
  padding: 1rem;
  background: #f7f9fb;
  border: 1px solid #dce4eb;
  border-radius: 10px;
}
h3 {
  margin: 1rem 0 0.5rem;
  font-size: 1rem;
}
p {
  line-height: 1.6;
}
.verificado {
  color: #24513b;
}
.problema {
  color: #952c29;
}
.tabla {
  max-width: 100%;
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}
th,
td {
  text-align: left;
  padding: 0.75rem;
  border-bottom: 1px solid #dce4eb;
  vertical-align: top;
}
small {
  display: block;
  margin-top: 0.25rem;
}
button {
  border: 1px solid #abbfcc;
  background: white;
  color: #244760;
  padding: 0.6rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
}
button:disabled {
  opacity: 0.6;
  cursor: wait;
}
summary {
  cursor: pointer;
  padding: 0.5rem 0;
}
.referencias {
  color: #6b5019;
}
@media (max-width: 700px) {
  .evaluacion {
    padding: 0.75rem;
  }
}
</style>
