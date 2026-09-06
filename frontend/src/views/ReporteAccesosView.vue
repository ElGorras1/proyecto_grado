<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'

interface AccesoLog {
  id: number
  usuario_id: number | null
  resultado: string
  fecha_hora: string
  ip_origen: string | null
  detalle: Record<string, unknown> | null
}

const accesos = ref<AccesoLog[]>([])
const fechaDesde = ref('')
const fechaHasta = ref('')
const resultado = ref('')
const cargando = ref(false)
const error = ref('')

async function cargarAccesos() {
  cargando.value = true
  error.value = ''
  try {
    const params: Record<string, string> = {}
    if (fechaDesde.value) params.fecha_desde = fechaDesde.value
    if (fechaHasta.value) params.fecha_hasta = fechaHasta.value
    if (resultado.value) params.resultado = resultado.value

    const { data } = await api.get('/auditoria/accesos', { params })
    accesos.value = data
  } catch {
    error.value = 'Error al cargar los registros de acceso'
  } finally {
    cargando.value = false
  }
}

function formatearFecha(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('es-BO', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

onMounted(cargarAccesos)
</script>

<template>
  <div class="reporte-accesos">
    <h1>Reporte de accesos</h1>

    <div class="filtros">
      <label>
        Desde
        <input v-model="fechaDesde" type="date" />
      </label>
      <label>
        Hasta
        <input v-model="fechaHasta" type="date" />
      </label>
      <label>
        Resultado
        <select v-model="resultado">
          <option value="">Todos</option>
          <option value="exito">Éxito</option>
          <option value="rechazo">Rechazo</option>
        </select>
      </label>
      <button :disabled="cargando" @click="cargarAccesos">
        {{ cargando ? 'Cargando...' : 'Filtrar' }}
      </button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <table v-if="accesos.length > 0">
      <thead>
        <tr>
          <th>Fecha / Hora</th>
          <th>Usuario</th>
          <th>Resultado</th>
          <th>IP</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="a in accesos" :key="a.id">
          <td>{{ formatearFecha(a.fecha_hora) }}</td>
          <td>{{ a.usuario_id ?? 'Desconocido' }}</td>
          <td>
            <span :class="a.resultado === 'exito' ? 'resultado-exito' : 'resultado-rechazo'">
              {{ a.resultado }}
            </span>
          </td>
          <td>{{ a.ip_origen ?? '—' }}</td>
        </tr>
      </tbody>
    </table>

    <p v-else-if="!cargando">No hay registros de acceso.</p>

    <router-link to="/">Volver al panel principal</router-link>
  </div>
</template>

<style scoped>
.reporte-accesos {
  padding: 2rem;
  font-family: system-ui, sans-serif;
}

.filtros {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.filtros label {
  display: flex;
  flex-direction: column;
  font-size: 0.85rem;
  gap: 0.25rem;
}

.filtros input,
.filtros select {
  padding: 0.4rem 0.6rem;
  border: 1px solid #ccc;
  border-radius: 6px;
}

.filtros button {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  border: 1px solid #ccc;
  background: #1f6feb;
  color: white;
  cursor: pointer;
  font-weight: 600;
}

.filtros button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1.5rem;
}

th,
td {
  padding: 0.6rem 0.8rem;
  border-bottom: 1px solid #e0e0e0;
  text-align: left;
}

th {
  background: #f4f6f8;
  font-weight: 600;
}

.resultado-exito {
  color: #1a7f37;
  font-weight: 600;
}

.resultado-rechazo {
  color: #d1242f;
  font-weight: 600;
}

.error {
  color: #d33;
  font-size: 0.85rem;
}
</style>
