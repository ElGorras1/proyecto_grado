import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import TrazabilidadArticulo from './TrazabilidadArticulo.vue'
import api from '@/services/api'

vi.mock('@/services/api', () => ({ default: { get: vi.fn(), defaults: { baseURL: 'http://localhost:8000/api/v1' } } }))
const obtener = vi.mocked(api.get)
const historico = { clave: 'HISTORICO:7', id: 7, clase: 'HISTORICO', descripcion: 'Cierre escaneado',
  fecha: '2025-12-31', fecha_registro: null, cantidad: 10, ingreso: 10, salida: 0,
  documento: 'KARDEX-01', imagen_url: '/storage/kardex/hoja.png', estado_relacion: 'PENDIENTE',
  conexiones: [{ ubicacion: 'documental', direccion: 'REGISTRO', etiqueta: 'Saldo documental', certeza: 'PENDIENTE' }],
  vinculos: [], afecta_stock_actual: false, estado: 'ACTIVO', lote_id: 3, tanda: 2, pagina: 1, fila: 4 }
const base = { ...historico, clave: 'BASE:1', id: 1, clase: 'BASE', descripcion: 'Base operativa fijada',
  fecha: '2026-10-08T12:00:00Z', documento: 'ACTA-01', imagen_url: null, estado_relacion: 'CONFIRMADA',
  conexiones: [], vinculos: [{ destino: 'HISTORICO:7', tipo: 'BASE_HISTORICA' }] }
const resultado = { eventos: [base], contexto: [historico], total: 1, pendientes: 0,
  nodes: [], links: [], ubicaciones: [{ id: 'documental', label: 'Saldo documental' }], criterio: 'Fechas documentales', avisos: [], integridad_libro: true }
const instancias: ReturnType<typeof mount>[] = []
function montar() {
  const consulta = obtener.getMockImplementation()
  obtener.mockImplementation((...args) => args[0] === '/kardex/tandas'
    ? Promise.resolve({ data: { tandas: [1, 2, 3].map(id => ({ id })) } })
    : consulta!(...args))
  const w = mount(TrazabilidadArticulo, { props: { articuloId: 1 }, global: { stubs: { GrafoTrazabilidad: true } } })
  instancias.push(w); return w
}
beforeEach(() => vi.resetAllMocks())
afterEach(() => instancias.splice(0).forEach(w => w.unmount()))

describe('Consulta de trazabilidad', () => {
  it('muestra la asignación inferida junto a la lectura documental', async () => {
    obtener.mockResolvedValue({ data: { ...resultado, eventos: [{ ...historico, area_documental: 'CDP',
      asignacion_area: { area: 'Capacitación', motivo: 'Agrupación por parecido y frecuencia; identidad no confirmada.' } }] } })
    const w = montar(); await flushPromises()
    expect(w.get('.detalle').text()).toContain('Área inferida: Capacitación')
    expect(w.get('.detalle').text()).toContain('Lectura conservada: CDP')
  })
  it('abre el cierre fijado fuera del filtro, la foto y su fila sin presentar un archivo inexistente', async () => {
    obtener.mockResolvedValue({ data: resultado })
    const w = montar(); await flushPromises()
    expect(w.get('[aria-label="Detalle de trazabilidad"]').text()).toContain('ACTA-01')
    expect(w.find('img').exists()).toBe(false)
    const vinculo = w.get('.vinculo button')
    await vinculo.trigger('click')
    expect(w.get('[aria-label="Detalle de trazabilidad"]').text()).toContain('Tanda 2 · Lote #3 · Página 1 · Fila 4')
    await w.findAll('button').find(b => b.text() === 'Abrir foto del Kárdex')!.trigger('click')
    expect(w.get('img').attributes('src')).toBe('http://localhost:8000/storage/kardex/hoja.png')
    await w.get('[role="dialog"] button').trigger('click')
    expect(w.find('[role="dialog"]').exists()).toBe(false)
  })
  it('envía filtros, pagina sin repetir eventos y valida las fechas antes de consultar', async () => {
    obtener.mockResolvedValue({ data: { ...resultado, total: 45 } })
    const w = montar(); await flushPromises()
    await w.get('[aria-label="Ámbito de trazabilidad"]').setValue('HISTORICO')
    await w.get('[aria-label="Tanda de trazabilidad"]').setValue('2')
    await w.get('[aria-label="Fecha desde"]').setValue('2025-01-01')
    await w.get('[aria-label="Ubicación de trazabilidad"]').setValue('documental')
    await w.get('form').trigger('submit'); await flushPromises()
    expect(obtener).toHaveBeenLastCalledWith('/kardex/articulos/1/trazabilidad', expect.objectContaining({
      params: expect.objectContaining({ ambito: 'HISTORICO', tanda: '2', desde: '2025-01-01', ubicacion: 'documental', offset: 0 }) }))
    await w.findAll('.navegacion button')[1].trigger('click'); await flushPromises()
    expect(obtener).toHaveBeenLastCalledWith('/kardex/articulos/1/trazabilidad', expect.objectContaining({ params: expect.objectContaining({ offset: 30 }) }))
    await w.get('[aria-label="Fecha hasta"]').setValue('2024-12-31')
    const llamadas = obtener.mock.calls.length
    await w.get('form').trigger('submit'); await flushPromises()
    expect(obtener.mock.calls.length).toBe(llamadas)
    expect(w.text()).toContain('Revisa el intervalo de fechas')
  })
  it('descarta una respuesta del artículo anterior y cancela al salir', async () => {
    let terminar: (valor: unknown) => void = () => {}
    obtener.mockImplementationOnce(() => new Promise(resolve => { terminar = resolve }))
    obtener.mockResolvedValueOnce({ data: { tandas: [1, 2, 3].map(id => ({ id })) } })
    obtener.mockResolvedValueOnce({ data: { ...resultado, eventos: [], contexto: [], total: 0 } })
    const w = montar()
    const anterior = obtener.mock.calls[0][1]?.signal as AbortSignal
    await w.setProps({ articuloId: 2 }); await flushPromises()
    expect(anterior.aborted).toBe(true)
    terminar({ data: resultado }); await flushPromises()
    expect(w.text()).toContain('No hay eventos que coincidan')
    expect(w.find('.detalle').exists()).toBe(false)
    const actual = obtener.mock.calls.find(c => c[0] === '/kardex/articulos/2/trazabilidad')![1]?.signal as AbortSignal
    w.unmount(); instancias.pop()
    expect(actual.aborted).toBe(true)
  })
  it('muestra el error y recupera la consulta sin modificar registros', async () => {
    obtener.mockRejectedValueOnce(new Error('Sin conexión'))
    obtener.mockResolvedValueOnce({ data: { tandas: [1, 2, 3].map(id => ({ id })) } })
    obtener.mockResolvedValueOnce({ data: resultado })
    const w = montar(); await flushPromises()
    expect(w.find('[role="alert"]').exists()).toBe(true)
    await w.get('[role="alert"] button').trigger('click'); await flushPromises()
    expect(w.text()).toContain('Base operativa fijada')
  })
})
