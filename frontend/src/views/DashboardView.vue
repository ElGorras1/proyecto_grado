<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

onMounted(() => {
  if (!auth.usuario) auth.fetchUsuarioActual()
})

function cerrarSesion() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="dashboard">
    <header>
      <h1>Panel principal</h1>
      <div>
        <span v-if="auth.usuario">{{ auth.usuario.nombre }} · {{ auth.usuario.rol }}</span>
        <button @click="cerrarSesion">Cerrar sesión</button>
      </div>
    </header>

    <p>
      Bienvenido/a. Este es el punto de partida para los módulos de
      Activos, Movimientos/Kardex, Trazabilidad y Auditoría (Sprints 2-5).
    </p>

    <div class="nav-links">
      <router-link v-if="auth.rol === 'Administrador'" :to="{ name: 'usuarios' }" class="nav-item">
        Gestión de usuarios
      </router-link>

      <router-link v-if="auth.rol === 'Administrador'" :to="{ name: 'areas' }" class="nav-item">
        Gestión de áreas
      </router-link>

      <router-link v-if="auth.rol === 'Administrador'" :to="{ name: 'admin' }" class="nav-item">
        Panel de administración
      </router-link>

      <router-link
        v-if="auth.rol === 'Administrador' || auth.rol === 'Auditor'"
        :to="{ name: 'reporteAccesos' }"
        class="nav-item"
      >
        Reporte de accesos
      </router-link>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 2rem;
  font-family: system-ui, sans-serif;
}
header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}
button {
  margin-left: 1rem;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  border: 1px solid #ccc;
  background: white;
  cursor: pointer;
}
.nav-links {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
  flex-wrap: wrap;
}
.nav-item {
  display: inline-block;
  padding: 0.6rem 1.2rem;
  background: #f0f4f8;
  color: #0969da;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 500;
  border: 1px solid #d0d7de;
}
.nav-item:hover {
  background: #e1ecf7;
}
</style>
