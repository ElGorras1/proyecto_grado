<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/layout/AppLayout.vue'

const route = useRoute()
const auth = useAuthStore()

const usarLayout = computed(() => {
  return auth.isAuthenticated && route.name !== 'login' && route.name !== 'forbidden'
})
</script>

<template>
  <AppLayout v-if="usarLayout">
    <router-view />
  </AppLayout>
  <router-view v-else />
</template>
