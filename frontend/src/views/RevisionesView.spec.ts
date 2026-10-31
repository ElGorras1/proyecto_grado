import { flushPromises, mount, RouterLinkStub } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import RevisionesView from './RevisionesView.vue'
const { get, post, auth } = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn(), auth: { rol: 'Administrador' } }))
vi.mock('@/services/api', () => ({ default: { get, post, defaults: { baseURL: 'http://localhost:8010/api/v1' } } }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }))
vi.mock('vue-router', () => ({ useRoute: () => ({ query: {} }) }))
const fila = { id: 1, tipo: 'HIL', origen: 'HIL', articulo_id: 7, articulo: 'Libro de prueba QA', codigo: 'QA', fecha: null, descripcion: 'Revisar fecha del papel', estado: 'Por categorizar', prioridad: 'MEDIA', score: null, destino: { path: '/kardex-digital', query: { articulo_id: 7, tab: 'hil' } } }
const bandeja = { total: 61, pagina: 1, limite: 30, conteos: { HIL: 60, MODELO: 1, OPERATIVO: 0 }, gestiones: [2025], filas: [fila, { ...fila, id: 2, tipo: 'SEGUIMIENTO', origen: 'MODELO', fecha: '2025-01-02', score: .7, destino: null }], alcance: 'Avisos para revisar; no son discrepancias confirmadas.' }
const detalle = { id: 2, articulo_id: 7, movimiento_id: 99, score: .7, umbral: .6, estado_revision: 'PENDIENTE', revision_numero: 0, datos_cambiaron: false, snapshot: { articulo: 'Libro de prueba QA', detalle: 'Fila conservada', fecha: '2025-01-02', ingresos: null, salidas: 2, ruta_imagen_respaldo: null }, contexto: { indicadores: ['Cantidad inusual'] }, revisiones: [] }
beforeEach(() => {
  auth.rol = 'Administrador'; get.mockReset(); post.mockReset()
  get.mockImplementation((url: string) => Promise.resolve({ data: url === '/automatizacion/estado' ? { configurada: true, habilitada: true } : url.includes('/seguimiento/') ? detalle : bandeja }))
})
function montar() { return mount(RevisionesView, { global: { stubs: { RouterLink: RouterLinkStub } } }) }
function diferida<T>() {
  let resolve!: (value: T) => void, reject!: (reason: unknown) => void
  const promise = new Promise<T>((res, rej) => { resolve = res; reject = rej })
  return { promise, resolve, reject }
}
describe('Revisiones cotidianas', () => {
  it.each([false, true])('ignora el resultado tardío de otra revisión (fallo: %s)', async falla => {
    const pendiente = diferida<{ data: typeof detalle }>()
    post.mockReturnValue(pendiente.promise)
    const original = get.getMockImplementation()!
    get.mockImplementation((url: string) => url.endsWith('/3')
      ? Promise.resolve({ data: { ...detalle, id: 3, movimiento_id: 100, snapshot: { ...detalle.snapshot, articulo: 'Otro artículo' } } })
      : url === '/revisiones/pendientes'
        ? Promise.resolve({ data: { ...bandeja, filas: [...bandeja.filas, { ...bandeja.filas[1], id: 3, articulo: 'Otro artículo' }] } })
        : original(url))
    const w = montar(); await flushPromises()
    await w.findAll('button').filter(b => b.text() === 'Abrir evidencia')[0].trigger('click'); await flushPromises()
    await w.get('.decision textarea').setValue('Cotejado con el documento original')
    await w.get('form.decision').trigger('submit')
    await w.findAll('button').filter(b => b.text() === 'Abrir evidencia')[1].trigger('click'); await flushPromises()
    if (falla) pendiente.reject({ response: { data: { detail: 'Conflicto del aviso anterior' } } })
    else pendiente.resolve({ data: { ...detalle, revision_numero: 1 } })
    await flushPromises()
    expect(w.get('.detalle h2').text()).toContain('Otro artículo · movimiento #100')
    expect(w.text()).not.toContain('Revisión registrada')
    expect(w.text()).not.toContain('Conflicto del aviso anterior')
    w.unmount()
  })
  it('no consulta de nuevo si se abandona la pantalla durante un guardado', async () => {
    const pendiente = diferida<{ data: typeof detalle }>(); post.mockReturnValue(pendiente.promise)
    const w = montar(); await flushPromises()
    await w.findAll('button').find(b => b.text() === 'Abrir evidencia')!.trigger('click'); await flushPromises()
    await w.get('.decision textarea').setValue('Cotejado con el documento original')
    await w.get('form.decision').trigger('submit')
    w.unmount(); const consultas = get.mock.calls.length
    pendiente.resolve({ data: { ...detalle, revision_numero: 1 } }); await flushPromises()
    expect(get.mock.calls).toHaveLength(consultas)
  })
  it('vuelve a la última página disponible cuando se resuelve el último aviso de otra página', async () => {
    const original = get.getMockImplementation()!
    get.mockImplementation((url: string, opciones?: { params: { pagina: number } }) => url === '/revisiones/pendientes'
      ? Promise.resolve({ data: { ...bandeja, total: 30, pagina: opciones!.params.pagina, filas: opciones!.params.pagina === 1 ? bandeja.filas : [] } })
      : original(url))
    const w = montar(); await flushPromises()
    // La lista puede reducirse mientras el usuario permanece en una página posterior.
    get.mockResolvedValueOnce({ data: { ...bandeja, total: 61 } })
    await w.findAll('button').find(b => b.text() === 'Actualizar pendientes')!.trigger('click'); await flushPromises()
    await w.findAll('button').find(b => b.text() === 'Siguiente')!.trigger('click'); await flushPromises()
    expect(get).toHaveBeenLastCalledWith('/revisiones/pendientes', expect.objectContaining({ params: expect.objectContaining({ pagina: 1 }) }))
    expect(w.text()).toContain('Página 1 de 1')
    w.unmount()
  })
  it('cierra la evidencia anterior al aplicar otro filtro', async () => {
    const w = montar(); await flushPromises()
    await w.findAll('button').find(b => b.text() === 'Abrir evidencia')!.trigger('click'); await flushPromises()
    expect(w.find('.detalle').exists()).toBe(true)
    await w.get('[aria-label="Artículo de la revisión"]').setValue('Otro libro')
    await w.get('form.filtros').trigger('submit'); await flushPromises()
    expect(w.find('.detalle').exists()).toBe(false)
    w.unmount()
  })
  it('reúne avisos con su origen y evidencia, sin solicitar entrenamientos', async () => {
    const w = montar(); await flushPromises()
    expect(w.text()).toContain('Revisión documental'); expect(w.text()).toContain('Análisis automático')
    expect(w.findComponent(RouterLinkStub).props('to')).toEqual(fila.destino)
    expect(get.mock.calls.some(c => String(c[0]).includes('entrenar'))).toBe(false)
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
  it('mantiene los filtros aplicados al paginar y aplica los cambios al confirmar', async () => {
    const w = montar(); await flushPromises()
    await w.get('[aria-label="Artículo de la revisión"]').setValue('Otro libro')
    await w.findAll('button').find(b => b.text() === 'Siguiente')!.trigger('click'); await flushPromises()
    expect(get).toHaveBeenLastCalledWith('/revisiones/pendientes', expect.objectContaining({ params: expect.objectContaining({ pagina: 2, articulo: undefined }) }))
    await w.get('form.filtros').trigger('submit'); await flushPromises()
    expect(get).toHaveBeenLastCalledWith('/revisiones/pendientes', expect.objectContaining({ params: expect.objectContaining({ pagina: 1, articulo: 'Otro libro' }) }))
    w.unmount()
  })
  it.each(['Administrador', 'Auditor'])('registra la revisión del seguimiento para %s conservando su versión', async rol => {
    auth.rol = rol; post.mockResolvedValue({ data: { ...detalle, revision_numero: 1 } })
    const w = montar(); await flushPromises()
    await w.findAll('button').find(b => b.text() === 'Abrir evidencia')!.trigger('click'); await flushPromises()
    await w.get('.decision textarea').setValue('Cotejado con el documento original')
    await w.get('form.decision').trigger('submit'); await flushPromises()
    expect(post).toHaveBeenCalledWith('/automatizacion/seguimiento/2/revision', expect.objectContaining({ revision_esperada: 0, motivo: 'Cotejado con el documento original' }))
    w.unmount()
  })
  it('permite al Operador consultar sin ofrecer una conclusión editable', async () => {
    auth.rol = 'Operador'
    const w = montar(); await flushPromises()
    await w.findAll('button').find(b => b.text() === 'Abrir evidencia')!.trigger('click'); await flushPromises()
    expect(w.find('form.decision').exists()).toBe(false)
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
})
