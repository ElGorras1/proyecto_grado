import { mount, RouterLinkStub } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import NavegacionTrabajo from './NavegacionTrabajo.vue'
const { ruta, auth } = vi.hoisted(() => ({ ruta: { name: 'reporteInventario', query: { gestion: '2020', origen: 'historico' } as Record<string, string> }, auth: { rol: 'Administrador' } }))
vi.mock('vue-router', () => ({ useRoute: () => ruta }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }))
beforeEach(() => { ruta.name = 'reporteInventario'; ruta.query = { gestion: '2020', origen: 'historico' } })
describe('Navegación por tareas', () => {
  it.each(['Administrador', 'Auditor', 'Operador'])('muestra los espacios permitidos a %s', rol => {
    auth.rol = rol
    const w = mount(NavegacionTrabajo, { global: { stubs: { RouterLink: RouterLinkStub } } })
    const principales = w.get('[aria-label="Navegación principal"]').text()
    expect(principales.includes('Administración')).toBe(rol !== 'Operador')
    expect(principales).toContain('Artículos e inventario')
    expect(principales).not.toContain('Entrenamiento')
    w.unmount()
  })
  it('conserva la gestión al cambiar entre movimientos, resumen y cierre', () => {
    auth.rol = 'Administrador'
    const w = mount(NavegacionTrabajo, { global: { stubs: { RouterLink: RouterLinkStub } } })
    const links = w.findAllComponents(RouterLinkStub).map(l => l.props('to'))
    expect(links).toContainEqual({ name: 'gestionInstitucional', query: { gestion: '2020', origen: 'historico' } })
    expect(links).toContainEqual({ name: 'cierresGestion', query: { gestion: '2020', origen: 'historico' } })
    w.unmount()
  })
  it('abre las operaciones del artículo consultado sin volver a buscarlo', () => {
    auth.rol = 'Administrador'; ruta.name = 'kardexDigital'; ruta.query = { articulo_id: '116' }
    const w = mount(NavegacionTrabajo, { global: { stubs: { RouterLink: RouterLinkStub } } })
    expect(w.findAllComponents(RouterLinkStub).map(l => l.props('to'))).toContainEqual({ name: 'inventarioVivo', query: { articulo_id: '116' } })
    w.unmount()
  })
})
