import { mount, flushPromises, RouterLinkStub } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AnaliticaOperativaView from './AnaliticaOperativaView.vue'
const { get, post, auth } = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  auth: { rol: 'Administrador' },
}))
vi.mock('@/services/api', () => ({ default: { get, post } }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }))
beforeEach(() => {
  auth.rol = 'Administrador'
  get.mockReset()
  post.mockReset()
  get.mockImplementation((url: string) =>
    Promise.resolve({
      data:
        url === '/kardex/articulos'
          ? [{ id: 1, nombre: 'Libro de prueba' }]
          : url.endsWith('/perfil')
            ? {
                total: 0,
                minimo: 125,
                minimo_dias: 14,
                faltantes: 125,
                suficientes: false,
                motivo_insuficiencia: 'Faltan operaciones reales.',
                controles_deterministicos_activos: true,
                modelo_activo: null,
                estado: 'SIN_DATOS_SUFICIENTES',
                exclusiones: {},
              }
            : { filas: [], total: 0 },
    }),
  )
})
describe('Analítica operativa sin datos institucionales', () => {
  it('aplica gestión, artículo y alerta al confirmar, y conserva la selección al paginar', async () => {
    const original = get.getMockImplementation()!
    get.mockImplementation((url: string) =>
      url.endsWith('/resultados')
        ? Promise.resolve({ data: { filas: [], total: 60 } })
        : original(url),
    )
    const w = mount(AnaliticaOperativaView, { global: { stubs: { RouterLink: RouterLinkStub } } })
    await flushPromises()
    await w.get('input[aria-label="Gestión de registro"]').setValue('2025')
    await w.get('select[aria-label="Artículo"]').setValue('1')
    await w.get('input[type=checkbox]').setValue(false)
    expect(w.text()).toContain('Hay cambios sin aplicar')
    expect(get.mock.calls.filter((c) => c[0].endsWith('/resultados'))).toHaveLength(1)
    await w.get('form[aria-label="Filtrar puntuaciones"]').trigger('submit')
    await flushPromises()
    expect(get).toHaveBeenCalledWith('/analitica-operativa/resultados', {
      params: {
        pagina: 1,
        gestion: 2025,
        articulo_id: '1',
        alertas: false,
      },
    })
    await w.get('input[aria-label="Gestión de registro"]').setValue('2026')
    await w
      .findAll('button')
      .find((b) => b.text() === 'Siguiente')!
      .trigger('click')
    await flushPromises()
    expect(get).toHaveBeenCalledWith('/analitica-operativa/resultados', {
      params: {
        pagina: 2,
        gestion: 2025,
        articulo_id: '1',
        alertas: false,
      },
    })
    await w
      .findAll('button')
      .find((b) => b.text() === 'Limpiar filtros')!
      .trigger('click')
    await flushPromises()
    expect(get).toHaveBeenCalledWith('/analitica-operativa/resultados', {
      params: {
        pagina: 1,
        gestion: undefined,
        articulo_id: undefined,
        alertas: true,
      },
    })
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
  it('distingue una consulta fallida de una selección vacía', async () => {
    const w = mount(AnaliticaOperativaView, { global: { stubs: { RouterLink: RouterLinkStub } } })
    await flushPromises()
    const original = get.getMockImplementation()!
    get.mockImplementation((url: string) =>
      url.endsWith('/resultados') ? Promise.reject(new Error('sin red')) : original(url),
    )
    await w.get('form').trigger('submit')
    await flushPromises()
    expect(w.text()).toContain('No se pudo completar')
    expect(w.text()).not.toContain('No hay puntuaciones para esta selección')
    w.unmount()
  })
  it('informa falta de datos y no entrena automáticamente', async () => {
    const w = mount(AnaliticaOperativaView, { global: { stubs: { RouterLink: RouterLinkStub } } })
    await flushPromises()
    expect(w.text()).toContain('Faltan operaciones reales.')
    expect(post).not.toHaveBeenCalled()
    const entrenar = w.findAll('button').find((b) => b.text().includes('Preparar nueva versión'))!
    expect(entrenar.attributes('disabled')).toBeDefined()
    w.unmount()
  })
  it.each(['Auditor', 'Operador'])('mantiene lectura para %s', async (rol) => {
    auth.rol = rol
    const w = mount(AnaliticaOperativaView, { global: { stubs: { RouterLink: RouterLinkStub } } })
    await flushPromises()
    expect(w.findAll('button').some((b) => b.text().includes('Preparar nueva versión'))).toBe(false)
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
})
