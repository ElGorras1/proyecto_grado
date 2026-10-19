import { mount, flushPromises, RouterLinkStub } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import GestionInstitucionalView from './GestionInstitucionalView.vue'
const { get, post, auth } = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  auth: { rol: 'Administrador' },
}))
vi.mock('@/services/api', () => ({ default: { get, post } }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }))
let permitido = true
const informe = {
  gestion: new Date().getFullYear(),
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
  get.mockReset()
  post.mockReset()
  get.mockImplementation((url: string) =>
    Promise.resolve({
      data: url.endsWith('vista-previa')
        ? {
            snapshot: {
              gestion: new Date().getFullYear(),
              total: 100,
              articulos: [],
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
  it('mantiene el informe de la gestión consultada hasta confirmar otro año', async () => {
    const original = get.getMockImplementation()!
    get.mockImplementation((url: string, opciones: any) =>
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
