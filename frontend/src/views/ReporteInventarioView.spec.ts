import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import api from '@/services/api'
import ReporteInventarioView from './ReporteInventarioView.vue'

vi.mock('@/services/api', () => ({ default: { get: vi.fn() } }))
const obtener = vi.mocked(api.get)

const datos = {
  gestion: 2026,
  resumen: { movimientos: 2, articulos: 1, ingresos: 10, salidas: 2,
    pendientes_hil: 1, historicos: 1, modernos: 1 },
  mensual: Array.from({ length: 12 }, (_, i) => ({ mes: i + 1, movimientos: i === 0 ? 2 : 0,
    ingresos: i === 0 ? 10 : 0, salidas: i === 0 ? 2 : 0 })),
  pagina: 1,
  limite: 50,
  filas: [{ id: 1, fecha: '2026-01-02', articulo: 'Libro A', codigo: 'LIB-001',
    origen: 'Histórico', lote_id: 1, pagina: 1, orden_fila: 2, detalle: 'Salida',
    referencia: null, area_original: null, nodo: 'Área: Biblioteca', tipo_operacion: null,
    ingresos: 0, salidas: 2, pendiente_hil: true }],
}

beforeEach(() => {
  vi.resetAllMocks()
  obtener.mockImplementation(async url => {
    if (url === '/reportes/inventario/opciones') {
      return { data: { gestiones: [2026, 2025], nodos: ['Área: Biblioteca'] } } as never
    }
    return { data: datos } as never
  })
})

describe('Reportes por gestión', () => {
  it('muestra el resumen y envía filtros combinados al backend', async () => {
    const wrapper = mount(ReporteInventarioView, { global: { stubs: ['router-link'] } })
    await flushPromises()
    expect(wrapper.text()).toContain('Pendientes HIL')
    expect(wrapper.text()).toContain('Libro A')
    expect(wrapper.text()).toContain('no representa existencias al cierre de año')
    await wrapper.find('input[type="search"]').setValue('LIB-001')
    const selects = wrapper.findAll('.filtros select')
    await selects[1].setValue('2')
    await selects[2].setValue('historico')
    await selects[5].setValue('pendiente')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(obtener).toHaveBeenLastCalledWith('/reportes/inventario', {
      params: { gestion: 2026, mes: 2, articulo: 'LIB-001', origen: 'historico',
        direccion: 'todas', revision: 'pendiente', pagina: 1, limite: 50 },
    })
    wrapper.unmount()
  })
})
