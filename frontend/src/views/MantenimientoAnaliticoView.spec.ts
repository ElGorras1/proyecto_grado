import { mount, flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import MantenimientoAnaliticoView from './MantenimientoAnaliticoView.vue'
const { get, put, auth } = vi.hoisted(() => ({ get: vi.fn(), put: vi.fn(), auth: { rol: 'Administrador' } }))
vi.mock('@/services/api', () => ({ default: { get, put } }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }))
const estado = { configurada: true, habilitada: true, modelo_base_id: 'modelo-1', preparar_candidatos: true, gestion_hasta: 2025, intervalo_segundos: 300, revision_dias: 30, huella_politica: 'a'.repeat(64), ultimo_analisis: null, proxima_revision: null, ultimo_informe: { elegibles: 188, nuevos_resultados: 0, nuevos_avisos: 0, mantenimiento: { estado: 'SIN_CAMBIOS', mensaje: 'Sin cambios; se conserva el modelo.' } } }
beforeEach(() => { auth.rol = 'Administrador'; get.mockReset(); put.mockReset(); get.mockImplementation((url: string) => Promise.resolve({ data: url === '/automatizacion/estado' ? estado : { filas: [{ id: 'modelo-1', estado: 'COMPLETADO', creado_en: '2026-10-20T12:00:00Z' }] } })) })
describe('Mantenimiento ocasional', () => {
  it('explica la programación sin entrenar ni guardar cambios al abrir', async () => {
    const original = get.getMockImplementation()!
    get.mockImplementation((url: string) => url === '/automatizacion/estado' ? Promise.resolve({ data: { ...estado, ultimo_informe: { ...estado.ultimo_informe, mantenimiento: { estado: 'PROGRAMADO' } } } }) : original(url))
    const w = mount(MantenimientoAnaliticoView); await flushPromises()
    expect(w.text()).toContain('cada 5 minutos'); expect(w.text()).toContain('cada 30 días')
    expect(w.text()).toContain('La revisión se realizará en la fecha programada.')
    expect(put).not.toHaveBeenCalled(); expect(w.get('details').attributes('open')).toBeUndefined()
    w.unmount()
  })
  it('mantiene al Auditor en consulta y no carga el selector de versiones', async () => {
    auth.rol = 'Auditor'
    const w = mount(MantenimientoAnaliticoView); await flushPromises()
    expect(w.find('form').exists()).toBe(false); expect(get.mock.calls.map(c => c[0])).toEqual(['/automatizacion/estado'])
    w.unmount()
  })
  it('envía la versión de configuración para impedir sobrescribir otro cambio', async () => {
    put.mockRejectedValue({ response: { data: { detail: 'La configuración cambió; vuelve a cargarla.' } } })
    const w = mount(MantenimientoAnaliticoView); await flushPromises()
    await w.get('textarea').setValue('Revisar la frecuencia programada')
    await w.get('form').trigger('submit'); await flushPromises()
    expect(put).toHaveBeenCalledWith('/automatizacion/politica', expect.objectContaining({ intervalo_segundos: 300, revision_dias: 30, huella_esperada: 'a'.repeat(64) }))
    expect(w.get('[role="alert"]').text()).toContain('La configuración cambió')
    w.unmount()
  })
})
