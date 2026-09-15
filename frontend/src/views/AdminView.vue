<script setup lang="ts">
import { ref } from 'vue'
import api from '@/services/api'

const resultado = ref('')

async function probarEndpointAdmin() {
  try {
    const { data } = await api.get('/auth/admin/ping')
    resultado.value = data.mensaje
  } catch {
    resultado.value = 'Error al llamar al endpoint administrativo'
  }
}
</script>

<template>
  <div class="admin-view">
    <div class="header-nav">
      <router-link to="/" class="btn-back"><i class="pi pi-arrow-left"></i> Volver</router-link>
      <h1>Administración</h1>
    </div>
    <p>Gestión de usuarios, roles y permisos (Sprint 1 en adelante).</p>
    <button @click="probarEndpointAdmin">Probar endpoint protegido (Administrador)</button>
    <p>{{ resultado }}</p>
  </div>
</template>

<style scoped>
.admin {
  padding: 2rem;
  font-family: system-ui, sans-serif;
}
</style>
