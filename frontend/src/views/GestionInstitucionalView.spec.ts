import { mount, flushPromises, RouterLinkStub } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import GestionInstitucionalView from './GestionInstitucionalView.vue'
const { get, post, auth, ruta, reemplazar } = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  auth: { rol: 'Administrador' },
  ruta: {} as Record<string, string>,
  reemplazar: vi.fn(),
}))
vi.mock('vue-router', async importOriginal => ({ ...await importOriginal<typeof import('vue-router')>(), useRoute: () => ({ query: ruta }), useRouter: () => ({ replace: reemplazar }) }))
vi.mock('@/services/api', () => ({ default: { get, post } }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }))
let permitido = true
const informe = {
  gestion: 2025,
  generado_en: '2026-10-08T12:00:00Z',
  limites: 'Saldo documental provisional',
  inventario_actual: [],
  movimientos: [],
  totales_actuales: { operativo: 0, documental_sin_activar: 100, articulos_sin_saldo_confiable: 1 },
  resumen_periodo: { eventos: 0, ingresos_y_ajustes: 0, salidas_y_ajustes: 0, trasladado: 0 },
  cobertura_historica: { historicos: 200, elegibles: 180, porcentaje_fisico: null },
  articulos_con_error_integridad: [],
}
beforeEach(() => {
  auth.rol = 'Administrador'
  permitido = true
  Object.keys(ruta).forEach(k => delete ruta[k])
  get.mockReset()
  post.mockReset()
  reemplazar.mockReset(); reemplazar.mockResolvedValue(undefined)
  get.mockImplementation((url: string) =>
    Promise.resolve({
      data: url.endsWith('vista-previa')
        ? {
            snapshot: {
              gestion: 2025,
              total: 100,
              articulos: [{ articulo_id: 1, total: 100 }],
              alcance: 'Solo digital',
              corte_exclusivo: '2027-01-01T04:00:00Z',
            },
            huella: 'a'.repeat(64),
            puede_cerrar: permitido,
            impedimentos: permitido ? [] : ['La gestión todavía no terminó.'],
          }
        : url === '/cierres-anuales'
          ? { filas: [], total: 0 }
          : informe,
    }),
  )
})
function montar() {
  return mount(GestionInstitucionalView, { global: { stubs: { RouterLink: RouterLinkStub } } })
}
describe('Gestión institucional', () => {
  it('comparte la gestión consultada desde el resumen con los otros apartados', async () => {
    ruta.gestion = '2025'
    const w = mount(GestionInstitucionalView, { props: { seccion: 'resumen' }, global: { stubs: { RouterLink: RouterLinkStub } } })
    await flushPromises()
    await w.get('form.filtros input').setValue(2019)
    await w.get('form.filtros').trigger('submit'); await flushPromises()
    expect(reemplazar).toHaveBeenCalledWith({ query: { gestion: 2019 } })
    w.unmount()
  })
  it('consulta el resumen sin cargar vista previa ni cierres', async () => {
    const w = mount(GestionInstitucionalView, { props: { seccion: 'resumen' }, global: { stubs: { RouterLink: RouterLinkStub } } })
    await flushPromises()
    expect(get.mock.calls.map(c => c[0])).toEqual(['/reportes/institucional'])
    expect(w.text()).toContain('Resumen institucional')
    expect(w.text()).not.toContain('Registros digitales de')
    expect(w.text()).toContain('Saldos documentales')
    expect(w.find('.cierre-form').exists()).toBe(false)
    expect(w.text()).not.toContain('Cierres conservados de todas las gestiones')
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
  it('consulta el cierre por separado y no propone guardar un balance vacío', async () => {
    const original = get.getMockImplementation()!
    get.mockImplementation(async (url: string) => {
      const r = await original(url)
      if (url.endsWith('vista-previa')) r.data.snapshot.articulos = []
      return r
    })
    const w = mount(GestionInstitucionalView, { props: { seccion: 'cierres' }, global: { stubs: { RouterLink: RouterLinkStub } } })
    await flushPromises()
    expect(get.mock.calls.map(c => c[0])).not.toContain('/reportes/institucional')
    expect(w.text()).toContain('no necesitas registrar un cierre vacío')
    expect(w.find('.cierre-form').exists()).toBe(false)
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
  it('vuelve a cargar al pasar del resumen al cierre sin reutilizar información de la otra pantalla', async () => {
    const w = mount(GestionInstitucionalView, { props: { seccion: 'resumen' }, global: { stubs: { RouterLink: RouterLinkStub } } })
    await flushPromises()
    await w.setProps({ seccion: 'cierres' }); await flushPromises()
    expect(w.text()).toContain('Vista previa del cierre')
    expect(w.text()).not.toContain('Saldo documental sin activar')
    await w.setProps({ seccion: 'resumen' }); await flushPromises()
    expect(w.text()).toContain('Saldo documental sin activar')
    expect(w.find('.cierre-form').exists()).toBe(false)
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
  it('consulta inicialmente la referencia documental 2025 sin registrar cierres', async () => {
    const w = montar()
    await flushPromises()
    expect(get).toHaveBeenCalledWith('/reportes/institucional', { params: { gestion: 2025 } })
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
  it('mantiene el informe de la gestión consultada hasta confirmar otro año', async () => {
    ruta.gestion = '2026'
    const original = get.getMockImplementation()!
    get.mockImplementation((url: string, opciones: { params: Record<string, string | number> }) =>
      url === '/reportes/institucional'
        ? Promise.resolve({
            data: {
              ...informe,
              gestion: opciones.params.gestion,
              cobertura_historica: {
                ...informe.cobertura_historica,
                por_gestion: {
                  '2025': { disponibles: 90, elegibles: 87 },
                },
              },
            },
          })
        : original(url),
    )
    const w = montar()
    await flushPromises()
    await w.get('form.filtros input').setValue(2025)
    expect(w.text()).toContain('La gestión cambió sin consultar')
    await w.get('form.filtros').trigger('submit')
    await flushPromises()
    expect(get).toHaveBeenCalledWith('/reportes/institucional', { params: { gestion: 2025 } })
    expect(w.text()).toContain('Documentos históricos de 2025')
    expect(w.text()).toContain('90 movimientos escaneados activos')
    expect(w.text()).toContain('87 elegibles')
    const enlace = w
      .findAllComponents(RouterLinkStub)
      .find((l) => l.text() === 'Ver todos los movimientos escaneados de 2025')!
    expect(enlace.props('to')).toEqual({
      path: '/reportes/inventario',
      query: { gestion: 2025, origen: 'historico' },
    })
    expect(w.text()).not.toContain('La gestión cambió sin consultar')
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
  it.each(['Auditor', 'Operador'])('muestra informe sin cierre editable para %s', async (rol) => {
    auth.rol = rol
    const w = montar()
    await flushPromises()
    expect(w.text()).toContain('sin porcentaje verificado')
    expect(w.text()).toContain('Saldo documental sin activar')
    expect(w.text()).not.toContain('Guardar cierre anual')
    w.unmount()
  })
  it('impide cerrar antes de terminar el año', async () => {
    permitido = false
    const w = montar()
    await flushPromises()
    expect(w.text()).toContain('todavía no terminó')
    expect(
      w
        .findAll('button')
        .find((b) => b.text() === 'Guardar cierre anual')!
        .attributes('disabled'),
    ).toBeDefined()
    w.unmount()
  })
  it('conserva solicitud y balance para un reintento tras perder conexión', async () => {
    const w = montar()
    await flushPromises()
    await w.get('.cierre-form input:not([type=checkbox])').setValue('ACTA-PRUEBA')
    await w.get('.cierre-form textarea').setValue('Balance revisado de la prueba')
    await w.get('.cierre-form input[type=checkbox]').setValue(true)
    post.mockRejectedValueOnce(new Error('sin internet'))
    await w.get('.cierre-form').trigger('submit')
    await flushPromises()
    const primero = post.mock.calls[0][1]
    post.mockResolvedValueOnce({ data: { gestion: 2026, version: 1 } })
    await w.get('.cierre-form').trigger('submit')
    await flushPromises()
    expect(post.mock.calls[1][1]).toEqual(primero)
    expect(primero.huella_esperada).toBe('a'.repeat(64))
    expect(w.text()).toContain('versión 1, guardado')
    w.unmount()
  })
})
