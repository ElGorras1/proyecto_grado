<template>
  <div class="forbidden">
    <h1>403 · Acceso denegado</h1>
    <p>Tu rol no tiene privilegios para ver esta sección.</p>
    <router-link :to="{ name: 'dashboard' }">Volver al panel principal</router-link>
  </div>
</template>

<style scoped>
.forbidden {
  padding: 3rem;
  text-align: center;
  font-family: system-ui, sans-serif;
}
</style>
