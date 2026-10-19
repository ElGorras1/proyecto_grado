import { mount, flushPromises, RouterLinkStub } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import MuestraHilView from './MuestraHilView.vue'

const { get, post, replace, auth } = vi.hoisted(() => ({
  get: vi.fn(), post: vi.fn(), replace: vi.fn(), auth: { rol: 'Auditor' }
}))
vi.mock('@/services/api', () => ({ default: { get, post, defaults: { baseURL: 'http://localhost:8000/api/v1' } } }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }))
vi.mock('vue-router', () => ({ useRoute: () => ({ query: {} }), useRouter: () => ({ replace }) }))

const fila = { id: 17, articulo_id: 2, articulo_nombre: 'Libro migrado', tanda: 2,
  fecha_movimiento: '2025-01-01', detalle: 'Venta', ingresos: null, salidas: 1,
  saldo_registrado: 4, tipos_alerta: [], huella_actual: 'a'.repeat(64),
  ruta_imagen_respaldo: 'storage/kardex_images/pagina.webp', revision: null }
let revisada = false

beforeEach(() => {
  auth.rol = 'Auditor'; revisada = false
  get.mockReset(); post.mockReset(); replace.mockReset()
  replace.mockResolvedValue(undefined)
  get.mockImplementation((url: string) => Promise.resolve({ data:
    url === '/kardex/muestras-validacion'
      ? [{ id: 9, creada_en: '2026-10-08T10:00:00Z', creada_por: 'Admin', ids: [17], tanda: 2 }]
      : { id: 9, creada_en: '2026-10-08T10:00:00Z', tanda: 2, semilla: 'acta',
          elegibles: 100, ids: [17], resumen: { sin_revisar: revisada ? 0 : 1,
            coinciden: revisada ? 1 : 0, diferencias: 0, desactualizadas: 0 },
          filas: [{ ...fila, revision: revisada ? { resultado: 'COINCIDE_DOCUMENTO',
            motivo: 'Coincide con la fotografía', revisor: 'Auditor',
            fecha: '2026-10-08T10:05:00Z', vigente: true } : null }] }
  }))
  post.mockImplementation(() => { revisada = true; return Promise.resolve({ data: {} }) })
})

describe('Muestra HIL', () => {
  it('exige motivo y firma la versión de la fila revisada', async () => {
    const wrapper = mount(MuestraHilView, { global: { stubs: { RouterLink: RouterLinkStub } } })
    await flushPromises()
    expect(wrapper.text()).toContain('Sin revisar: 1')
    expect(wrapper.get('details a').attributes('href')).toContain('/storage/kardex_images/pagina.webp')
    await wrapper.findAll('.decision-form button')[0].trigger('click')
    expect(post).not.toHaveBeenCalled()
    await wrapper.get('#motivo-17').setValue('Coincide con la fotografía')
    await wrapper.findAll('.decision-form button')[0].trigger('click')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/kardex/muestras-validacion/9/movimientos/17/revision', {
      resultado: 'COINCIDE_DOCUMENTO', motivo: 'Coincide con la fotografía', huella_fila: 'a'.repeat(64)
    })
    expect(wrapper.text()).toContain('Coinciden: 1')
    wrapper.unmount()
  })

  it('permite consulta al Operador sin acciones de validación', async () => {
    auth.rol = 'Operador'
    const wrapper = mount(MuestraHilView, { global: { stubs: { RouterLink: RouterLinkStub } } })
    await flushPromises()
    expect(wrapper.text()).toContain('Libro migrado')
    expect(wrapper.find('.decision-form').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('Crear un corte de revisión')
    wrapper.unmount()
  })
})
