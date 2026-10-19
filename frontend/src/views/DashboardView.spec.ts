import { mount, RouterLinkStub } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import DashboardView from './DashboardView.vue'
const { auth, push } = vi.hoisted(() => ({
  auth: {
    usuario: { nombre: 'Cuenta', rol: 'Administrador' },
    rol: 'Administrador',
    logout: vi.fn(),
  },
  push: vi.fn(),
}))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }))
vi.mock('vue-router', () => ({ useRouter: () => ({ push }) }))
describe('Inicio', () => {
  it.each(['Administrador', 'Operador', 'Auditor'])(
    'ofrece las secciones y herramientas correspondientes a %s',
    (rol) => {
      auth.rol = rol
      const w = mount(DashboardView, { global: { stubs: { RouterLink: RouterLinkStub } } })
      const rutas = w.findAllComponents(RouterLinkStub).map((l) => {
        const destino = l.props('to')
        return typeof destino === 'string' ? destino : destino.name
      })
      expect(rutas).toEqual([
        'kardexDigital',
        'inventarioVivo',
        'reporteInventario',
        'analitica',
        'analiticaOperativa',
        'gestionInstitucional',
        'alertasInventario',
        ...(rol === 'Administrador' ? ['usuarios'] : []),
        ...(rol !== 'Operador' ? ['reporteAccesos'] : []),
      ])
      w.unmount()
    },
  )
  it('cierra la sesión y vuelve al acceso', async () => {
    const w = mount(DashboardView, { global: { stubs: { RouterLink: RouterLinkStub } } })
    await w.get('button').trigger('click')
    expect(auth.logout).toHaveBeenCalled()
    expect(push).toHaveBeenCalledWith({ name: 'login' })
    w.unmount()
  })
})
