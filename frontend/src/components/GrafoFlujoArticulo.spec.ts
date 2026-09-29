import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import GrafoFlujoArticulo from './GrafoFlujoArticulo.vue'
import api from '@/services/api'

vi.mock('@/services/api', () => ({ default: { get: vi.fn() } }))
const obtener = vi.mocked(api.get)
const ciclo = {
  nodes: [{ name: 'Almacén Central' }, { name: 'Feria del Libro' }, { name: 'Ventas' }],
  links: [
    { source: 'Almacén Central', target: 'Feria del Libro', value: 120 },
    { source: 'Feria del Libro', target: 'Almacén Central', value: 30 },
    { source: 'Almacén Central', target: 'Ventas', value: 10 },
  ],
}
const instancias: ReturnType<typeof mount>[] = []
function montar() {
  const wrapper = mount(GrafoFlujoArticulo, { props: { articuloId: 63, nombre: 'AGUSTINA Y ELLOS' } })
  instancias.push(wrapper)
  return wrapper
}
beforeEach(() => vi.resetAllMocks())
afterEach(() => { instancias.splice(0).forEach(w => w.unmount()) })

describe('Flujo de artículos', () => {
  it('representa ida y vuelta sin perder cantidades y permite destacar un área', async () => {
    obtener.mockResolvedValue({ data: ciclo })
    const w = montar()
    await flushPromises()
    expect(w.findAll('svg > path')).toHaveLength(3)
    expect(w.findAll('.nodo')).toHaveLength(2)
    expect(w.findAll('tbody tr')).toHaveLength(2)
    expect(w.findAll('.metrica strong').map(n => n.text())).toEqual(['30', '130', '2'])
    await w.find('.nodo').trigger('click')
    expect(w.findAll('tbody tr')).toHaveLength(1)
    expect(w.find('tbody').text()).toContain('Feria del Libro')
    expect(w.find('tbody').text()).toContain('120')
    await w.find('.detalle-cabecera button').trigger('click')
    expect(w.findAll('tbody tr')).toHaveLength(2)
  })

  it('ignora una respuesta atrasada al cambiar de artículo y cancela al salir', async () => {
    let terminar: (value: { data: typeof ciclo }) => void = () => {}
    obtener.mockImplementationOnce(() => new Promise(resolve => { terminar = resolve }))
    obtener.mockResolvedValueOnce({ data: { nodes: [], links: [] } })
    const w = montar()
    const primera = obtener.mock.calls[0][1]?.signal as AbortSignal
    await w.setProps({ articuloId: 65, nombre: 'CAER EN EL CIELO' })
    await flushPromises()
    expect(primera.aborted).toBe(true)
    terminar({ data: ciclo })
    await flushPromises()
    expect(w.find('svg').exists()).toBe(false)
    expect(w.text()).toContain('todavía no tiene entradas')
    const ultima = obtener.mock.calls[1][1]?.signal as AbortSignal
    w.unmount()
    expect(ultima.aborted).toBe(true)
    instancias.pop()
  })

  it('muestra un error recuperable y permite volver a cargar', async () => {
    obtener.mockRejectedValueOnce(new Error('Servidor no disponible'))
    obtener.mockResolvedValueOnce({ data: ciclo })
    const w = montar()
    await flushPromises()
    expect(w.find('[role="alert"]').exists()).toBe(true)
    await w.find('[role="alert"] button').trigger('click')
    await flushPromises()
    expect(w.find('svg').exists()).toBe(true)
  })

  it('rechaza enlaces incompletos sin romper la vista', async () => {
    obtener.mockResolvedValue({ data: { ...ciclo, links: [{ source: 'Inexistente', target: 'Almacén Central', value: 2 }] } })
    const w = montar()
    await flushPromises()
    expect(w.find('[role="alert"]').exists()).toBe(true)
    expect(w.find('svg').exists()).toBe(false)
  })
})
