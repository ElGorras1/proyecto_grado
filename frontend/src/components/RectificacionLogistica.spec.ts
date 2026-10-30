import { mount, flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import RectificacionLogistica from './RectificacionLogistica.vue'
import type { FuenteLogistica } from '@/services/rectificacionLogistica'
const { post, auth } = vi.hoisted(() => ({ post: vi.fn(), auth: { rol: 'Administrador' } }))
vi.mock('@/services/api', () => ({ default: { post } }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }))
function fuente(clase: FuenteLogistica['clase'] = 'TRANSFERENCIA'): FuenteLogistica {
  return { clase, registro_id: 10, version: 'a'.repeat(64), datos: { cantidad: 2, encargado_id: 1,
    referencia_documento: 'ACTA-ORIGINAL', observaciones: '',
    ...(clase === 'TRANSFERENCIA' ? { area_origen_id: 1, area_destino_id: 2 } :
      clase === 'ENTREGA' ? { tipo: 'FERIA', area_origen_id: 1, receptor_nombre: 'Centro QA', receptor_tipo: 'INSTITUCION', ubicacion_externa: 'Puesto QA', ciudad: 'La Paz' } :
      { tipo: 'VENTA', area_destino_id: null, comprador: 'Comprador QA' }) } }
}
function montar(clase?: FuenteLogistica['clase']) {
  return mount(RectificacionLogistica, { props: { articuloId: 1, fuente: fuente(clase),
    areas: [{ id: 1, nombre: 'Galería' }, { id: 2, nombre: 'Depósito' }], encargados: [{ id: 1, nombre: 'Responsable' }] } })
}
beforeEach(() => { vi.clearAllMocks(); auth.rol = 'Administrador'; post.mockResolvedValue({ data: {} }) })
describe('Rectificación logística', () => {
  it.each(['TRANSFERENCIA', 'ENTREGA', 'EVENTO_CUSTODIA'] as const)('conserva fuente y exige cotejo para %s', async clase => {
    const w = montar(clase)
    expect(w.text()).toContain('El registro original se conserva')
    expect(w.get('button[type="submit"]').attributes('disabled')).toBeDefined()
    const inputs = w.findAll('input')
    await inputs[0].setValue(0)
    await w.get('input[type="checkbox"]').setValue(true)
    const referencia = w.findAll('input').find(i => i.element.parentElement?.textContent?.includes('Acta o documento'))!
    await referencia.setValue('ACTA-RECTIFICACION')
    const motivo = w.findAll('textarea').find(t => t.element.parentElement?.textContent?.includes('Motivo'))!
    await motivo.setValue('Cotejo del comprobante y corrección del registro.')
    await w.get('form').trigger('submit'); await flushPromises()
    expect(post).toHaveBeenCalledWith('/kardex/articulos/1/rectificaciones-logisticas', expect.objectContaining({
      registro_id: 10, version_esperada: 'a'.repeat(64), evidencia_revisada: true,
      cambios: expect.objectContaining({ clase, cantidad: 0 }),
    }))
    expect(w.emitted('guardado')).toHaveLength(1)
    w.unmount()
  })
  it('reutiliza la solicitud tras una respuesta incierta', async () => {
    post.mockRejectedValueOnce(new Error('conexión'))
    const w = montar()
    await w.get('input[type="checkbox"]').setValue(true)
    await w.get('form').trigger('submit'); await flushPromises()
    expect(w.get('[role="alert"]').text()).toContain('reintenta este mismo envío')
    await w.get('form').trigger('submit'); await flushPromises()
    expect(post.mock.calls[0][1].solicitud_id).toBe(post.mock.calls[1][1].solicitud_id)
    w.unmount()
  })
  it('conserva el formulario cuando la compensación es imposible y permite recargar', async () => {
    post.mockRejectedValue({ response: { data: { detail: 'La compensación no tiene unidades disponibles.' } } })
    const w = montar()
    await w.get('input[type="checkbox"]').setValue(true)
    await w.get('form').trigger('submit'); await flushPromises()
    expect(w.get('[role="alert"]').text()).toContain('no tiene unidades')
    await w.findAll('button').find(b => b.text() === 'Actualizar registros')!.trigger('click')
    expect(w.emitted('recargar')).toHaveLength(1)
    expect(w.find('form').exists()).toBe(true)
    w.unmount()
  })
  it.each(['Auditor', 'Operador'])('no permite mover stock a %s', rol => {
    auth.rol = rol
    const w = montar()
    expect(w.find('form').exists()).toBe(false)
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
})
