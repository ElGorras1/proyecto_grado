import { defineStore } from 'pinia'
import axios from 'axios'

export interface UsuarioActual {
  id: number
  nombre: string
  email: string
  rol: 'Administrador' | 'Operador' | 'Auditor'
  area_id: number | null
}

interface AuthState {
  token: string | null
  usuario: UsuarioActual | null
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: sessionStorage.getItem('access_token'),
    usuario: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    rol: (state) => state.usuario?.rol ?? null,
  },

  actions: {
    async login(email: string, password: string) {
      const { data } = await axios.post(`${API_BASE}/auth/login`, { email, password })
      this.token = data.access_token
      sessionStorage.setItem('access_token', data.access_token)
      await this.fetchUsuarioActual()
    },

    async fetchUsuarioActual() {
      if (!this.token) return
      const { data } = await axios.get(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${this.token}` },
      })
      this.usuario = data
    },

    logout() {
      this.token = null
      this.usuario = null
      sessionStorage.removeItem('access_token')
    },
  },
})

/*
 * Nota: se usa sessionStorage (no localStorage) para el token por
 * defecto -> la sesión se cierra al cerrar la pestaña, lo cual es una
 * postura de seguridad razonable para un sistema institucional.
 * Si la institución exige "recordar sesión", cambiar a localStorage
 * es una decisión de negocio, no técnica.
 */
